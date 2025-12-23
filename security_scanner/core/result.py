"""
Result Data Structures

Defines standardized data structures for vulnerability results
and scan results.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from security_scanner.core.severity import Severity, Confidence


@dataclass
class VulnerabilityResult:
    """
    Represents a single vulnerability finding.
    
    Attributes:
        title: Short descriptive title
        description: Detailed description of the vulnerability
        file_path: Path to the affected file
        line: Line number where vulnerability was found
        severity: Severity level (critical/high/medium/low)
        confidence: Detection confidence level
        vulnerability_type: Category of vulnerability
        impact: Description of potential impact
        root_cause: Explanation of why this is vulnerable
        suggested_fix: How to fix the vulnerability
        suggested_version: Safe version to upgrade to (for dependencies)
        cve_id: CVE identifier if available
        cwe_id: CWE identifier if available
        references: List of reference URLs
        scanner: Name of the scanner that detected this
        raw_match: The actual code/content that matched
    """
    title: str
    description: str
    file_path: str
    severity: Severity
    confidence: Confidence
    vulnerability_type: str
    impact: str
    root_cause: str
    suggested_fix: str
    line: Optional[int] = None
    end_line: Optional[int] = None
    suggested_version: Optional[str] = None
    cve_id: Optional[str] = None
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None
    references: List[str] = field(default_factory=list)
    scanner: str = "unknown"
    raw_match: Optional[str] = None
    package_name: Optional[str] = None
    current_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'line': self.line if self.line else '',
            'end_line': self.end_line if self.end_line else '',
            'severity': self.severity.value if isinstance(self.severity, Severity) else self.severity,
            'confidence': self.confidence.value if isinstance(self.confidence, Confidence) else self.confidence,
            'vulnerability_type': self.vulnerability_type,
            'impact': self.impact,
            'root_cause': self.root_cause,
            'suggested_fix': self.suggested_fix,
            'suggested_version': self.suggested_version or '',
            'cve_id': self.cve_id or '',
            'cwe_id': self.cwe_id or '',
            'cvss_score': self.cvss_score,
            'references': self.references,
            'scanner': self.scanner,
            'package_name': self.package_name or '',
            'current_version': self.current_version or '',
        }
        return result
    
    @property
    def priority_score(self) -> int:
        """Get priority score for sorting."""
        from security_scanner.core.severity import SeverityClassifier
        severity_score = SeverityClassifier.get_priority_score(self.severity)
        confidence_bonus = {'high': 0.3, 'medium': 0.1, 'low': 0}.get(
            self.confidence.value if isinstance(self.confidence, Confidence) else self.confidence, 
            0
        )
        return severity_score + confidence_bonus


@dataclass
class ScanResult:
    """
    Represents the complete result of a security scan.
    
    Attributes:
        repository_url: URL of the scanned repository
        scan_started_at: When the scan started
        scan_completed_at: When the scan completed
        vulnerabilities: List of all vulnerabilities found
        files_scanned: Number of files scanned
        scan_duration_ms: Duration of scan in milliseconds
        error: Error message if scan failed
    """
    repository_url: str
    scan_started_at: datetime = field(default_factory=datetime.utcnow)
    scan_completed_at: Optional[datetime] = None
    vulnerabilities: List[VulnerabilityResult] = field(default_factory=list)
    files_scanned: int = 0
    scan_duration_ms: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_vulnerability(self, vuln: VulnerabilityResult) -> None:
        """Add a vulnerability to the results."""
        self.vulnerabilities.append(vuln)
    
    def add_vulnerabilities(self, vulns: List[VulnerabilityResult]) -> None:
        """Add multiple vulnerabilities to the results."""
        self.vulnerabilities.extend(vulns)
    
    def complete_scan(self) -> None:
        """Mark the scan as complete."""
        self.scan_completed_at = datetime.utcnow()
        if self.scan_started_at:
            delta = self.scan_completed_at - self.scan_started_at
            self.scan_duration_ms = int(delta.total_seconds() * 1000)
    
    def get_by_severity(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get vulnerabilities grouped by severity.
        
        Returns:
            Dict with keys: critical, high, medium, low
        """
        result = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
        }
        
        # Sort by priority score (highest first)
        sorted_vulns = sorted(
            self.vulnerabilities,
            key=lambda v: v.priority_score,
            reverse=True
        )
        
        for vuln in sorted_vulns:
            severity_key = vuln.severity.value if isinstance(vuln.severity, Severity) else vuln.severity
            if severity_key in result:
                result[severity_key].append(vuln.to_dict())
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        by_severity = self.get_by_severity()
        
        return {
            'repository_url': self.repository_url,
            'scan_started_at': self.scan_started_at.isoformat() if self.scan_started_at else None,
            'scan_completed_at': self.scan_completed_at.isoformat() if self.scan_completed_at else None,
            'scan_duration_ms': self.scan_duration_ms,
            'files_scanned': self.files_scanned,
            'total_vulnerabilities': len(self.vulnerabilities),
            'summary': {
                'critical': len(by_severity['critical']),
                'high': len(by_severity['high']),
                'medium': len(by_severity['medium']),
                'low': len(by_severity['low']),
            },
            'critical': by_severity['critical'],
            'high': by_severity['high'],
            'medium': by_severity['medium'],
            'low': by_severity['low'],
            'error': self.error,
            'metadata': self.metadata,
        }
    
    @property
    def has_critical(self) -> bool:
        """Check if any critical vulnerabilities were found."""
        return any(
            v.severity == Severity.CRITICAL 
            for v in self.vulnerabilities
        )
    
    @property
    def is_clean(self) -> bool:
        """Check if no vulnerabilities were found."""
        return len(self.vulnerabilities) == 0
