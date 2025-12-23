"""
Code Pattern Scanner

Scans source code for security vulnerabilities using regex patterns.
Detects SQL injection, command injection, XSS, and other common vulnerabilities.
Enhanced with production-grade advanced patterns for comprehensive security analysis.
"""
import re
import logging
from typing import Dict, List, Optional, Set
from security_scanner.engine.base_scanner import BaseScanner
from security_scanner.core.result import VulnerabilityResult
from security_scanner.core.severity import Severity, Confidence
from security_scanner.core.patterns import VulnerabilityPatterns, VulnerabilityPattern
from security_scanner.core.advanced_patterns import AdvancedPatterns

logger = logging.getLogger(__name__)


class CodePatternScanner(BaseScanner):
    """
    Scans source code for vulnerability patterns.
    
    Production-grade scanner that detects:
    - SQL Injection
    - Command Injection
    - XSS
    - Insecure Deserialization
    - Path Traversal
    - Weak Cryptography
    - Authentication Issues
    - Authorization Problems
    - Business Logic Flaws
    -Framework-Specific Vulnerabilities
    """
    
    name = "code_pattern"
    description = "Scans source code for vulnerability patterns (Production Grade)"
    
    # File extensions to scan
    SCANNABLE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx',
        '.java', '.go', '.rb', '.php',
        '.cs', '.rs', '.swift', '.kt'
    }
    
    def __init__(self):
        """Initialize the code pattern scanner with basic and advanced patterns."""
        super().__init__()
        self.patterns = VulnerabilityPatterns()
        self.advanced_patterns = AdvancedPatterns()
    
    def is_applicable(self, file_path: str) -> bool:
        """Check if file is a source code file."""
        import os
        _, ext = os.path.splitext(file_path.lower())
        return ext in self.SCANNABLE_EXTENSIONS
    
    def scan(
        self, 
        files: Dict[str, str],
        **kwargs
    ) -> List[VulnerabilityResult]:
        """
        Scan source code files for vulnerability patterns.
        
        Args:
            files: Dictionary of file paths to contents
            
        Returns:
            List of vulnerability results
        """
        results = []
        
        for file_path, content in files.items():
            if not self.is_applicable(file_path):
                continue
            
            try:
                file_results = self._scan_file(file_path, content)
                results.extend(file_results)
            except Exception as e:
                logger.warning(f"Error scanning {file_path}: {str(e)}")
        
        # Filter false positives
        results = self.filter_false_positives(results, files)
        
        logger.info(f"Found {len(results)} code pattern vulnerabilities")
        return results
    
    def _scan_file(
        self, 
        file_path: str, 
        content: str
    ) -> List[VulnerabilityResult]:
        """Scan a single file for vulnerability patterns."""
        results = []
        
        # Get applicable patterns for this file type (basic patterns)
        patterns = self.patterns.get_patterns_for_file(file_path)
        
        # Add advanced patterns
        advanced_patterns = self.advanced_patterns.get_all_advanced_patterns()
        # Filter advanced patterns by file extension if specified
        import os
        _, ext = os.path.splitext(file_path.lower())
        for adv_pattern in advanced_patterns:
            if adv_pattern.file_extensions is None or ext in adv_pattern.file_extensions:
                patterns.append(adv_pattern)
        
        # Skip secret patterns (handled by SecretScanner)
        patterns = [p for p in patterns if 'secret' not in p.vulnerability_type.lower()
                   and 'hardcoded' not in p.vulnerability_type.lower()
                   and 'api_key' not in p.vulnerability_type.lower()
                   and 'private_key' not in p.vulnerability_type.lower()]
        
        lines = content.split('\n')
        
        for pattern in patterns:
            try:
                # Find all matches
                for match in pattern.pattern.finditer(content):
                    # Get line number
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # Get the actual line content
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                    
                    # Check exclude patterns (false positive reduction)
                    if self._should_exclude(match.group(0), line_content, pattern):
                        continue
                    
                    # Check if in comment
                    if self._is_in_comment(line_content, file_path):
                        continue
                    
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
                        raw_match=line_content.strip()[:200]  # Limit length
                    ))
                    
            except Exception as e:
                logger.warning(f"Pattern {pattern.id} failed on {file_path}: {str(e)}")
        
        return results
    
    def _should_exclude(
        self, 
        match_text: str, 
        line_content: str,
        pattern: VulnerabilityPattern
    ) -> bool:
        """Check if match should be excluded (false positive)."""
        # Check pattern-specific exclusions
        if pattern.exclude_patterns:
            for exclude in pattern.exclude_patterns:
                if exclude.search(match_text) or exclude.search(line_content):
                    return True
        
        # Generic false positive indicators
        false_positive_indicators = [
            r'test',
            r'mock',
            r'fake',
            r'dummy',
            r'example',
            r'sample',
            r'placeholder',
        ]
        
        lower_line = line_content.lower()
        for indicator in false_positive_indicators:
            if re.search(indicator, lower_line):
                # Only exclude for medium/low confidence patterns
                if pattern.confidence != Confidence.HIGH:
                    return True
        
        return False
    
    def _is_in_comment(self, line: str, file_path: str) -> bool:
        """Check if the line is a comment."""
        import os
        _, ext = os.path.splitext(file_path.lower())
        
        stripped = line.strip()
        
        # Python comments
        if ext == '.py':
            if stripped.startswith('#'):
                return True
            if stripped.startswith('"""') or stripped.startswith("'''"):
                return True
        
        # JavaScript/TypeScript/Java/C-style comments
        if ext in {'.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.cs', '.rs'}:
            if stripped.startswith('//'):
                return True
            if stripped.startswith('/*') or stripped.startswith('*'):
                return True
        
        # Ruby comments
        if ext == '.rb':
            if stripped.startswith('#'):
                return True
        
        # PHP comments
        if ext == '.php':
            if stripped.startswith('//') or stripped.startswith('#'):
                return True
            if stripped.startswith('/*'):
                return True
        
        return False
    
    def filter_false_positives(
        self, 
        results: List[VulnerabilityResult],
        files: Dict[str, str]
    ) -> List[VulnerabilityResult]:
        """
        Advanced false positive filtering.
        
        Contextual analysis to reduce noise.
        """
        filtered = []
        
        for result in results:
            # Skip if raw_match looks like documentation
            if result.raw_match:
                raw_lower = result.raw_match.lower()
                
                # Skip documentation/comments that slipped through
                doc_indicators = [
                    'example:', 'e.g.', 'usage:', 'note:',
                    '@param', '@return', '@example', 'todo:',
                    '>>>', 'docstring'
                ]
                if any(ind in raw_lower for ind in doc_indicators):
                    continue
                
                # Skip test files for certain vulnerability types
                if '/test' in result.file_path.lower() or '_test.' in result.file_path.lower():
                    if result.confidence != Confidence.HIGH:
                        continue
            
            filtered.append(result)
        
        return filtered
