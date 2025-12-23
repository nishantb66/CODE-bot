"""
Direct Code Scanner API Views

Allows users to scan code directly by uploading files or pasting code.
Uses all available scanners for deep analysis.
"""
import logging
import os
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from security_scanner.engine.orchestrator import ScanOrchestrator
from security_scanner.engine.secret_scanner import SecretScanner
from security_scanner.engine.code_pattern_scanner import CodePatternScanner
from security_scanner.engine.config_scanner import ConfigScanner
from security_scanner.engine.dependency_scanner import DependencyScanner
from security_scanner.core.result import ScanResult, VulnerabilityResult
from security_scanner.core.severity import Severity, Confidence

logger = logging.getLogger(__name__)


# Maximum file size: 2MB
MAX_FILE_SIZE = 2 * 1024 * 1024

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {
    # Python
    '.py', '.pyw',
    # JavaScript/TypeScript
    '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    # Java
    '.java',
    # Go
    '.go',
    # Ruby
    '.rb',
    # PHP
    '.php',
    # C/C++
    '.c', '.cpp', '.cc', '.h', '.hpp',
    # Rust
    '.rs',
    # Swift
    '.swift',
    # Kotlin
    '.kt', '.kts',
    # Scala
    '.scala',
    # Configuration
    '.json', '.yaml', '.yml', '.xml', '.toml', '.ini', '.cfg',
    '.env', '.env.local', '.env.production',
    # Shell
    '.sh', '.bash', '.zsh',
    # SQL
    '.sql',
    # Dockerfile
    '', # Dockerfile has no extension
    # Text
    '.txt', '.md',
}


class DirectCodeScanAPIView(APIView):
    """
    API endpoint for scanning code directly without a repository.
    
    Features:
    - Upload a code file (max 2MB)
    - Paste code directly
    - Get detailed vulnerability analysis
    - Uses all available scanners
    
    POST /api/security/scan-code/
    
    Supports:
    - multipart/form-data (file upload)
    - application/json (code paste)
    """
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def post(self, request):
        """
        Scan code directly for vulnerabilities.
        
        Body (JSON):
            code (str): The code to scan
            filename (str): Filename with extension (e.g., "app.py")
            language (str, optional): Programming language
        
        OR
        
        Body (multipart/form-data):
            file: The file to scan
        """
        try:
            # Determine input type
            code = None
            filename = None
            
            # Check for file upload
            if 'file' in request.FILES:
                uploaded_file = request.FILES['file']
                
                # Validate file size
                if uploaded_file.size > MAX_FILE_SIZE:
                    return Response(
                        {
                            'success': False,
                            'error': f'File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Get filename and extension
                filename = uploaded_file.name
                _, ext = os.path.splitext(filename.lower())
                
                # Validate extension
                if ext not in ALLOWED_EXTENSIONS and filename not in ['Dockerfile', 'Makefile', 'Jenkinsfile']:
                    return Response(
                        {
                            'success': False,
                            'error': f'File type not supported. Allowed: {", ".join(sorted(ALLOWED_EXTENSIONS))}'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Read file content
                try:
                    code = uploaded_file.read().decode('utf-8')
                except UnicodeDecodeError:
                    return Response(
                        {
                            'success': False,
                            'error': 'File must be a valid text/code file (UTF-8 encoded)'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Check for code paste
            elif 'code' in request.data:
                code = request.data.get('code', '')
                filename = request.data.get('filename', 'code.txt')
                
                if not code or not code.strip():
                    return Response(
                        {
                            'success': False,
                            'error': 'No code provided'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validate code size
                if len(code) > MAX_FILE_SIZE:
                    return Response(
                        {
                            'success': False,
                            'error': f'Code too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            else:
                return Response(
                    {
                        'success': False,
                        'error': 'No code or file provided. Send either a file or code+filename in the request.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Perform the scan
            logger.info(f"Direct code scan requested for file: {filename}")
            
            result = self._scan_code(code, filename)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception(f"Direct code scan failed: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': f'Scan failed: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _scan_code(self, code: str, filename: str) -> Dict[str, Any]:
        """
        Perform a deep scan on the provided code.
        
        Returns detailed vulnerability report with risks and suggestions.
        """
        from datetime import datetime
        import time
        
        start_time = time.time()
        
        # Create file dict for scanners
        files = {filename: code}
        
        # Initialize scanners
        scanners = [
            SecretScanner(),
            CodePatternScanner(),
            ConfigScanner(),
        ]
        
        # Check if it's a dependency file
        _, ext = os.path.splitext(filename.lower())
        dependency_files = {
            'requirements.txt', 'package.json', 'package-lock.json',
            'yarn.lock', 'Pipfile', 'Pipfile.lock', 'pyproject.toml',
            'go.mod', 'go.sum', 'Cargo.toml', 'Cargo.lock',
            'Gemfile', 'Gemfile.lock', 'composer.json', 'pom.xml',
            'build.gradle'
        }
        
        is_dependency_file = filename.lower() in dependency_files or ext in ['.json', '.lock', '.toml']
        
        if is_dependency_file:
            scanners.append(DependencyScanner())
        
        # Run all scanners
        all_vulnerabilities = []
        scanner_results = {}
        
        for scanner in scanners:
            try:
                scanner.pre_scan_hook(files)
                results = scanner.scan(files)
                results = scanner.post_scan_hook(results)
                
                scanner_results[scanner.name] = len(results)
                all_vulnerabilities.extend(results)
                
            except Exception as e:
                logger.warning(f"Scanner {scanner.name} failed: {str(e)}")
                scanner_results[scanner.name] = f"Error: {str(e)}"
        
        # Deduplicate
        seen = set()
        unique_vulns = []
        for vuln in all_vulnerabilities:
            key = (vuln.title, vuln.file_path, vuln.line or 0)
            if key not in seen:
                seen.add(key)
                unique_vulns.append(vuln)
        
        # Sort by severity
        severity_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3}
        unique_vulns.sort(key=lambda v: severity_order.get(v.severity, 4))
        
        # Calculate metrics
        total_lines = len(code.split('\n'))
        scan_duration = round((time.time() - start_time) * 1000)
        
        # Build risk score
        risk_score = self._calculate_risk_score(unique_vulns)
        risk_level = self._get_risk_level(risk_score)
        
        # Group by severity
        by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
        for vuln in unique_vulns:
            sev = vuln.severity.value if isinstance(vuln.severity, Severity) else vuln.severity
            if sev in by_severity:
                by_severity[sev].append(vuln.to_dict())
        
        # Build detailed report
        report = {
            'success': True,
            'filename': filename,
            'language': self._detect_language(filename),
            'total_lines': total_lines,
            'scan_duration_ms': scan_duration,
            'scanned_at': datetime.utcnow().isoformat(),
            
            # Risk assessment
            'risk_assessment': {
                'score': risk_score,
                'level': risk_level,
                'description': self._get_risk_description(risk_level),
            },
            
            # Summary
            'summary': {
                'total_vulnerabilities': len(unique_vulns),
                'critical': len(by_severity['critical']),
                'high': len(by_severity['high']),
                'medium': len(by_severity['medium']),
                'low': len(by_severity['low']),
            },
            
            # Vulnerabilities by severity
            'vulnerabilities': {
                'critical': by_severity['critical'],
                'high': by_severity['high'],
                'medium': by_severity['medium'],
                'low': by_severity['low'],
            },
            
            # Scanners used
            'scanners_used': list(scanner_results.keys()),
            'scanner_results': scanner_results,
            
            # Recommendations
            'recommendations': self._generate_recommendations(unique_vulns, filename),
            
            # Executive summary
            'executive_summary': self._generate_executive_summary(
                filename, total_lines, unique_vulns, risk_level
            ),
        }
        
        return report
    
    def _calculate_risk_score(self, vulnerabilities: List[VulnerabilityResult]) -> int:
        """Calculate overall risk score (0-100)."""
        if not vulnerabilities:
            return 0
        
        score = 0
        for vuln in vulnerabilities:
            if vuln.severity == Severity.CRITICAL:
                score += 25
            elif vuln.severity == Severity.HIGH:
                score += 15
            elif vuln.severity == Severity.MEDIUM:
                score += 8
            else:
                score += 3
        
        return min(100, score)
    
    def _get_risk_level(self, score: int) -> str:
        """Convert score to risk level."""
        if score >= 75:
            return 'critical'
        elif score >= 50:
            return 'high'
        elif score >= 25:
            return 'medium'
        elif score > 0:
            return 'low'
        return 'safe'
    
    def _get_risk_description(self, level: str) -> str:
        """Get description for risk level."""
        descriptions = {
            'critical': 'Immediate action required. This code contains critical security vulnerabilities that could lead to severe compromise.',
            'high': 'High risk. Significant security issues detected that should be addressed before deployment.',
            'medium': 'Moderate risk. Security concerns found that should be reviewed and addressed.',
            'low': 'Low risk. Minor issues detected, consider addressing when possible.',
            'safe': 'No vulnerabilities detected. The code appears to follow secure coding practices.',
        }
        return descriptions.get(level, 'Unknown risk level')
    
    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename."""
        _, ext = os.path.splitext(filename.lower())
        
        language_map = {
            '.py': 'Python',
            '.pyw': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript (React)',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript (React)',
            '.java': 'Java',
            '.go': 'Go',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.c': 'C',
            '.cpp': 'C++',
            '.cc': 'C++',
            '.h': 'C/C++ Header',
            '.hpp': 'C++ Header',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.xml': 'XML',
            '.toml': 'TOML',
            '.sql': 'SQL',
            '.sh': 'Shell',
            '.bash': 'Bash',
        }
        
        if filename == 'Dockerfile':
            return 'Dockerfile'
        elif filename == 'Jenkinsfile':
            return 'Jenkins Pipeline'
        elif filename == 'Makefile':
            return 'Makefile'
        
        return language_map.get(ext, 'Unknown')
    
    def _generate_recommendations(
        self, 
        vulnerabilities: List[VulnerabilityResult],
        filename: str
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on findings."""
        recommendations = []
        seen_types = set()
        
        for vuln in vulnerabilities:
            if vuln.vulnerability_type not in seen_types:
                seen_types.add(vuln.vulnerability_type)
                
                rec = {
                    'type': vuln.vulnerability_type,
                    'priority': vuln.severity.value if isinstance(vuln.severity, Severity) else vuln.severity,
                    'title': f'Fix {vuln.vulnerability_type.replace("_", " ").title()} Issues',
                    'description': vuln.suggested_fix or f'Review and fix {vuln.vulnerability_type} vulnerabilities.',
                    'affected_count': sum(1 for v in vulnerabilities if v.vulnerability_type == vuln.vulnerability_type),
                }
                recommendations.append(rec)
        
        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda r: priority_order.get(r['priority'], 4))
        
        return recommendations[:10]  # Top 10 recommendations
    
    def _generate_executive_summary(
        self,
        filename: str,
        total_lines: int,
        vulnerabilities: List[VulnerabilityResult],
        risk_level: str
    ) -> str:
        """Generate a human-readable executive summary."""
        if not vulnerabilities:
            return f"Security scan of '{filename}' ({total_lines} lines) completed successfully. No vulnerabilities were detected. The code follows secure coding practices."
        
        critical = sum(1 for v in vulnerabilities if v.severity == Severity.CRITICAL)
        high = sum(1 for v in vulnerabilities if v.severity == Severity.HIGH)
        medium = sum(1 for v in vulnerabilities if v.severity == Severity.MEDIUM)
        low = sum(1 for v in vulnerabilities if v.severity == Severity.LOW)
        
        parts = [f"Security scan of '{filename}' ({total_lines} lines) detected {len(vulnerabilities)} potential security issues."]
        
        if critical:
            parts.append(f"{critical} CRITICAL issue(s) require immediate attention.")
        if high:
            parts.append(f"{high} HIGH severity issue(s) should be addressed promptly.")
        if medium:
            parts.append(f"{medium} MEDIUM severity issue(s) found.")
        if low:
            parts.append(f"{low} LOW severity issue(s) detected.")
        
        # Add top vulnerability types
        vuln_types = {}
        for v in vulnerabilities:
            t = v.vulnerability_type
            vuln_types[t] = vuln_types.get(t, 0) + 1
        
        if vuln_types:
            top_types = sorted(vuln_types.items(), key=lambda x: -x[1])[:3]
            types_str = ", ".join([f"{t.replace('_', ' ')}" for t, _ in top_types])
            parts.append(f"Main concerns: {types_str}.")
        
        return " ".join(parts)
