"""
Security Scanner Admin Configuration
"""
from django.contrib import admin
from security_scanner.models import ScanHistory


@admin.register(ScanHistory)
class ScanHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for ScanHistory model."""
    
    list_display = [
        'id',
        'repository_name',
        'status',
        'user',
        'started_at',
        'duration_ms',
        'total_vulnerabilities',
        'critical_count',
        'high_count',
    ]
    
    list_filter = [
        'status',
        'started_at',
    ]
    
    search_fields = [
        'repository_url',
        'repository_name',
        'user__email',
    ]
    
    readonly_fields = [
        'started_at',
        'completed_at',
        'duration_ms',
        'files_scanned',
        'critical_count',
        'high_count',
        'medium_count',
        'low_count',
        'results',
    ]
    
    ordering = ['-started_at']
    
    def total_vulnerabilities(self, obj):
        return obj.total_vulnerabilities
    total_vulnerabilities.short_description = 'Total'
