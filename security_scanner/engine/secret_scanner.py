"""
Secret Scanner

Detects hardcoded secrets, API keys, passwords, and credentials
in source code and configuration files.
"""
import re
import logging
import hashlib
from typing import Dict, List, Set, Tuple
from security_scanner.engine.base_scanner import BaseScanner
from security_scanner.core.result import VulnerabilityResult
from security_scanner.core.severity import Severity, Confidence
from security_scanner.core.patterns import VulnerabilityPatterns

logger = logging.getLogger(__name__)


class SecretScanner(BaseScanner):
    """
    Scans for hardcoded secrets and credentials.
    
    Detects:
    - API keys (AWS, GCP, Stripe, etc.)
    - Private keys
    - Database credentials
    - JWT secrets
    - Passwords
    - OAuth tokens
    """
    
    name = "secret"
    description = "Detects hardcoded secrets and credentials"
    
    # Files that commonly contain secrets (should be scanned carefully)
    SECRET_FILES = {
        '.env', '.env.local', '.env.production', '.env.development',
        'config.py', 'config.js', 'settings.py', 'secrets.py',
        'credentials.json', 'secrets.json', 'config.json',
        '.npmrc', '.pypirc', 'docker-compose.yml', 'docker-compose.yaml'
    }
    
    # Files to skip (likely false positives)
    SKIP_PATTERNS = [
        r'\.lock$',
        r'\.min\.js$',
        r'\.min\.css$',
        r'node_modules/',
        r'vendor/',
        r'\.git/',
        r'test.*\.py$',
        r'_test\.py$',
        r'\.test\.js$',
        r'\.spec\.js$',
        r'mock',
        r'fixture',
    ]
    
    # Known test/example patterns that should be excluded
    FALSE_POSITIVE_PATTERNS = [
        re.compile(r'example', re.IGNORECASE),
        re.compile(r'test', re.IGNORECASE),
        re.compile(r'fake', re.IGNORECASE),
        re.compile(r'dummy', re.IGNORECASE),
        re.compile(r'sample', re.IGNORECASE),
        re.compile(r'placeholder', re.IGNORECASE),
        re.compile(r'your[_-]?(api[_-]?)?key', re.IGNORECASE),
        re.compile(r'xxx+', re.IGNORECASE),
        re.compile(r'12345', re.IGNORECASE),
        re.compile(r'changeme', re.IGNORECASE),
        re.compile(r'password123', re.IGNORECASE),
        re.compile(r'sk_test_', re.IGNORECASE),  # Stripe test keys are OK
    ]
    
    # Entropy threshold for detecting random strings (secrets)
    ENTROPY_THRESHOLD = 3.5
    
    def __init__(self):
        """Initialize the secret scanner."""
        super().__init__()
        self.patterns = VulnerabilityPatterns()
        self._found_secrets: Set[str] = set()  # For deduplication
    
    def _should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped."""
        for pattern in self.SKIP_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                return True
        return False
    
    def scan(
        self, 
        files: Dict[str, str],
        **kwargs
    ) -> List[VulnerabilityResult]:
        """
        Scan files for hardcoded secrets.
        
        Args:
            files: Dictionary of file paths to contents
            
        Returns:
            List of vulnerability results
        """
        results = []
        self._found_secrets.clear()
        
        for file_path, content in files.items():
            if self._should_skip_file(file_path):
                continue
            
            try:
                file_results = self._scan_file(file_path, content)
                results.extend(file_results)
            except Exception as e:
                logger.warning(f"Error scanning {file_path} for secrets: {str(e)}")
        
        # Filter and deduplicate
        results = self._deduplicate_results(results)
        
        logger.info(f"Found {len(results)} potential secrets")
        return results
    
    def _scan_file(
        self, 
        file_path: str, 
        content: str
    ) -> List[VulnerabilityResult]:
        """Scan a single file for secrets."""
        results = []
        
        # Get secret patterns
        secret_patterns = self.patterns.SECRET_PATTERNS
        
        lines = content.split('\n')
        
        for pattern in secret_patterns:
            for match in pattern.pattern.finditer(content):
                # Get line number
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                # Extract the matched secret value
                matched_text = match.group(0)
                
                # Apply false positive checks
                if self._is_false_positive(matched_text, line_content, file_path):
                    continue
                
                # Skip if in comment
                if self._is_in_comment(line_content, file_path):
                    continue
                
                # Check entropy for generic patterns
                if pattern.confidence == Confidence.MEDIUM:
                    secret_value = self._extract_secret_value(matched_text)
                    if secret_value and self._calculate_entropy(secret_value) < self.ENTROPY_THRESHOLD:
                        continue
                
                # Deduplicate by secret hash
                secret_hash = hashlib.sha256(matched_text.encode()).hexdigest()[:16]
                if secret_hash in self._found_secrets:
                    continue
                self._found_secrets.add(secret_hash)
                
                # Mask the secret for display
                masked_line = self._mask_secret_in_line(line_content, matched_text)
                
                results.append(VulnerabilityResult(
                    title=pattern.title,
                    description=pattern.description,
                    file_path=file_path,
                    line=line_num,
                    severity=pattern.severity,
                    confidence=pattern.confidence,
                    vulnerability_type=pattern.vulnerability_type,
                    impact=pattern.impact,
                    root_cause=pattern.root_cause,
                    suggested_fix=pattern.suggested_fix,
                    cwe_id=pattern.cwe_id,
                    scanner=self.name,
                    raw_match=masked_line[:200]  # Show masked version
                ))
        
        return results
    
    def _is_false_positive(
        self, 
        matched_text: str, 
        line_content: str,
        file_path: str
    ) -> bool:
        """Check if the match is likely a false positive."""
        # Check against known false positive patterns
        for fp_pattern in self.FALSE_POSITIVE_PATTERNS:
            if fp_pattern.search(matched_text):
                return True
            if fp_pattern.search(line_content):
                return True
        
        # Check if in documentation or comments
        import os
        filename = os.path.basename(file_path).lower()
        if 'readme' in filename or 'doc' in filename:
            return True
        
        # Check for common template placeholders
        placeholders = [
            '<your', '{{', '${', '%{', 
            'YOUR_', 'ENTER_', 'INSERT_', 'REPLACE_',
            '***', '---', '...'
        ]
        for placeholder in placeholders:
            if placeholder in matched_text.upper():
                return True
        
        return False
    
    def _is_in_comment(self, line: str, file_path: str) -> bool:
        """Check if the line is a comment."""
        import os
        _, ext = os.path.splitext(file_path.lower())
        
        stripped = line.strip()
        
        # Common comment patterns
        comment_starts = ['#', '//', '/*', '*', '"""', "'''", '<!--', '%', ';']
        
        for start in comment_starts:
            if stripped.startswith(start):
                return True
        
        return False
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of a string."""
        import math
        from collections import Counter
        
        if not text:
            return 0.0
        
        counter = Counter(text)
        length = len(text)
        
        entropy = 0.0
        for count in counter.values():
            probability = count / length
            entropy -= probability * math.log2(probability)
        
        return entropy
    
    def _extract_secret_value(self, matched_text: str) -> str:
        """Extract the actual secret value from a match."""
        # Remove common key-value patterns
        value_patterns = [
            r'["\']([^"\']+)["\']',  # Quoted string
            r'=\s*([^\s;,\n]+)',      # Assignment
            r':\s*([^\s;,\n]+)',      # Colon separator
        ]
        
        for pattern in value_patterns:
            match = re.search(pattern, matched_text)
            if match:
                return match.group(1)
        
        return matched_text
    
    def _mask_secret_in_line(self, line: str, secret: str) -> str:
        """Mask the secret value in the line for safe display."""
        # Find the secret in the line and replace with masked version
        if len(secret) > 8:
            visible_start = secret[:4]
            visible_end = secret[-4:]
            masked = f"{visible_start}{'*' * 8}{visible_end}"
            return line.replace(secret, masked)
        else:
            masked = '*' * len(secret)
            return line.replace(secret, masked)
    
    def _deduplicate_results(
        self, 
        results: List[VulnerabilityResult]
    ) -> List[VulnerabilityResult]:
        """Remove duplicate findings (same secret in multiple places)."""
        seen = set()
        unique = []
        
        for result in results:
            # Create key based on title and file
            key = (result.title, result.file_path, result.line)
            
            if key not in seen:
                seen.add(key)
                unique.append(result)
        
        return unique
