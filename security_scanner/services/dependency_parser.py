"""
Dependency Parser Service

Parses various dependency file formats to extract package names and versions.
Supports multiple languages and package managers.
"""
import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Dependency:
    """Represents a parsed dependency."""
    name: str
    version: str
    ecosystem: str
    file_path: str
    line_number: Optional[int] = None
    is_dev_dependency: bool = False
    raw_specifier: str = ""
    
    @property
    def identifier(self) -> str:
        """Unique identifier for this dependency."""
        return f"{self.ecosystem}/{self.name}@{self.version}"


class DependencyParser:
    """
    Parses dependency files from various package managers.
    
    Supported formats:
    - Python: requirements.txt, Pipfile, pyproject.toml, setup.py
    - JavaScript: package.json, package-lock.json
    - Go: go.mod
    - Rust: Cargo.toml
    - Ruby: Gemfile
    - PHP: composer.json
    - Java: pom.xml (basic support)
    """
    
    ECOSYSTEM_MAP = {
        'requirements.txt': 'PyPI',
        'Pipfile': 'PyPI',
        'Pipfile.lock': 'PyPI',
        'pyproject.toml': 'PyPI',
        'setup.py': 'PyPI',
        'setup.cfg': 'PyPI',
        'poetry.lock': 'PyPI',
        'package.json': 'npm',
        'package-lock.json': 'npm',
        'yarn.lock': 'npm',
        'go.mod': 'Go',
        'go.sum': 'Go',
        'Cargo.toml': 'crates.io',
        'Cargo.lock': 'crates.io',
        'Gemfile': 'RubyGems',
        'Gemfile.lock': 'RubyGems',
        'composer.json': 'Packagist',
        'composer.lock': 'Packagist',
        'pom.xml': 'Maven',
        'build.gradle': 'Maven',
    }
    
    def __init__(self):
        """Initialize the parser."""
        pass
    
    def parse_file(
        self, 
        file_path: str, 
        content: str
    ) -> List[Dependency]:
        """
        Parse a dependency file and extract dependencies.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            List of parsed dependencies
        """
        import os
        filename = os.path.basename(file_path)
        
        # Determine parser based on filename
        if 'requirements' in filename.lower() and filename.endswith('.txt'):
            return self._parse_requirements_txt(file_path, content)
        elif filename == 'Pipfile':
            return self._parse_pipfile(file_path, content)
        elif filename == 'pyproject.toml':
            return self._parse_pyproject_toml(file_path, content)
        elif filename == 'package.json':
            return self._parse_package_json(file_path, content)
        elif filename == 'package-lock.json':
            return self._parse_package_lock_json(file_path, content)
        elif filename == 'go.mod':
            return self._parse_go_mod(file_path, content)
        elif filename == 'Cargo.toml':
            return self._parse_cargo_toml(file_path, content)
        elif filename == 'Gemfile':
            return self._parse_gemfile(file_path, content)
        elif filename == 'composer.json':
            return self._parse_composer_json(file_path, content)
        elif filename == 'pom.xml':
            return self._parse_pom_xml(file_path, content)
        
        return []
    
    def _parse_requirements_txt(
        self, 
        file_path: str, 
        content: str
    ) -> List[Dependency]:
        """Parse Python requirements.txt format."""
        dependencies = []
        
        # Pattern for requirements.txt
        # Matches: package==version, package>=version, package~=version, etc.
        pattern = re.compile(
            r'^([a-zA-Z0-9_\-\.]+)\s*(?:[=<>~!]+)\s*([0-9][0-9a-zA-Z\.\-\*]*)',
            re.MULTILINE
        )
        
        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#') or line.startswith('-'):
                continue
            
            # Remove inline comments
            if '#' in line:
                line = line.split('#')[0].strip()
            
            match = pattern.match(line)
            if match:
                name = match.group(1).lower()
                version = match.group(2)
                
                # Clean version string
                version = self._normalize_version(version)
                
                if version:
                    dependencies.append(Dependency(
                        name=name,
                        version=version,
                        ecosystem='PyPI',
                        file_path=file_path,
                        line_number=line_num,
                        raw_specifier=line
                    ))
        
        return dependencies
    
    def _parse_pipfile(
        self, 
        file_path: str, 
        content: str
    ) -> List[Dependency]:
        """Parse Pipfile format."""
        dependencies = []
        
        try:
            # Simple TOML-like parsing for Pipfile
            in_packages = False
            in_dev_packages = False
            
            for line_num, line in enumerate(content.split('\n'), 1):
                line = line.strip()
                
                if line == '[packages]':
                    in_packages = True
                    in_dev_packages = False
                    continue
                elif line == '[dev-packages]':
                    in_packages = False
                    in_dev_packages = True
                    continue
                elif line.startswith('['):
                    in_packages = False
                    in_dev_packages = False
                    continue
                
                if (in_packages or in_dev_packages) and '=' in line:
                    # Parse package = "version" or package = {version = "..."}
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        name = parts[0].strip().strip('"').strip("'").lower()
                        version_part = parts[1].strip()
                        
                        # Extract version from various formats
                        version = self._extract_pipfile_version(version_part)
                        
                        if name and version:
                            dependencies.append(Dependency(
                                name=name,
                                version=version,
                                ecosystem='PyPI',
                                file_path=file_path,
                                line_number=line_num,
                                is_dev_dependency=in_dev_packages,
                                raw_specifier=line
                            ))
        except Exception as e:
            logger.warning(f"Error parsing Pipfile: {str(e)}")
        
        return dependencies
    
    def _extract_pipfile_version(self, version_part: str) -> Optional[str]:
        """Extract version from Pipfile version specification."""
        version_part = version_part.strip()
        
        # Simple string version
        if version_part.startswith('"') or version_part.startswith("'"):
            version = version_part.strip('"').strip("'")
            if version == '*':
                return None
            # Remove operators
            version = re.sub(r'^[=<>~!]+', '', version)
            return self._normalize_version(version) if version else None
        
        # Table format {version = "..."}
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', version_part)
        if match:
            version = match.group(1)
            version = re.sub(r'^[=<>~!]+', '', version)
            return self._normalize_version(version) if version else None
        
        return None
    
    def _parse_pyproject_toml(
        self, 
        file_path: str, 
        content: str
    ) -> List[Dependency]:
        """Parse pyproject.toml format."""
        dependencies = []
        
        try:
            # Find dependencies section
            deps_pattern = re.compile(
                r'dependencies\s*=\s*\[(.*?)\]',
                re.DOTALL
            )
            
            match = deps_pattern.search(content)
            if match:
                deps_content = match.group(1)
                
                # Parse each dependency line
                dep_pattern = re.compile(
                    r'["\']([a-zA-Z0-9_\-\.]+)(?:[=<>~!]+)([0-9][^"\']*)["\']'
                )
                
                for dep_match in dep_pattern.finditer(deps_content):
                    name = dep_match.group(1).lower()
                    version = self._normalize_version(dep_match.group(2))
                    
                    if version:
                        dependencies.append(Dependency(
                            name=name,
                            version=version,
                            ecosystem='PyPI',
                            file_path=file_path,
                            raw_specifier=dep_match.group(0)
                        ))
        except Exception as e:
            logger.warning(f"Error parsing pyproject.toml: {str(e)}")
        
        return dependencies
    
    def _parse_package_json(
        self, 
        file_path: str, 
        content: str
    ) -> List[Dependency]:
        """Parse package.json format."""
        dependencies = []
        
        try:
            data = json.loads(content)
            
            # Parse regular dependencies
            for name, version in data.get('dependencies', {}).items():
                clean_version = self._normalize_npm_version(version)
                if clean_version:
                    dependencies.append(Dependency(
                        name=name,
                        version=clean_version,
                        ecosystem='npm',
                        file_path=file_path,
                        is_dev_dependency=False,
                        raw_specifier=f"{name}: {version}"
                    ))
            
            # Parse dev dependencies
            for name, version in data.get('devDependencies', {}).items():
                clean_version = self._normalize_npm_version(version)
                if clean_version:
                    dependencies.append(Dependency(
                        name=name,
                        version=clean_version,
                        ecosystem='npm',
                        file_path=file_path,
                        is_dev_dependency=True,
                        raw_specifier=f"{name}: {version}"
                    ))
                    
        except json.JSONDecodeError as e:
            logger.warning(f"Error parsing package.json: {str(e)}")
        
        return dependencies
    
    def _parse_package_lock_json(
        self, 
        file_path: str, 
        content: str
    ) -> List[Dependency]:
        """Parse package-lock.json for exact versions."""
        dependencies = []
        
        try:
            data = json.loads(content)
            
            # Handle both v1/v2 and v3 package-lock formats
            packages = data.get('packages', {})
            if packages:
                # v3 format
                for path, info in packages.items():
                    if path and not path.startswith('node_modules/'):
                        continue
                    if not path:  # Root package
                        continue
                    
                    name = path.replace('node_modules/', '').split('node_modules/')[-1]
                    version = info.get('version')
                    
                    if name and version:
                        dependencies.append(Dependency(
                            name=name,
                            version=version,
                            ecosystem='npm',
                            file_path=file_path,
                            raw_specifier=f"{name}@{version}"
                        ))
            else:
                # v1/v2 format
                for name, info in data.get('dependencies', {}).items():
                    version = info.get('version')
                    if version:
                        dependencies.append(Dependency(
                            name=name,
                            version=version,
                            ecosystem='npm',
                            file_path=file_path,
                            raw_specifier=f"{name}@{version}"
                        ))
                        
        except json.JSONDecodeError as e:
            logger.warning(f"Error parsing package-lock.json: {str(e)}")
        
        return dependencies
    
    def _parse_go_mod(
        self, 
        file_path: str, 
        content: str
    ) -> List[Dependency]:
        """Parse go.mod format."""
        dependencies = []
        
        # Match require blocks and single requires
        require_pattern = re.compile(
            r'require\s+(?:\(([^)]+)\)|([^\s]+)\s+([^\s]+))',
            re.MULTILINE
        )
        
        # Pattern for individual dependencies
        dep_pattern = re.compile(
            r'^\s*([^\s]+)\s+(v[0-9][^\s]*)',
            re.MULTILINE
        )
        
        for match in require_pattern.finditer(content):
            if match.group(1):
                # Block format
                block_content = match.group(1)
                for dep_match in dep_pattern.finditer(block_content):
                    name = dep_match.group(1)
                    version = dep_match.group(2)
                    
                    dependencies.append(Dependency(
                        name=name,
                        version=version,
                        ecosystem='Go',
                        file_path=file_path,
                        raw_specifier=f"{name} {version}"
                    ))
            else:
                # Single line format
                name = match.group(2)
                version = match.group(3)
                
                if name and version:
                    dependencies.append(Dependency(
                        name=name,
                        version=version,
                        ecosystem='Go',
                        file_path=file_path,
                        raw_specifier=f"{name} {version}"
                    ))
        
        return dependencies
    
    def _parse_cargo_toml(
        self, 
        file_path: str, 
        content: str
    ) -> List[Dependency]:
        """Parse Cargo.toml format."""
        dependencies = []
        
        # Find [dependencies] section
        in_dependencies = False
        
        for line_num, line in enumerate(content.split('\n'), 1):
            stripped = line.strip()
            
            if stripped == '[dependencies]':
                in_dependencies = True
                continue
            elif stripped.startswith('[') and stripped != '[dependencies]':
                in_dependencies = False
                continue
            
            if in_dependencies and '=' in stripped and not stripped.startswith('#'):
                # Parse dependency = "version" or dependency = { version = "..." }
                parts = stripped.split('=', 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    version_part = parts[1].strip()
                    
                    # Extract version
                    if version_part.startswith('"'):
                        version = version_part.strip('"')
                    else:
                        match = re.search(r'version\s*=\s*"([^"]+)"', version_part)
                        version = match.group(1) if match else None
                    
                    if name and version:
                        dependencies.append(Dependency(
                            name=name,
                            version=self._normalize_version(version),
                            ecosystem='crates.io',
                            file_path=file_path,
                            line_number=line_num,
                            raw_specifier=stripped
                        ))
        
        return dependencies
    
    def _parse_gemfile(
        self, 
        file_path: str, 
        content: str
    ) -> List[Dependency]:
        """Parse Ruby Gemfile format."""
        dependencies = []
        
        # Match gem 'name', 'version' patterns
        pattern = re.compile(
            r"gem\s+['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]",
            re.MULTILINE
        )
        
        for match in pattern.finditer(content):
            name = match.group(1)
            version = self._normalize_version(match.group(2))
            
            if version:
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    ecosystem='RubyGems',
                    file_path=file_path,
                    raw_specifier=match.group(0)
                ))
        
        return dependencies
    
    def _parse_composer_json(
        self, 
        file_path: str, 
        content: str
    ) -> List[Dependency]:
        """Parse PHP composer.json format."""
        dependencies = []
        
        try:
            data = json.loads(content)
            
            for name, version in data.get('require', {}).items():
                if name == 'php':
                    continue
                clean_version = self._normalize_version(version)
                if clean_version:
                    dependencies.append(Dependency(
                        name=name,
                        version=clean_version,
                        ecosystem='Packagist',
                        file_path=file_path,
                        raw_specifier=f"{name}: {version}"
                    ))
                    
        except json.JSONDecodeError as e:
            logger.warning(f"Error parsing composer.json: {str(e)}")
        
        return dependencies
    
    def _parse_pom_xml(
        self, 
        file_path: str, 
        content: str
    ) -> List[Dependency]:
        """Parse Maven pom.xml format (basic support)."""
        dependencies = []
        
        # Basic regex pattern for dependencies
        pattern = re.compile(
            r'<dependency>\s*'
            r'<groupId>([^<]+)</groupId>\s*'
            r'<artifactId>([^<]+)</artifactId>\s*'
            r'(?:<version>([^<]+)</version>)?',
            re.MULTILINE | re.DOTALL
        )
        
        for match in pattern.finditer(content):
            group_id = match.group(1)
            artifact_id = match.group(2)
            version = match.group(3)
            
            if version and not version.startswith('$'):
                name = f"{group_id}:{artifact_id}"
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    ecosystem='Maven',
                    file_path=file_path,
                    raw_specifier=f"{name}:{version}"
                ))
        
        return dependencies
    
    def _normalize_version(self, version: str) -> Optional[str]:
        """Normalize version string."""
        if not version:
            return None
        
        # Remove common prefixes and operators
        version = re.sub(r'^[=<>~^!]+', '', version.strip())
        
        # Remove wildcards
        version = version.replace('*', '').rstrip('.')
        
        # Check if we have a valid version
        if not version or version in ['*', 'latest', 'x']:
            return None
        
        return version
    
    def _normalize_npm_version(self, version: str) -> Optional[str]:
        """Normalize npm version string."""
        if not version:
            return None
        
        version = version.strip()
        
        # Remove common npm prefixes
        version = re.sub(r'^[\^~>=<]+', '', version)
        
        # Handle ranges - take the first version
        if ' ' in version:
            version = version.split()[0]
        
        # Remove x and * wildcards
        version = re.sub(r'\.[xX*]', '', version)
        
        # Skip git/url dependencies
        if any(x in version for x in ['git', 'http', 'file:', '/']):
            return None
        
        return version if version else None
