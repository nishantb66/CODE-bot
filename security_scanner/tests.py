"""
Security Scanner Tests

Unit tests for the security scanner components.
"""
from django.test import TestCase
from security_scanner.core.severity import Severity, Confidence, SeverityClassifier
from security_scanner.core.result import VulnerabilityResult, ScanResult
from security_scanner.services.dependency_parser import DependencyParser
from security_scanner.engine.secret_scanner import SecretScanner
from security_scanner.engine.code_pattern_scanner import CodePatternScanner


class SeverityTestCase(TestCase):
    """Tests for severity classification."""
    
    def test_cvss_to_severity_critical(self):
        """Test CVSS 9.0+ maps to CRITICAL."""
        self.assertEqual(Severity.from_cvss(9.5), Severity.CRITICAL)
        self.assertEqual(Severity.from_cvss(10.0), Severity.CRITICAL)
    
    def test_cvss_to_severity_high(self):
        """Test CVSS 7.0-8.9 maps to HIGH."""
        self.assertEqual(Severity.from_cvss(7.0), Severity.HIGH)
        self.assertEqual(Severity.from_cvss(8.9), Severity.HIGH)
    
    def test_cvss_to_severity_medium(self):
        """Test CVSS 4.0-6.9 maps to MEDIUM."""
        self.assertEqual(Severity.from_cvss(4.0), Severity.MEDIUM)
        self.assertEqual(Severity.from_cvss(6.9), Severity.MEDIUM)
    
    def test_cvss_to_severity_low(self):
        """Test CVSS 0.1-3.9 maps to LOW."""
        self.assertEqual(Severity.from_cvss(0.1), Severity.LOW)
        self.assertEqual(Severity.from_cvss(3.9), Severity.LOW)


class DependencyParserTestCase(TestCase):
    """Tests for dependency parsing."""
    
    def test_parse_requirements_txt(self):
        """Test parsing Python requirements.txt."""
        parser = DependencyParser()
        content = """
django==4.2.0
requests>=2.28.0
flask~=2.3.0
# This is a comment
numpy==1.24.0
        """
        
        deps = parser.parse_file('requirements.txt', content)
        
        self.assertGreater(len(deps), 0)
        
        names = [d.name for d in deps]
        self.assertIn('django', names)
        self.assertIn('requests', names)
        self.assertIn('flask', names)
        self.assertIn('numpy', names)
    
    def test_parse_package_json(self):
        """Test parsing Node.js package.json."""
        parser = DependencyParser()
        content = '''
{
    "name": "test-app",
    "dependencies": {
        "express": "^4.18.0",
        "lodash": "4.17.21"
    },
    "devDependencies": {
        "jest": "^29.0.0"
    }
}
        '''
        
        deps = parser.parse_file('package.json', content)
        
        self.assertGreater(len(deps), 0)
        
        names = [d.name for d in deps]
        self.assertIn('express', names)
        self.assertIn('lodash', names)


class SecretScannerTestCase(TestCase):
    """Tests for secret detection."""
    
    def test_detect_aws_key(self):
        """Test detection of AWS access keys."""
        scanner = SecretScanner()
        files = {
            'config.py': 'AWS_ACCESS_KEY = "AKIAZ3MSJFHEB9JXYZ11"'  # Realistic pattern
        }
        
        results = scanner.scan(files)
        
        # Should detect the AWS key pattern
        # Note: May be 0 if filtered, which is also acceptable behavior
        # The main test is that the scanner runs without error
        self.assertIsNotNone(results)
        self.assertGreater(len(results), 0)
    
    def test_ignore_test_secrets(self):
        """Test that example/test secrets are ignored."""
        scanner = SecretScanner()
        files = {
            'test_config.py': 'API_KEY = "test_example_key_12345"'
        }
        
        results = scanner.scan(files)
        
        # Should be filtered as false positive
        self.assertEqual(len(results), 0)


class ScanResultTestCase(TestCase):
    """Tests for scan result aggregation."""
    
    def test_get_by_severity(self):
        """Test grouping vulnerabilities by severity."""
        result = ScanResult(repository_url="https://github.com/test/repo")
        
        # Add vulnerabilities of different severities
        result.add_vulnerability(VulnerabilityResult(
            title="Critical Issue",
            description="Test",
            file_path="test.py",
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="test",
            impact="Test",
            root_cause="Test",
            suggested_fix="Test"
        ))
        
        result.add_vulnerability(VulnerabilityResult(
            title="Low Issue",
            description="Test",
            file_path="test.py",
            severity=Severity.LOW,
            confidence=Confidence.HIGH,
            vulnerability_type="test",
            impact="Test",
            root_cause="Test",
            suggested_fix="Test"
        ))
        
        by_severity = result.get_by_severity()
        
        self.assertEqual(len(by_severity['critical']), 1)
        self.assertEqual(len(by_severity['low']), 1)
        self.assertEqual(len(by_severity['high']), 0)
        self.assertEqual(len(by_severity['medium']), 0)
