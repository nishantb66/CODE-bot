"""
OSV.dev API Client

Queries the Open Source Vulnerabilities database for known
vulnerabilities in dependencies. Free, no API key required.
"""
import logging
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


@dataclass
class VulnerabilityInfo:
    """Represents a vulnerability from OSV.dev."""
    id: str
    summary: str
    details: str
    severity: str
    cvss_score: Optional[float]
    cwe_ids: List[str]
    references: List[str]
    affected_versions: List[str]
    fixed_version: Optional[str]
    published: Optional[str]
    modified: Optional[str]


class OSVClientError(Exception):
    """Custom exception for OSV client errors."""
    pass


class OSVClient:
    """
    Client for querying OSV.dev vulnerability database.
    
    OSV.dev is a free, open-source vulnerability database that aggregates
    data from multiple sources including:
    - GitHub Security Advisories
    - PyPI Advisory Database
    - npm Advisory Database
    - RustSec
    - Go Vulnerability Database
    - And many more
    
    No API key required!
    """
    
    BASE_URL = "https://api.osv.dev/v1"
    BATCH_SIZE = 100  # OSV supports batch queries
    
    # Ecosystem mapping for different package managers
    ECOSYSTEM_MAP = {
        # Python
        'requirements.txt': 'PyPI',
        'Pipfile': 'PyPI',
        'pyproject.toml': 'PyPI',
        'setup.py': 'PyPI',
        'poetry.lock': 'PyPI',
        
        # JavaScript/Node.js
        'package.json': 'npm',
        'package-lock.json': 'npm',
        'yarn.lock': 'npm',
        
        # Go
        'go.mod': 'Go',
        'go.sum': 'Go',
        
        # Rust
        'Cargo.toml': 'crates.io',
        'Cargo.lock': 'crates.io',
        
        # Ruby
        'Gemfile': 'RubyGems',
        'Gemfile.lock': 'RubyGems',
        
        # PHP
        'composer.json': 'Packagist',
        'composer.lock': 'Packagist',
        
        # Java/Maven
        'pom.xml': 'Maven',
        'build.gradle': 'Maven',
    }
    
    def __init__(self):
        """Initialize the OSV client."""
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'SecurityScanner/1.0'
        })
    
    def query_vulnerability(
        self, 
        package: str, 
        version: str, 
        ecosystem: str
    ) -> List[VulnerabilityInfo]:
        """
        Query OSV for vulnerabilities in a specific package version.
        
        Args:
            package: Package name
            version: Package version
            ecosystem: Package ecosystem (npm, PyPI, etc.)
            
        Returns:
            List of vulnerabilities found
        """
        try:
            response = self.session.post(
                f"{self.BASE_URL}/query",
                json={
                    "package": {
                        "name": package,
                        "ecosystem": ecosystem
                    },
                    "version": version
                },
                timeout=30
            )
            
            if response.status_code != 200:
                logger.warning(
                    f"OSV query failed for {package}@{version}: "
                    f"HTTP {response.status_code}"
                )
                return []
            
            data = response.json()
            return self._parse_vulnerabilities(data.get('vulns', []))
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"OSV query error for {package}: {str(e)}")
            return []
    
    def query_vulnerabilities_batch(
        self, 
        packages: List[Dict[str, str]]
    ) -> Dict[str, List[VulnerabilityInfo]]:
        """
        Query OSV for vulnerabilities in multiple packages at once.
        
        Args:
            packages: List of dicts with 'name', 'version', 'ecosystem' keys
            
        Returns:
            Dict mapping package identifiers to their vulnerabilities
        """
        results = {}
        
        # OSV supports batch queries
        queries = []
        package_map = {}
        
        for pkg in packages:
            name = pkg.get('name')
            version = pkg.get('version')
            ecosystem = pkg.get('ecosystem')
            
            if not all([name, version, ecosystem]):
                continue
            
            query = {
                "package": {
                    "name": name,
                    "ecosystem": ecosystem
                },
                "version": version
            }
            queries.append(query)
            package_map[f"{ecosystem}/{name}@{version}"] = pkg
        
        # Split into batches
        for i in range(0, len(queries), self.BATCH_SIZE):
            batch = queries[i:i + self.BATCH_SIZE]
            batch_results = self._query_batch(batch)
            
            for j, vulns in enumerate(batch_results):
                pkg = packages[i + j] if i + j < len(packages) else None
                if pkg:
                    key = f"{pkg.get('ecosystem')}/{pkg.get('name')}@{pkg.get('version')}"
                    results[key] = vulns
        
        return results
    
    def _query_batch(self, queries: List[Dict]) -> List[List[VulnerabilityInfo]]:
        """Execute a batch query to OSV."""
        try:
            response = self.session.post(
                f"{self.BASE_URL}/querybatch",
                json={"queries": queries},
                timeout=60
            )
            
            if response.status_code != 200:
                logger.warning(f"OSV batch query failed: HTTP {response.status_code}")
                return [[] for _ in queries]
            
            data = response.json()
            results = []
            
            for result in data.get('results', []):
                vulns = self._parse_vulnerabilities(result.get('vulns', []))
                results.append(vulns)
            
            # Pad with empty lists if needed
            while len(results) < len(queries):
                results.append([])
            
            return results
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"OSV batch query error: {str(e)}")
            return [[] for _ in queries]
    
    def _parse_vulnerabilities(
        self, 
        vulns: List[Dict[str, Any]]
    ) -> List[VulnerabilityInfo]:
        """Parse raw vulnerability data from OSV."""
        parsed = []
        
        for vuln in vulns:
            # Extract severity and CVSS score
            severity = "UNKNOWN"
            cvss_score = None
            
            for sev in vuln.get('severity', []):
                if sev.get('type') == 'CVSS_V3':
                    cvss_score = float(sev.get('score', 0))
                    if cvss_score >= 9.0:
                        severity = "CRITICAL"
                    elif cvss_score >= 7.0:
                        severity = "HIGH"
                    elif cvss_score >= 4.0:
                        severity = "MEDIUM"
                    else:
                        severity = "LOW"
                    break
            
            # If no CVSS, check database_specific severity
            if severity == "UNKNOWN":
                db_specific = vuln.get('database_specific', {})
                severity = db_specific.get('severity', 'UNKNOWN').upper()
            
            # Extract CWE IDs
            cwe_ids = []
            for alias in vuln.get('aliases', []):
                if alias.startswith('CWE-'):
                    cwe_ids.append(alias)
            
            # Extract references
            references = []
            for ref in vuln.get('references', []):
                if ref.get('url'):
                    references.append(ref['url'])
            
            # Extract fixed version
            fixed_version = None
            affected_versions = []
            for affected in vuln.get('affected', []):
                for range_info in affected.get('ranges', []):
                    for event in range_info.get('events', []):
                        if 'fixed' in event:
                            fixed_version = event['fixed']
                        if 'introduced' in event:
                            affected_versions.append(f">={event['introduced']}")
            
            parsed.append(VulnerabilityInfo(
                id=vuln.get('id', 'UNKNOWN'),
                summary=vuln.get('summary', 'No summary available'),
                details=vuln.get('details', ''),
                severity=severity,
                cvss_score=cvss_score,
                cwe_ids=cwe_ids,
                references=references[:5],  # Limit references
                affected_versions=affected_versions,
                fixed_version=fixed_version,
                published=vuln.get('published'),
                modified=vuln.get('modified')
            ))
        
        return parsed
    
    @classmethod
    def get_ecosystem_for_file(cls, filename: str) -> Optional[str]:
        """Get the ecosystem for a dependency file."""
        import os
        basename = os.path.basename(filename)
        return cls.ECOSYSTEM_MAP.get(basename)
