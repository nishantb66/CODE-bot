"""
CI/CD Pipeline Scanner

Detects security vulnerabilities in CI/CD configuration files.
Covers GitHub Actions, GitLab CI, Jenkins, CircleCI, and Travis CI.
"""
import re
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from security_scanner.engine.base_scanner import BaseScanner
from security_scanner.core.result import VulnerabilityResult
from security_scanner.core.severity import Severity, Confidence

logger = logging.getLogger(__name__)


@dataclass
class CICDPattern:
    """CI/CD vulnerability pattern."""
    id: str
    title: str
    description: str
    pattern: re.Pattern
    severity: Severity
    confidence: Confidence
    impact: str
    root_cause: str
    suggested_fix: str
    file_patterns: List[str]
    cwe_id: Optional[str] = None


class CICDScanner(BaseScanner):
    """
    Scans CI/CD configuration files for security issues.
    
    Covers:
    - GitHub Actions
    - GitLab CI
    - Jenkins
    - CircleCI
    - Travis CI
    - Azure Pipelines
    """
    
    name = "cicd"
    description = "Detects CI/CD pipeline vulnerabilities"
    
    CICD_PATTERNS: List[CICDPattern] = [
        # GitHub Actions
        CICDPattern(
            id="GHA001",
            title="GitHub Actions: Script Injection via Untrusted Input",
            description="Workflow uses potentially untrusted input directly in run script.",
            pattern=re.compile(
                r'run:\s*[^\n]*\$\{\{\s*(?:github\.event\.(?:issue|pull_request|comment)\.(?:title|body)|'
                r'github\.event\.(?:inputs|client_payload)\.[^}]+|'
                r'github\.head_ref|github\.event\.(?:review\.body|discussion\.body))\s*\}\}',
                re.MULTILINE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            impact="Command injection in CI/CD pipeline. Attackers can execute arbitrary code by manipulating PR titles, issue bodies, etc.",
            root_cause="Untrusted input from GitHub events used directly in shell scripts without sanitization.",
            suggested_fix="Use an intermediate environment variable: env: TITLE: ${{ github.event.issue.title }} then reference as $TITLE. Or use actions/github-script with proper escaping.",
            file_patterns=['.github/workflows/*.yml', '.github/workflows/*.yaml'],
            cwe_id="CWE-78"
        ),
        CICDPattern(
            id="GHA002",
            title="GitHub Actions: Workflow Triggered by Untrusted Source",
            description="Workflow triggered by pull_request_target with checkout of PR code.",
            pattern=re.compile(
                r'on:\s*(?:pull_request_target|issue_comment|workflow_run)',
                re.MULTILINE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.MEDIUM,
            impact="Attackers can run arbitrary code with repository write access and secrets access.",
            root_cause="Dangerous event trigger combined with PR code checkout.",
            suggested_fix="Avoid checking out PR code in pull_request_target workflows. Use pull_request event when possible.",
            file_patterns=['.github/workflows/*.yml', '.github/workflows/*.yaml'],
            cwe_id="CWE-78"
        ),
        CICDPattern(
            id="GHA003",
            title="GitHub Actions: Secrets in Command Arguments",
            description="Secrets used directly in command line arguments.",
            pattern=re.compile(
                r'run:\s*[^\n]*\$\{\{\s*secrets\.[^}]+\s*\}\}',
                re.MULTILINE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.MEDIUM,
            impact="Secrets may be exposed in process listings or logs despite masking.",
            root_cause="Secrets passed as command line arguments instead of environment variables.",
            suggested_fix="Use environment variables: env: SECRET: ${{ secrets.MY_SECRET }} then use $SECRET in run.",
            file_patterns=['.github/workflows/*.yml', '.github/workflows/*.yaml'],
            cwe_id="CWE-532"
        ),
        CICDPattern(
            id="GHA004",
            title="GitHub Actions: Executable Dependency Not Pinned",
            description="GitHub Action used without version pinning (uses @main or @master).",
            pattern=re.compile(
                r'uses:\s*[^@\n]+@(?:main|master|latest)\b',
                re.MULTILINE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.HIGH,
            impact="Supply chain attack possible if action maintainer's account is compromised.",
            root_cause="Action version not pinned to specific SHA or release tag.",
            suggested_fix="Pin actions to specific SHA: uses: actions/checkout@a81bbbf8298c0fa03ea29cdc473d45769f953675",
            file_patterns=['.github/workflows/*.yml', '.github/workflows/*.yaml'],
            cwe_id="CWE-829"
        ),
        CICDPattern(
            id="GHA005",
            title="GitHub Actions: Workflow Has Write Permissions",
            description="Workflow has write permissions that may not be necessary.",
            pattern=re.compile(
                r'permissions:\s*(?:\n\s+)?(?:contents|packages|pull-requests|issues|actions|id-token):\s*write',
                re.MULTILINE
            ),
            severity=Severity.LOW,
            confidence=Confidence.LOW,
            impact="Excessive permissions increase blast radius if workflow is compromised.",
            root_cause="Workflow granted write permissions beyond what is needed.",
            suggested_fix="Follow principle of least privilege. Only grant permissions that are absolutely required.",
            file_patterns=['.github/workflows/*.yml', '.github/workflows/*.yaml'],
            cwe_id="CWE-250"
        ),

        # GitLab CI
        CICDPattern(
            id="GITLAB001",
            title="GitLab CI: Script with Untrusted Variables",
            description="CI script uses predefined variables that could be manipulated.",
            pattern=re.compile(
                r'script:\s*\n\s*-[^\n]*\$(?:CI_COMMIT_(?:REF_NAME|BRANCH|TAG)|CI_MERGE_REQUEST_(?:TITLE|DESCRIPTION))',
                re.MULTILINE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.MEDIUM,
            impact="Command injection possible through branch names or MR titles.",
            root_cause="Untrusted CI variables used directly in scripts.",
            suggested_fix="Quote variables and validate expected format before use.",
            file_patterns=['.gitlab-ci.yml', '.gitlab-ci.yaml'],
            cwe_id="CWE-78"
        ),
        CICDPattern(
            id="GITLAB002",
            title="GitLab CI: Allow Failure on Security Job",
            description="Security-related job configured with allow_failure: true.",
            pattern=re.compile(
                r'(?:security|sast|dast|scan|audit)[^\n]*:\s*\n(?:[^\n]*\n)*?\s*allow_failure:\s*true',
                re.MULTILINE | re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.MEDIUM,
            impact="Security checks can fail without blocking the pipeline.",
            root_cause="Security job configured to allow failures.",
            suggested_fix="Remove allow_failure: true from security-critical jobs.",
            file_patterns=['.gitlab-ci.yml', '.gitlab-ci.yaml'],
            cwe_id="CWE-693"
        ),

        # Jenkins
        CICDPattern(
            id="JENKINS001",
            title="Jenkins: Script Security Bypass",
            description="Jenkinsfile uses methods that bypass script security.",
            pattern=re.compile(
                r'@(?:NonCPS|Grab)',
                re.MULTILINE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.MEDIUM,
            impact="Script security sandbox can be bypassed, allowing arbitrary code execution.",
            root_cause="Annotations used to bypass Jenkins script security.",
            suggested_fix="Avoid @NonCPS and @Grab. Use approved methods or request admin approval.",
            file_patterns=['Jenkinsfile', 'Jenkinsfile.*'],
            cwe_id="CWE-693"
        ),
        CICDPattern(
            id="JENKINS002",
            title="Jenkins: Credentials in Plain Text",
            description="Credentials appear to be hardcoded in Jenkinsfile.",
            pattern=re.compile(
                r'(?:password|secret|token|key)\s*[=:]\s*["\'][^"\']{8,}["\']',
                re.IGNORECASE | re.MULTILINE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.MEDIUM,
            impact="Credentials exposed in source code and pipeline logs.",
            root_cause="Credentials hardcoded instead of using Jenkins credentials store.",
            suggested_fix="Use credentials() binding: withCredentials([string(credentialsId: 'my-secret', variable: 'SECRET')])",
            file_patterns=['Jenkinsfile', 'Jenkinsfile.*'],
            cwe_id="CWE-798"
        ),
        CICDPattern(
            id="JENKINS003",
            title="Jenkins: Unsafe Script Approval",
            description="Pipeline uses script block without proper sandboxing.",
            pattern=re.compile(
                r'script\s*\{[^}]*(?:evaluate|execute|sh\s+["\'][^"\']*\$)',
                re.MULTILINE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.LOW,
            impact="Script block may execute unsafe operations.",
            root_cause="Script block with potentially dangerous operations.",
            suggested_fix="Avoid script blocks where possible. Use declarative syntax.",
            file_patterns=['Jenkinsfile', 'Jenkinsfile.*'],
            cwe_id="CWE-94"
        ),

        # CircleCI
        CICDPattern(
            id="CIRCLE001",
            title="CircleCI: SSH Fingerprint Exposed",
            description="SSH fingerprint appears to be hardcoded.",
            pattern=re.compile(
                r'fingerprints:\s*\n\s*-\s*["\'][a-f0-9:]{47}["\']',
                re.MULTILINE
            ),
            severity=Severity.LOW,
            confidence=Confidence.HIGH,
            impact="SSH configuration visible in code, though fingerprint itself is not secret.",
            root_cause="SSH fingerprint hardcoded in config.",
            suggested_fix="Use CircleCI contexts or environment variables for sensitive configuration.",
            file_patterns=['.circleci/config.yml', '.circleci/config.yaml'],
            cwe_id="CWE-312"
        ),

        # Travis CI
        CICDPattern(
            id="TRAVIS001",
            title="Travis CI: Secure Environment Variable Exposed",
            description="Environment variable marked secure but pattern suggests exposure risk.",
            pattern=re.compile(
                r'env:\s*\n(?:\s*-\s*)?(?:global:\s*\n)?(?:\s*-\s*)?secure:\s*["\'][^"\']+["\']',
                re.MULTILINE
            ),
            severity=Severity.LOW,
            confidence=Confidence.LOW,
            impact="Encrypted variables configuration requires careful handling.",
            root_cause="Secure variables in Travis configuration.",
            suggested_fix="Ensure secrets are encrypted with `travis encrypt` and not exposed in logs.",
            file_patterns=['.travis.yml', '.travis.yaml'],
            cwe_id="CWE-312"
        ),

        # General CI/CD
        CICDPattern(
            id="CICD001",
            title="CI/CD: Curl Pipe to Shell",
            description="Pipeline downloads and executes script directly (curl | sh pattern).",
            pattern=re.compile(
                r'(?:curl|wget)\s+[^\n|]*\|\s*(?:sh|bash|zsh)',
                re.MULTILINE | re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            impact="Script downloaded and executed without verification. MITM attack possible.",
            root_cause="Untrusted script execution in CI pipeline.",
            suggested_fix="Download script, verify checksum, then execute. Or install tools via package manager.",
            file_patterns=['*.yml', '*.yaml', 'Jenkinsfile', 'Jenkinsfile.*'],
            cwe_id="CWE-494"
        ),
        CICDPattern(
            id="CICD002",
            title="CI/CD: Disabled SSL Verification",
            description="SSL certificate verification disabled in CI/CD script.",
            pattern=re.compile(
                r'(?:--insecure|--no-check-certificate|-k\s|GIT_SSL_NO_VERIFY|NODE_TLS_REJECT_UNAUTHORIZED=0)',
                re.MULTILINE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            impact="Man-in-the-middle attacks possible. Malicious code injection risk.",
            root_cause="SSL verification disabled to work around certificate issues.",
            suggested_fix="Fix certificate issues properly. Never disable SSL verification in CI/CD.",
            file_patterns=['*.yml', '*.yaml', 'Jenkinsfile', 'Jenkinsfile.*', '.circleci/*'],
            cwe_id="CWE-295"
        ),
    ]
    
    def __init__(self):
        """Initialize the CI/CD scanner."""
        super().__init__()
    
    def _matches_file_pattern(self, file_path: str, patterns: List[str]) -> bool:
        """Check if file path matches any of the patterns."""
        import os
        import fnmatch
        
        for pattern in patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
            if fnmatch.fnmatch(os.path.basename(file_path), pattern):
                return True
        
        return False
    
    def _is_cicd_file(self, file_path: str) -> bool:
        """Check if file is a CI/CD configuration file."""
        import os
        
        cicd_paths = [
            '.github/workflows/',
            '.gitlab-ci',
            '.circleci/',
            '.travis',
            'Jenkinsfile',
            'azure-pipelines',
            'bitbucket-pipelines',
        ]
        
        return any(indicator in file_path for indicator in cicd_paths)
    
    def scan(
        self, 
        files: Dict[str, str],
        **kwargs
    ) -> List[VulnerabilityResult]:
        """
        Scan CI/CD configuration files for vulnerabilities.
        
        Args:
            files: Dictionary of file paths to contents
            
        Returns:
            List of vulnerability results
        """
        results = []
        
        for file_path, content in files.items():
            if not self._is_cicd_file(file_path):
                continue
            
            for pattern in self.CICD_PATTERNS:
                if not self._matches_file_pattern(file_path, pattern.file_patterns):
                    continue
                
                try:
                    for match in pattern.pattern.finditer(content):
                        # Get line number
                        line_num = content[:match.start()].count('\n') + 1
                        lines = content.split('\n')
                        line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                        
                        # Skip comments
                        if line_content.strip().startswith('#'):
                            continue
                        
                        results.append(VulnerabilityResult(
                            title=pattern.title,
                            description=pattern.description,
                            file_path=file_path,
                            line=line_num,
                            severity=pattern.severity,
                            confidence=pattern.confidence,
                            vulnerability_type="cicd_vulnerability",
                            impact=pattern.impact,
                            root_cause=pattern.root_cause,
                            suggested_fix=pattern.suggested_fix,
                            cwe_id=pattern.cwe_id,
                            scanner=self.name,
                            raw_match=line_content.strip()[:200]
                        ))
                        
                except Exception as e:
                    logger.warning(f"CI/CD pattern {pattern.id} failed: {str(e)}")
        
        # Deduplicate
        results = self._deduplicate(results)
        
        logger.info(f"Found {len(results)} CI/CD vulnerabilities")
        return results
    
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
