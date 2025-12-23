"""
Advanced Vulnerability Patterns for Production Use

This module contains comprehensive vulnerability patterns for real-world security scanning.
Includes authentication, authorization, business logic, and framework-specific vulnerabilities.
"""
import re
from dataclasses import dataclass
from typing import List, Pattern, Optional
from security_scanner.core.severity import Severity, Confidence
from security_scanner.core.patterns import VulnerabilityPattern


class AdvancedPatterns:
    """
    Production-grade vulnerability patterns for comprehensive security analysis.
    These patterns detect subtle security issues often missed by basic scanners.
    """
    
    # ==================== AUTHENTICATION & SESSION MANAGEMENT ====================
    AUTHENTICATION_PATTERNS: List[VulnerabilityPattern] = [
        VulnerabilityPattern(
            id="AUTH001",
            title="Missing Authentication Check",
            description="API endpoint or route appears to lack authentication middleware/decorator.",
            pattern=re.compile(
                r'@app\.route\(["\'][^"\']+["\']\)|router\.(?:get|post|put|delete)\(["\']',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.LOW,
            vulnerability_type="missing_authentication",
            impact="Unauthorized access to sensitive endpoints.",
            root_cause="Route defined without authentication middleware.",
            suggested_fix="Add authentication decorator/middleware: @login_required, @jwt_required, or authenticate middleware.",
            cwe_id="CWE-306"
        ),
        VulnerabilityPattern(
            id="AUTH002",
            title="Weak Session Configuration",
            description="Session cookie configured without secure flags.",
            pattern=re.compile(
                r'(?:SESSION_COOKIE_SECURE|cookie\.secure|secure:\s*false|httpOnly:\s*false)',
                re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.HIGH,
            vulnerability_type="insecure_session",
            impact="Session hijacking through XSS or man-in-the-middle attacks.",
            root_cause="Session cookies not marked as Secure and HttpOnly.",
           suggested_fix="Set SESSION_COOKIE_SECURE=True, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax'",
            cwe_id="CWE-614"
        ),
        VulnerabilityPattern(
            id="AUTH003",
            title="Hardcoded Salt or IV",
            description="Cryptographic salt or initialization vector (IV) is hardcoded.",
            pattern=re.compile(
                r'(?:salt|iv|nonce)\s*=\s*["\'](?:[A-Za-z0-9+/=]{16,})["\']',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            vulnerability_type="hardcoded_crypto",
            impact="Predictable encryption allowing attackers to decrypt data.",
            root_cause="Salt/IV should be randomly generated for each encryption operation.",
            suggested_fix="Generate random salt/IV using os.urandom() or crypto.randomBytes().",
            cwe_id="CWE-329"
        ),
        VulnerabilityPattern(
            id="AUTH004",
            title="Insecure Password Storage",
            description="Password appears to be stored in plaintext or with weak hashing.",
            pattern=re.compile(
                r'(?:user\.password|password)\s*=\s*(?:request\.|req\.body\.|password|pwd)',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.MEDIUM,
            vulnerability_type="weak_password_storage",
            impact="Password database compromise exposes user credentials.",
            root_cause="Passwords not properly hashed before storage.",
            suggested_fix="Use bcrypt, scrypt, or Argon2 for password hashing. Never store plaintext passwords.",
            cwe_id="CWE-256"
        ),
    ]
    
    # ==================== AUTHORIZATION & ACCESS CONTROL ====================
    AUTHORIZATION_PATTERNS: List[VulnerabilityPattern] = [
        VulnerabilityPattern(
            id="AUTHZ001",
           title="Insecure Direct Object Reference (IDOR)",
            description="Direct object reference using user-supplied ID without access control check.",
            pattern=re.compile(
                r'(?:get|find|fetch)(?:One|By(?:Id|PK))?\s*\(\s*(?:req\.params|request\.GET|params\.|query\.)',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.MEDIUM,
            vulnerability_type="idor",
            impact="Users can access or modify resources belonging to other users.",
            root_cause="Missing ownership verification before accessing resource.",
            suggested_fix="Verify user owns the resource: if resource.user_id != current_user.id: abort(403)",
            cwe_id="CWE-639"
        ),
        VulnerabilityPattern(
            id="AUTHZ002",
           title="Missing Authorization Check",
            description="Database query or resource access without permission check.",
            pattern=re.compile(
                r'\.(?:delete|update|remove|destroy)\s*\([^)]*(?:req\.params|request\.GET)',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.MEDIUM,
            vulnerability_type="missing_authorization",
            impact="Privilege escalation and unauthorized data modification.",
            root_cause="No check to verify user is authorized to perform this action.",
            suggested_fix="Implement role-based access control (RBAC) or attribute-based access control (ABAC).",
            cwe_id="CWE-862"
        ),
        VulnerabilityPattern(
            id="AUTHZ003",
            title="Mass Assignment Vulnerability",
            description="Direct assignment of user input to model without field filtering.",
            pattern=re.compile(
                r'\.(?:update|create|save)\s*\(\s*(?:req\.body|request\.(?:POST|data)|params\.\*)',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.MEDIUM,
            vulnerability_type="mass_assignment",
            impact="Attacker can modify unintended fields like is_admin, role, or verified.",
            root_cause="No whitelist of allowed fields for mass assignment.",
            suggested_fix="Use strong parameters, whitelisting, or DTOs: Model.create({name: req.body.name, email: req.body.email})",
            cwe_id="CWE-915"
        ),
    ]
    
    # ==================== BUSINESS LOGIC VULNERABILITIES ====================
    BUSINESS_LOGIC_PATTERNS: List[VulnerabilityPattern] = [
        VulnerabilityPattern(
            id="LOGIC001",
            title="Missing Rate Limiting",
            description="Endpoint lacks rate limiting protection.",
            pattern=re.compile(
                r'(?:@app\.route|router\.post|app\.post)\s*\(["\']\/(?:login|register|api|password)',
                re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.LOW,
            vulnerability_type="missing_rate_limit",
            impact="Brute force attacks, credential stuffing, API abuse.",
            root_cause="No rate limiting middleware applied.",
            suggested_fix="Implement rate limiting: @limiter.limit('5 per minute'), use Flask-Limiter, express-rate-limit, or similar.",
            cwe_id="CWE-307"
        ),
        VulnerabilityPattern(
            id="LOGIC002",
            title="Time-of-Check Time-of-Use (TOCTOU)",
            description="Potential race condition between check and use.",
            pattern=re.compile(
                r'if\s+os\.path\.exists\([^)]+\):[^}]*\n[^}]*(?:open|delete|rename)',
                re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.LOW,
            vulnerability_type="race_condition",
            impact="Race condition exploits, file manipulation attacks.",
            root_cause="Check and use operations are not atomic.",
            suggested_fix="Use atomic operations or file locking mechanisms.",
            cwe_id="CWE-367"
        ),
        VulnerabilityPattern(
            id="LOGIC003",
            title="Integer Overflow Risk",
            description="Arithmetic operation that may overflow without bounds checking.",
            pattern=re.compile(
                r'(?:amount|price|quantity|balance)\s*(?:\+|\*)\s*(?:\d+|[\w.]+)',
                re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.LOW,
            vulnerability_type="integer_overflow",
            impact="Unexpected behavior, logic bypasses, financial loss.",
            root_cause="No bounds checking on arithmetic operations.",
            suggested_fix="Add bounds checking and use safe math libraries.",
            cwe_id="CWE-190"
        ),
    ]
    
    # ==================== ERROR HANDLING & INFORMATION DISCLOSURE ====================
    ERROR_HANDLING_PATTERNS: List[VulnerabilityPattern] = [
        VulnerabilityPattern(
            id="ERROR001",
            title="Debug Mode Enabled",
            description="Application running with debug mode enabled.",
            pattern=re.compile(
                r'(?:DEBUG|debug)\s*=\s*True|app\.run\([^)]*debug\s*=\s*True',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            vulnerability_type="debug_mode",
            impact="Sensitive information disclosure, stack traces visible to attackers.",
            root_cause="Debug mode left enabled in production.",
            suggested_fix="Set DEBUG=False in production. Use environment variables.",
            cwe_id="CWE-11"
        ),
        VulnerabilityPattern(
            id="ERROR002",
            title="Sensitive Data in Exception",
            description="Exception handling that may expose sensitive data.",
            pattern=re.compile(
                r'except[^:]*:\s*(?:print|console\.log|logger\.error)\s*\([^)]*(?:password|secret|key|token)',
                re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.MEDIUM,
            vulnerability_type="info_disclosure",
            impact="Sensitive data leaked in logs or error messages.",
            root_cause="Logging sensitive data in error handlers.",
            suggested_fix="Sanitize error messages. Never log passwords, tokens, or keys.",
            cwe_id="CWE-209"
        ),
        VulnerabilityPattern(
            id="ERROR003",
            title="Insufficient Logging",
            description="Critical operation lacks audit logging.",
            pattern=re.compile(
                r'def\s+(?:delete|remove|transfer|update_admin)\s*\([^)]*\):(?!.*log)',
                re.IGNORECASE
            ),
            severity=Severity.LOW,
            confidence=Confidence.LOW,
            vulnerability_type="insufficient_logging",
            impact="Security incidents cannot be properly investigated.",
            root_cause="Critical operations not logged for audit trail.",
            suggested_fix="Add audit logging for sensitive operations: logger.info(f'User {user_id} performed {action}')",
            cwe_id="CWE-778"
        ),
    ]
    
    # ==================== HTTP SECURITY ====================
    HTTP_SECURITY_PATTERNS: List[VulnerabilityPattern] = [
        VulnerabilityPattern(
            id="HTTP001",
            title="Missing HTTPS Enforcement",
            description="Application not enforcing HTTPS.",
            pattern=re.compile(
                r'(?:http://|SECURE_SSL_REDIRECT\s*=\s*False)',
                re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.MEDIUM,
            vulnerability_type="missing_https",
            impact="Man-in-the-middle attacks, data interception.",
            root_cause="HTTPS not enforced.",
            suggested_fix="Use SECURE_SSL_REDIRECT=True, HSTS headers, and redirect HTTP to HTTPS.",
            cwe_id="CWE-319"
        ),
        VulnerabilityPattern(
            id="HTTP002",
            title="Missing Security Headers",
            description="Response lacks important security headers.",
            pattern=re.compile(
                r'response\.headers\[(?!.*(?:X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security))',
                re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.LOW,
            vulnerability_type="missing_headers",
            impact="Clickjacking, MIME-sniffing attacks.",
            root_cause="Security headers not set.",
            suggested_fix="Add headers: X-Frame-Options: DENY, X-Content-Type-Options: nosniff, Strict-Transport-Security: max-age=31536000",
            cwe_id="CWE-693"
        ),
        VulnerabilityPattern(
            id="HTTP003",
            title="Open Redirect Vulnerability",
            description="Redirect using unvalidated user input.",
            pattern=re.compile(
                r'(?:redirect|location\.href|window\.location)\s*=\s*(?:request\.|req\.|params\.|query\.)',
                re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.HIGH,
            vulnerability_type="open_redirect",
            impact="Phishing attacks, credential theft.",
            root_cause="Redirect URL not validated.",
            suggested_fix="Whitelist allowed redirect domains or use relative URLs only.",
            cwe_id="CWE-601"
        ),
    ]
    
    # ==================== FRAMEWORK-SPECIFIC PATTERNS (Django) ====================
    DJANGO_PATTERNS: List[VulnerabilityPattern] = [
        VulnerabilityPattern(
            id="DJANGO001",
            title="Django Secret Key Exposed",
            description="Django SECRET_KEY found in source code.",
            pattern=re.compile(
                r'SECRET_KEY\s*=\s*["\'](?!.*env|.*get)[^"\']{20,}["\']',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="django_secret",
            impact="Session forgery, CSRF bypass, complete application compromise.",
            root_cause="SECRET_KEY hardcoded instead of using environment variable.",
            suggested_fix="Move to environment variable: SECRET_KEY = os.environ['DJANGO_SECRET_KEY']",
            cwe_id="CWE-798",
            file_extensions=['.py']
        ),
        VulnerabilityPattern(
            id="DJANGO002",
            title="Django Raw SQL Query",
            description="Raw SQL query without parameterization.",
            pattern=re.compile(
                r'\.raw\s*\(\s*[fF]?["\'][^"\']*(?:\%s|\{|:)[^"\']*["\']',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="sql_injection",
            impact="SQL injection leading to data breach.",
            root_cause="String formatting used in raw SQL query.",
            suggested_fix="Use parameterized queries: Model.objects.raw('SELECT * FROM table WHERE id = %s', [user_id])",
            cwe_id="CWE-89",
            file_extensions=['.py']
        ),
        VulnerabilityPattern(
            id="DJANGO003",
            title="Django CSRF Exemption",
            description="CSRF protection disabled for view.",
            pattern=re.compile(
                r'@csrf_exempt',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            vulnerability_type="csrf_disabled",
            impact="Cross-Site Request Forgery attacks.",
            root_cause="CSRF protection explicitly disabled.",
            suggested_fix="Remove @csrf_exempt. If absolutely necessary for API, use proper token-based authentication.",
            cwe_id="CWE-352",
            file_extensions=['.py']
        ),
    ]
    
    @classmethod
    def get_all_advanced_patterns(cls) -> List[VulnerabilityPattern]:
        """Get all advanced vulnerability patterns."""
        all_patterns = []
        all_patterns.extend(cls.AUTHENTICATION_PATTERNS)
        all_patterns.extend(cls.AUTHORIZATION_PATTERNS)
        all_patterns.extend(cls.BUSINESS_LOGIC_PATTERNS)
        all_patterns.extend(cls.ERROR_HANDLING_PATTERNS)
        all_patterns.extend(cls.HTTP_SECURITY_PATTERNS)
        all_patterns.extend(cls.DJANGO_PATTERNS)
        return all_patterns
