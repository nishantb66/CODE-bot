"""
Severity Classification Module

Provides standardized severity levels and classification logic
for security vulnerabilities.
"""
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    
    @classmethod
    def from_cvss(cls, score: float) -> 'Severity':
        """
        Convert CVSS score to severity level.
        
        CVSS v3.0 Severity Ratings:
        - 0.0: None
        - 0.1-3.9: Low
        - 4.0-6.9: Medium
        - 7.0-8.9: High
        - 9.0-10.0: Critical
        """
        if score >= 9.0:
            return cls.CRITICAL
        elif score >= 7.0:
            return cls.HIGH
        elif score >= 4.0:
            return cls.MEDIUM
        elif score >= 0.1:
            return cls.LOW
        return cls.INFO
    
    @classmethod
    def from_string(cls, severity_str: str) -> 'Severity':
        """Convert string to Severity enum."""
        severity_map = {
            'critical': cls.CRITICAL,
            'high': cls.HIGH,
            'medium': cls.MEDIUM,
            'moderate': cls.MEDIUM,
            'low': cls.LOW,
            'info': cls.INFO,
            'informational': cls.INFO,
        }
        return severity_map.get(severity_str.lower(), cls.INFO)


class Confidence(str, Enum):
    """Detection confidence levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    
    @classmethod
    def from_score(cls, score: float) -> 'Confidence':
        """Convert confidence score (0-1) to level."""
        if score >= 0.8:
            return cls.HIGH
        elif score >= 0.5:
            return cls.MEDIUM
        return cls.LOW


class SeverityClassifier:
    """
    Classifies vulnerabilities by severity based on various factors.
    """
    
    # Vulnerability type to base severity mapping
    TYPE_SEVERITY_MAP = {
        # Critical
        'rce': Severity.CRITICAL,
        'remote_code_execution': Severity.CRITICAL,
        'sql_injection': Severity.CRITICAL,
        'command_injection': Severity.CRITICAL,
        'ssrf': Severity.CRITICAL,
        'xxe': Severity.CRITICAL,
        'deserialization': Severity.CRITICAL,
        'authentication_bypass': Severity.CRITICAL,
        'hardcoded_secret': Severity.CRITICAL,
        'private_key_exposure': Severity.CRITICAL,
        'api_key_exposure': Severity.CRITICAL,
        
        # High
        'xss': Severity.HIGH,
        'csrf': Severity.HIGH,
        'path_traversal': Severity.HIGH,
        'insecure_deserialization': Severity.HIGH,
        'broken_authentication': Severity.HIGH,
        'sensitive_data_exposure': Severity.HIGH,
        'insecure_direct_object_reference': Severity.HIGH,
        'weak_cryptography': Severity.HIGH,
        'hardcoded_password': Severity.HIGH,
        'debug_mode_enabled': Severity.HIGH,
        
        # Medium
        'insecure_configuration': Severity.MEDIUM,
        'missing_security_header': Severity.MEDIUM,
        'weak_password_policy': Severity.MEDIUM,
        'insufficient_logging': Severity.MEDIUM,
        'cors_misconfiguration': Severity.MEDIUM,
        'insecure_cookie': Severity.MEDIUM,
        'deprecated_api': Severity.MEDIUM,
        'outdated_dependency': Severity.MEDIUM,
        
        # Low
        'information_disclosure': Severity.LOW,
        'verbose_error': Severity.LOW,
        'missing_rate_limiting': Severity.LOW,
        'insecure_http': Severity.LOW,
    }
    
    @classmethod
    def classify(
        cls,
        vuln_type: str,
        cvss_score: Optional[float] = None,
        exploitability: Optional[str] = None,
    ) -> Severity:
        """
        Classify vulnerability severity.
        
        Args:
            vuln_type: Type of vulnerability
            cvss_score: CVSS score if available
            exploitability: Exploitability level if available
        
        Returns:
            Severity enum value
        """
        # If CVSS score available, use it as primary indicator
        if cvss_score is not None:
            return Severity.from_cvss(cvss_score)
        
        # Otherwise, use type-based classification
        vuln_type_lower = vuln_type.lower().replace(' ', '_').replace('-', '_')
        return cls.TYPE_SEVERITY_MAP.get(vuln_type_lower, Severity.MEDIUM)
    
    @classmethod
    def get_priority_score(cls, severity: Severity) -> int:
        """Get numeric priority score for sorting (higher = more severe)."""
        priority_map = {
            Severity.CRITICAL: 4,
            Severity.HIGH: 3,
            Severity.MEDIUM: 2,
            Severity.LOW: 1,
            Severity.INFO: 0,
        }
        return priority_map.get(severity, 0)
