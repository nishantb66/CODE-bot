"""
Core utilities for Security Scanner.
"""
from security_scanner.core.result import (
    VulnerabilityResult,
    ScanResult,
    Severity,
    Confidence,
)
from security_scanner.core.severity import SeverityClassifier
from security_scanner.core.patterns import VulnerabilityPatterns

__all__ = [
    'VulnerabilityResult',
    'ScanResult',
    'Severity',
    'Confidence',
    'SeverityClassifier',
    'VulnerabilityPatterns',
]
