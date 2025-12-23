"""
Configuration Scanner

Detects security misconfigurations in configuration files.
Covers Django, Node.js, Docker, Kubernetes, and other common frameworks.
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from security_scanner.engine.base_scanner import BaseScanner
from security_scanner.core.result import VulnerabilityResult
from security_scanner.core.severity import Severity, Confidence

logger = logging.getLogger(__name__)


@dataclass
class ConfigPattern:
    """Configuration vulnerability pattern."""
    id: str
    title: str
    description: str
    pattern: re.Pattern
    severity: Severity
    confidence: Confidence
    impact: str
    root_cause: str
    suggested_fix: str
    file_patterns: List[str]  # File name patterns this applies to
    cwe_id: Optional[str] = None


class ConfigScanner(BaseScanner):
    """
    Scans configuration files for security misconfigurations.
    
    Covers:
    - Django settings (DEBUG, SECRET_KEY, ALLOWED_HOSTS)
    - Node.js/Express configurations
    - Docker configurations
    - Kubernetes manifests
    - Nginx/Apache configs
    - Environment configurations
    """
    
    name = "config"
    description = "Detects security misconfigurations"
    
    # Configuration patterns
    CONFIG_PATTERNS: List[ConfigPattern] = [
        # Django misconfigurations
        ConfigPattern(
            id="DJANGO001",
            title="Django DEBUG Mode Enabled in Production",
            description="DEBUG = True found in Django settings. Debug mode should never be enabled in production.",
            pattern=re.compile(r'^\s*DEBUG\s*=\s*True', re.MULTILINE | re.IGNORECASE),
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            impact="Detailed error pages expose sensitive information, source code, and configuration to attackers.",
            root_cause="DEBUG mode left enabled, likely copied from development configuration.",
            suggested_fix="Set DEBUG = False in production settings. Use environment variable: DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'",
            file_patterns=['settings.py', 'settings/*.py', 'config.py'],
            cwe_id="CWE-489"
        ),
        ConfigPattern(
            id="DJANGO002",
            title="Django Weak SECRET_KEY",
            description="Django SECRET_KEY appears to be weak or hardcoded.",
            pattern=re.compile(
                r'SECRET_KEY\s*=\s*["\'](?:django-insecure-|secret|changeme|yoursecretkey)[^"\']*["\']',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            impact="Weak SECRET_KEY compromises session security, CSRF protection, and cryptographic signing.",
            root_cause="Default or placeholder SECRET_KEY not replaced with a secure random value.",
            suggested_fix="Generate a new secret key: `python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\"` and store in environment variable.",
            file_patterns=['settings.py', 'settings/*.py'],
            cwe_id="CWE-798"
        ),
        ConfigPattern(
            id="DJANGO003",
            title="Django ALLOWED_HOSTS Wildcard",
            description="ALLOWED_HOSTS set to allow all hosts ('*').",
            pattern=re.compile(r"ALLOWED_HOSTS\s*=\s*\[\s*['\"]?\*['\"]?\s*\]", re.IGNORECASE),
            severity=Severity.MEDIUM,
            confidence=Confidence.HIGH,
            impact="Host header injection attacks, cache poisoning, password reset poisoning.",
            root_cause="Wildcard ALLOWED_HOSTS used for convenience instead of explicit domain list.",
            suggested_fix="Specify exact domains: ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']",
            file_patterns=['settings.py', 'settings/*.py'],
            cwe_id="CWE-644"
        ),
        ConfigPattern(
            id="DJANGO004",
            title="Django Insecure Cookie Settings",
            description="Session or CSRF cookies not configured for security.",
            pattern=re.compile(
                r'(?:SESSION_COOKIE_SECURE|CSRF_COOKIE_SECURE)\s*=\s*False',
                re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.HIGH,
            impact="Cookies can be intercepted over HTTP connections, enabling session hijacking.",
            root_cause="Secure cookie flags disabled, cookies transmitted over insecure connections.",
            suggested_fix="Set SESSION_COOKIE_SECURE = True and CSRF_COOKIE_SECURE = True for HTTPS sites.",
            file_patterns=['settings.py', 'settings/*.py'],
            cwe_id="CWE-614"
        ),

        # Node.js/Express misconfigurations
        ConfigPattern(
            id="NODE001",
            title="Express Trust Proxy Misconfiguration",
            description="Express trust proxy enabled unsafely.",
            pattern=re.compile(r"trust\s*proxy['\"]?\s*[,:]\s*true", re.IGNORECASE),
            severity=Severity.MEDIUM,
            confidence=Confidence.MEDIUM,
            impact="IP spoofing attacks possible through X-Forwarded-For header manipulation.",
            root_cause="Trust proxy set to true without proper proxy configuration.",
            suggested_fix="Use specific proxy count or IP addresses: app.set('trust proxy', 1) or app.set('trust proxy', 'loopback')",
            file_patterns=['*.js', '*.ts', 'app.js', 'server.js', 'index.js'],
            cwe_id="CWE-290"
        ),
        ConfigPattern(
            id="NODE002",
            title="Node.js TLS Certificate Validation Disabled",
            description="TLS/SSL certificate validation disabled.",
            pattern=re.compile(
                r'(?:rejectUnauthorized|NODE_TLS_REJECT_UNAUTHORIZED)\s*[=:]\s*(?:false|0|["\']0["\'])',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            impact="Man-in-the-middle attacks possible due to disabled certificate verification.",
            root_cause="SSL verification disabled, often to work around certificate issues.",
            suggested_fix="Enable certificate validation. Fix certificate issues instead of disabling validation.",
            file_patterns=['*.js', '*.ts', '.env*'],
            cwe_id="CWE-295"
        ),

        # Docker misconfigurations
        ConfigPattern(
            id="DOCKER001",
            title="Docker Container Running as Root",
            description="Dockerfile does not specify a non-root user.",
            pattern=re.compile(r'^(?!.*USER\s+(?!root)).*$(?=.*(?:FROM|CMD|ENTRYPOINT))', re.MULTILINE | re.DOTALL),
            severity=Severity.MEDIUM,
            confidence=Confidence.LOW,
            impact="Container breakout attacks more dangerous when running as root.",
            root_cause="No USER instruction in Dockerfile, defaulting to root.",
            suggested_fix="Add USER instruction: RUN adduser -D appuser && USER appuser",
            file_patterns=['Dockerfile', 'Dockerfile.*'],
            cwe_id="CWE-250"
        ),
        ConfigPattern(
            id="DOCKER002",
            title="Docker Privileged Mode",
            description="Container configured to run in privileged mode.",
            pattern=re.compile(r'privileged\s*:\s*true', re.IGNORECASE),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            impact="Privileged containers can escape containment and access host system.",
            root_cause="Privileged flag enabled, giving container full host access.",
            suggested_fix="Remove privileged: true. Use specific capabilities with cap_add instead.",
            file_patterns=['docker-compose.yml', 'docker-compose.yaml', '*.yaml', '*.yml'],
            cwe_id="CWE-250"
        ),
        ConfigPattern(
            id="DOCKER003",
            title="Docker Exposed Host Network",
            description="Container using host network mode.",
            pattern=re.compile(r'network_mode\s*:\s*["\']?host["\']?', re.IGNORECASE),
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            impact="Container can access all host network interfaces, reducing isolation.",
            root_cause="Host network mode used, bypassing Docker network isolation.",
            suggested_fix="Use bridge networking with explicit port mapping instead of host network.",
            file_patterns=['docker-compose.yml', 'docker-compose.yaml'],
            cwe_id="CWE-668"
        ),

        # Kubernetes misconfigurations
        ConfigPattern(
            id="K8S001",
            title="Kubernetes Pod Running as Root",
            description="Pod security context allows running as root.",
            pattern=re.compile(r'runAsNonRoot\s*:\s*false', re.IGNORECASE),
            severity=Severity.MEDIUM,
            confidence=Confidence.HIGH,
            impact="Container processes running as root increase blast radius of compromises.",
            root_cause="runAsNonRoot not enforced in security context.",
            suggested_fix="Set runAsNonRoot: true and runAsUser to a non-zero UID.",
            file_patterns=['*.yaml', '*.yml'],
            cwe_id="CWE-250"
        ),
        ConfigPattern(
            id="K8S002",
            title="Kubernetes Privileged Container",
            description="Container configured with privileged security context.",
            pattern=re.compile(r'privileged\s*:\s*true', re.IGNORECASE),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            impact="Privileged containers can access host resources and escape isolation.",
            root_cause="Privileged flag enabled in security context.",
            suggested_fix="Remove privileged: true. Use specific capabilities if needed.",
            file_patterns=['*.yaml', '*.yml'],
            cwe_id="CWE-250"
        ),
        ConfigPattern(
            id="K8S003",
            title="Kubernetes Allow Privilege Escalation",
            description="Container allows privilege escalation.",
            pattern=re.compile(r'allowPrivilegeEscalation\s*:\s*true', re.IGNORECASE),
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            impact="Processes can gain more privileges than parent process.",
            root_cause="allowPrivilegeEscalation not explicitly set to false.",
            suggested_fix="Set allowPrivilegeEscalation: false in security context.",
            file_patterns=['*.yaml', '*.yml'],
            cwe_id="CWE-250"
        ),
        ConfigPattern(
            id="K8S004",
            title="Kubernetes Secrets in Environment Variables",
            description="Kubernetes secrets exposed as environment variables.",
            pattern=re.compile(
                r'env:\s*\n\s*-\s*name:.*\n\s*valueFrom:\s*\n\s*secretKeyRef:',
                re.MULTILINE
            ),
            severity=Severity.LOW,
            confidence=Confidence.MEDIUM,
            impact="Secrets in env vars may be logged or exposed through process listings.",
            root_cause="Secrets mounted as environment variables instead of files.",
            suggested_fix="Mount secrets as files using volumes for better security.",
            file_patterns=['*.yaml', '*.yml'],
            cwe_id="CWE-532"
        ),

        # General web security
        ConfigPattern(
            id="WEB001",
            title="CORS Allow All Origins",
            description="CORS configured to allow any origin.",
            pattern=re.compile(
                r'(?:Access-Control-Allow-Origin|cors.*origin)\s*[=:]\s*["\']?\*["\']?',
                re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.MEDIUM,
            impact="Cross-origin requests from any domain allowed, potential for data theft.",
            root_cause="CORS misconfigured to allow all origins.",
            suggested_fix="Specify exact allowed origins instead of wildcard.",
            file_patterns=['*.py', '*.js', '*.ts', '*.conf', 'nginx.conf'],
            cwe_id="CWE-346"
        ),
        ConfigPattern(
            id="WEB002",
            title="HTTP Instead of HTTPS",
            description="Hardcoded HTTP URL found where HTTPS should be used.",
            pattern=re.compile(
                r'(?:api[_-]?url|base[_-]?url|endpoint)\s*[=:]\s*["\']http://(?!localhost|127\.0\.0\.1)',
                re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.MEDIUM,
            impact="Data transmitted in plaintext, susceptible to interception.",
            root_cause="Non-secure HTTP used for API or endpoint URLs.",
            suggested_fix="Use HTTPS for all external URLs.",
            file_patterns=['*.py', '*.js', '*.ts', '*.json', '.env*'],
            cwe_id="CWE-319"
        ),
    ]
    
    def __init__(self):
        """Initialize the configuration scanner."""
        super().__init__()
    
    def _matches_file_pattern(self, file_path: str, patterns: List[str]) -> bool:
        """Check if file path matches any of the patterns."""
        import os
        import fnmatch
        
        filename = os.path.basename(file_path)
        
        for pattern in patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
            if fnmatch.fnmatch(file_path, pattern):
                return True
        
        return False
    
    def scan(
        self, 
        files: Dict[str, str],
        **kwargs
    ) -> List[VulnerabilityResult]:
        """
        Scan configuration files for misconfigurations.
        
        Args:
            files: Dictionary of file paths to contents
            
        Returns:
            List of vulnerability results
        """
        results = []
        
        for config_pattern in self.CONFIG_PATTERNS:
            for file_path, content in files.items():
                # Check if file matches the pattern's applicable files
                if not self._matches_file_pattern(file_path, config_pattern.file_patterns):
                    continue
                
                try:
                    matches = list(config_pattern.pattern.finditer(content))
                    
                    for match in matches:
                        # Get line number
                        line_num = content[:match.start()].count('\n') + 1
                        lines = content.split('\n')
                        line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                        
                        # Skip comments
                        if self._is_comment(line_content, file_path):
                            continue
                        
                        results.append(VulnerabilityResult(
                            title=config_pattern.title,
                            description=config_pattern.description,
                            file_path=file_path,
                            line=line_num,
                            severity=config_pattern.severity,
                            confidence=config_pattern.confidence,
                            vulnerability_type="insecure_configuration",
                            impact=config_pattern.impact,
                            root_cause=config_pattern.root_cause,
                            suggested_fix=config_pattern.suggested_fix,
                            cwe_id=config_pattern.cwe_id,
                            scanner=self.name,
                            raw_match=line_content.strip()[:200]
                        ))
                        
                except Exception as e:
                    logger.warning(f"Config pattern {config_pattern.id} failed on {file_path}: {str(e)}")
        
        # Deduplicate
        results = self._deduplicate(results)
        
        logger.info(f"Found {len(results)} configuration issues")
        return results
    
    def _is_comment(self, line: str, file_path: str) -> bool:
        """Check if line is a comment."""
        import os
        stripped = line.strip()
        _, ext = os.path.splitext(file_path.lower())
        
        comment_starters = ['#', '//', '/*', '*', '<!--', '%', ';']
        
        # YAML comments
        if ext in ['.yml', '.yaml']:
            return stripped.startswith('#')
        
        return any(stripped.startswith(s) for s in comment_starters)
    
    def _deduplicate(self, results: List[VulnerabilityResult]) -> List[VulnerabilityResult]:
        """Remove duplicate findings."""
        seen = set()
        unique = []
        
        for result in results:
            key = (result.title, result.file_path, result.line)
            if key not in seen:
                seen.add(key)
                unique.append(result)
        
        return unique
