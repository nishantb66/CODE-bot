"""
Security Scanner Models

Database models for storing scan history and results.
"""
from django.db import models
from django.conf import settings


class ScanHistory(models.Model):
    """
    Stores history of security scans performed.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='security_scans',
        null=True,
        blank=True,
        help_text="User who initiated the scan"
    )
    
    repository_url = models.URLField(
        max_length=500,
        help_text="GitHub repository URL that was scanned"
    )
    
    repository_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Repository name (owner/repo)"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the scan"
    )
    
    started_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the scan started"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the scan completed"
    )
    
    duration_ms = models.IntegerField(
        default=0,
        help_text="Scan duration in milliseconds"
    )
    
    files_scanned = models.IntegerField(
        default=0,
        help_text="Number of files scanned"
    )
    
    # Vulnerability counts
    critical_count = models.IntegerField(default=0)
    high_count = models.IntegerField(default=0)
    medium_count = models.IntegerField(default=0)
    low_count = models.IntegerField(default=0)
    
    # Results stored as JSON
    results = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full scan results in JSON format"
    )
    
    error_message = models.TextField(
        blank=True,
        help_text="Error message if scan failed"
    )
    
    class Meta:
        verbose_name = "Scan History"
        verbose_name_plural = "Scan Histories"
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'started_at']),
            models.Index(fields=['repository_url']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Scan of {self.repository_name or self.repository_url} - {self.status}"
    
    @property
    def total_vulnerabilities(self) -> int:
        """Get total number of vulnerabilities found."""
        return self.critical_count + self.high_count + self.medium_count + self.low_count
    
    @property
    def has_critical_issues(self) -> bool:
        """Check if scan found critical issues."""
        return self.critical_count > 0
