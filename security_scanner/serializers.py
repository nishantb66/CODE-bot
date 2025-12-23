"""
Security Scanner Serializers

Request/Response validation for the security scanner API.
"""
from rest_framework import serializers


class SecurityScanRequestSerializer(serializers.Serializer):
    """
    Request serializer for initiating a security scan.
    """
    repository_url = serializers.URLField(
        required=True,
        help_text="GitHub repository URL to scan (must be public)"
    )
    
    include_low_confidence = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Include low-confidence findings"
    )
    
    max_files = serializers.IntegerField(
        required=False,
        default=500,
        min_value=10,
        max_value=1000,
        help_text="Maximum number of files to scan"
    )
    
    def validate_repository_url(self, value):
        """Validate that URL is a GitHub repository URL."""
        import re
        
        github_patterns = [
            r'https?://github\.com/[^/]+/[^/]+/?',
            r'git@github\.com:[^/]+/[^/]+(?:\.git)?',
        ]
        
        for pattern in github_patterns:
            if re.match(pattern, value):
                return value
        
        raise serializers.ValidationError(
            "Invalid GitHub repository URL. "
            "Please provide a valid URL like: https://github.com/owner/repo"
        )


class VulnerabilitySerializer(serializers.Serializer):
    """
    Serializer for individual vulnerability findings.
    """
    title = serializers.CharField()
    description = serializers.CharField()
    file_path = serializers.CharField()
    line = serializers.CharField(allow_blank=True)
    end_line = serializers.CharField(allow_blank=True)
    severity = serializers.CharField()
    confidence = serializers.CharField()
    vulnerability_type = serializers.CharField()
    impact = serializers.CharField()
    root_cause = serializers.CharField()
    suggested_fix = serializers.CharField()
    suggested_version = serializers.CharField(allow_blank=True)
    cve_id = serializers.CharField(allow_blank=True)
    cwe_id = serializers.CharField(allow_blank=True)
    cvss_score = serializers.FloatField(allow_null=True)
    references = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    scanner = serializers.CharField()
    package_name = serializers.CharField(allow_blank=True)
    current_version = serializers.CharField(allow_blank=True)


class ScanSummarySerializer(serializers.Serializer):
    """
    Serializer for scan summary counts.
    """
    critical = serializers.IntegerField()
    high = serializers.IntegerField()
    medium = serializers.IntegerField()
    low = serializers.IntegerField()


class SecurityScanResponseSerializer(serializers.Serializer):
    """
    Response serializer for security scan results.
    """
    success = serializers.BooleanField(default=True)
    repository_url = serializers.CharField()
    scan_started_at = serializers.DateTimeField(allow_null=True)
    scan_completed_at = serializers.DateTimeField(allow_null=True)
    scan_duration_ms = serializers.IntegerField()
    files_scanned = serializers.IntegerField()
    total_vulnerabilities = serializers.IntegerField()
    summary = ScanSummarySerializer()
    critical = VulnerabilitySerializer(many=True)
    high = VulnerabilitySerializer(many=True)
    medium = VulnerabilitySerializer(many=True)
    low = VulnerabilitySerializer(many=True)
    error = serializers.CharField(allow_null=True, allow_blank=True)
    metadata = serializers.DictField(required=False)


class ScanHistorySerializer(serializers.Serializer):
    """
    Serializer for scan history entries.
    """
    id = serializers.IntegerField()
    repository_url = serializers.CharField()
    repository_name = serializers.CharField()
    status = serializers.CharField()
    started_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField(allow_null=True)
    duration_ms = serializers.IntegerField()
    files_scanned = serializers.IntegerField()
    critical_count = serializers.IntegerField()
    high_count = serializers.IntegerField()
    medium_count = serializers.IntegerField()
    low_count = serializers.IntegerField()
    total_vulnerabilities = serializers.IntegerField()
    has_critical_issues = serializers.BooleanField()
