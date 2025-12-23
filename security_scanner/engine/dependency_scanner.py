"""
Dependency Scanner

Scans dependency files for known vulnerabilities using OSV.dev API.
"""
import logging
from typing import Dict, List, Optional
from security_scanner.engine.base_scanner import BaseScanner
from security_scanner.core.result import VulnerabilityResult
from security_scanner.core.severity import Severity, Confidence
from security_scanner.services.osv_client import OSVClient
from security_scanner.services.dependency_parser import DependencyParser, Dependency

logger = logging.getLogger(__name__)


class DependencyScanner(BaseScanner):
    """
    Scans dependency files for known vulnerabilities.
    
    Uses OSV.dev to check for CVEs and security advisories
    in project dependencies.
    """
    
    name = "dependency"
    description = "Scans dependencies for known vulnerabilities"
    
    # Files this scanner handles
    DEPENDENCY_FILES = {
        'requirements.txt',
        'Pipfile',
        'pyproject.toml',
        'package.json',
        'package-lock.json',
        'yarn.lock',
        'go.mod',
        'Cargo.toml',
        'Gemfile',
        'composer.json',
        'pom.xml',
        'build.gradle',
    }
    
    def __init__(self):
        """Initialize the dependency scanner."""
        super().__init__()
        self.osv_client = OSVClient()
        self.parser = DependencyParser()
    
    def is_applicable(self, file_path: str) -> bool:
        """Check if file is a dependency file."""
        import os
        filename = os.path.basename(file_path).lower()
        
        # Check exact matches
        if filename in {f.lower() for f in self.DEPENDENCY_FILES}:
            return True
        
        # Check for requirements*.txt pattern
        if 'requirements' in filename and filename.endswith('.txt'):
            return True
        
        return False
    
    def scan(
        self, 
        files: Dict[str, str],
        **kwargs
    ) -> List[VulnerabilityResult]:
        """
        Scan dependency files for known vulnerabilities.
        
        Args:
            files: Dictionary of file paths to contents
            
        Returns:
            List of vulnerability results
        """
        results = []
        all_dependencies = []
        
        # Parse all dependency files
        for file_path, content in files.items():
            if self.is_applicable(file_path):
                try:
                    deps = self.parser.parse_file(file_path, content)
                    all_dependencies.extend(deps)
                    logger.info(f"Parsed {len(deps)} dependencies from {file_path}")
                except Exception as e:
                    logger.warning(f"Error parsing {file_path}: {str(e)}")
        
        if not all_dependencies:
            logger.info("No dependencies found to scan")
            return results
        
        logger.info(f"Scanning {len(all_dependencies)} total dependencies")
        
        # Prepare batch query
        packages = []
        for dep in all_dependencies:
            packages.append({
                'name': dep.name,
                'version': dep.version,
                'ecosystem': dep.ecosystem
            })
        
        # Query OSV.dev
        try:
            vuln_results = self.osv_client.query_vulnerabilities_batch(packages)
        except Exception as e:
            logger.error(f"OSV query failed: {str(e)}")
            return results
        
        # Create dependency lookup for quick access
        dep_lookup = {
            f"{d.ecosystem}/{d.name}@{d.version}": d 
            for d in all_dependencies
        }
        
        # Process vulnerability results
        for pkg_key, vulns in vuln_results.items():
            if not vulns:
                continue
            
            dep = dep_lookup.get(pkg_key)
            if not dep:
                continue
            
            for vuln in vulns:
                # Determine severity
                if vuln.cvss_score:
                    severity = Severity.from_cvss(vuln.cvss_score)
                else:
                    severity = Severity.from_string(vuln.severity)
                
                # Create vulnerability result
                result = VulnerabilityResult(
                    title=f"Vulnerable Dependency: {dep.name}@{dep.version}",
                    description=vuln.summary or f"Known vulnerability in {dep.name}",
                    file_path=dep.file_path,
                    line=dep.line_number,
                    severity=severity,
                    confidence=Confidence.HIGH,  # OSV data is reliable
                    vulnerability_type="outdated_dependency",
                    impact=self._get_impact_description(severity, dep.name),
                    root_cause=f"The package {dep.name} version {dep.version} contains a known security vulnerability.",
                    suggested_fix=self._get_fix_suggestion(dep, vuln),
                    suggested_version=vuln.fixed_version,
                    cve_id=vuln.id if vuln.id.startswith('CVE') else None,
                    cwe_id=vuln.cwe_ids[0] if vuln.cwe_ids else None,
                    cvss_score=vuln.cvss_score,
                    references=vuln.references,
                    scanner=self.name,
                    package_name=dep.name,
                    current_version=dep.version
                )
                results.append(result)
        
        # Filter and deduplicate
        results = self._deduplicate_results(results)
        
        logger.info(f"Found {len(results)} dependency vulnerabilities")
        return results
    
    def _get_impact_description(self, severity: Severity, package_name: str) -> str:
        """Generate impact description based on severity."""
        impacts = {
            Severity.CRITICAL: (
                f"Critical vulnerability in {package_name} could allow remote code execution, "
                "data breach, or complete system compromise. Immediate patching required."
            ),
            Severity.HIGH: (
                f"High severity vulnerability in {package_name} may allow significant security "
                "breaches including unauthorized access or data exposure."
            ),
            Severity.MEDIUM: (
                f"Medium severity issue in {package_name} could lead to security weaknesses "
                "that might be exploited under certain conditions."
            ),
            Severity.LOW: (
                f"Low severity issue in {package_name} represents a minor security concern "
                "with limited exploitability."
            ),
        }
        return impacts.get(severity, f"Security vulnerability found in {package_name}")
    
    def _get_fix_suggestion(self, dep: Dependency, vuln) -> str:
        """Generate fix suggestion."""
        if vuln.fixed_version:
            return (
                f"Upgrade {dep.name} from version {dep.version} to {vuln.fixed_version} or later. "
                f"Run: "
            ) + self._get_upgrade_command(dep, vuln.fixed_version)
        return (
            f"Check for available updates to {dep.name} and upgrade to the latest secure version. "
            f"Review the vulnerability details and assess if a workaround is available."
        )
    
    def _get_upgrade_command(self, dep: Dependency, fixed_version: str) -> str:
        """Generate upgrade command based on ecosystem."""
        commands = {
            'PyPI': f"`pip install {dep.name}>={fixed_version}`",
            'npm': f"`npm install {dep.name}@{fixed_version}`",
            'Go': f"`go get {dep.name}@{fixed_version}`",
            'crates.io': f"Update Cargo.toml: `{dep.name} = \"{fixed_version}\"`",
            'RubyGems': f"`gem update {dep.name}`",
            'Packagist': f"`composer require {dep.name}:{fixed_version}`",
            'Maven': f"Update pom.xml version to {fixed_version}",
        }
        return commands.get(dep.ecosystem, f"Update to version {fixed_version}")
    
    def _deduplicate_results(
        self, 
        results: List[VulnerabilityResult]
    ) -> List[VulnerabilityResult]:
        """Remove duplicate vulnerability findings."""
        seen = set()
        unique = []
        
        for result in results:
            # Create a unique key based on package, version, and CVE
            key = (
                result.package_name,
                result.current_version,
                result.cve_id or result.title
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(result)
        
        return unique
