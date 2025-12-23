"""
Vulnerability Detection Patterns

Comprehensive regex patterns for detecting security vulnerabilities
in source code. These patterns are carefully crafted to minimize
false positives while catching genuine security issues.
"""
import re
from dataclasses import dataclass
from typing import List, Dict, Pattern, Optional
from security_scanner.core.severity import Severity, Confidence


@dataclass
class VulnerabilityPattern:
    """Defines a vulnerability detection pattern."""
    id: str
    title: str
    description: str
    pattern: Pattern
    severity: Severity
    confidence: Confidence
    vulnerability_type: str
    impact: str
    root_cause: str
    suggested_fix: str
    cwe_id: Optional[str] = None
    file_extensions: Optional[List[str]] = None  # None = all files
    exclude_patterns: Optional[List[Pattern]] = None  # Patterns to exclude (false positive reduction)


class VulnerabilityPatterns:
    """
    Collection of vulnerability detection patterns organized by category.
    Patterns are optimized for accuracy with low false positive rates.
    """
    
    # ==================== HARDCODED SECRETS ====================
    SECRET_PATTERNS: List[VulnerabilityPattern] = [
        VulnerabilityPattern(
            id="SECRET001",
            title="AWS Access Key Exposed",
            description="AWS Access Key ID found in source code. This can lead to unauthorized access to AWS resources.",
            pattern=re.compile(
                r'(?:AKIA|A3T|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="hardcoded_secret",
            impact="Attackers can gain full access to AWS account resources, leading to data theft, crypto mining, or infrastructure destruction.",
            root_cause="AWS access key was committed to source code instead of using environment variables or secrets management.",
            suggested_fix="Remove the key immediately, rotate it in AWS IAM console, and use AWS Secrets Manager or environment variables.",
            cwe_id="CWE-798",
            exclude_patterns=[re.compile(r'example|test|fake|dummy|sample', re.IGNORECASE)]
        ),
        VulnerabilityPattern(
            id="SECRET002",
            title="AWS Secret Access Key Exposed",
            description="AWS Secret Access Key found in source code.",
            pattern=re.compile(
                r'(?:aws_secret_access_key|aws_secret_key|secret_access_key)\s*[=:]\s*["\']([A-Za-z0-9/+=]{40})["\']',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="hardcoded_secret",
            impact="Full AWS account compromise possible. Attackers can access all AWS services.",
            root_cause="Secret key stored in source code instead of secure secrets management.",
            suggested_fix="Immediately rotate the key in AWS IAM and use AWS Secrets Manager or environment variables.",
            cwe_id="CWE-798"
        ),
        VulnerabilityPattern(
            id="SECRET003",
            title="GitHub Personal Access Token Exposed",
            description="GitHub Personal Access Token (PAT) found in source code.",
            pattern=re.compile(
                r'ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59}',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="api_key_exposure",
            impact="Unauthorized access to GitHub repositories, ability to push malicious code or steal private repositories.",
            root_cause="GitHub token committed to source code.",
            suggested_fix="Revoke the token immediately in GitHub Settings > Developer settings > Personal access tokens and generate a new one.",
            cwe_id="CWE-798"
        ),
        VulnerabilityPattern(
            id="SECRET004",
            title="Generic API Key Pattern",
            description="Potential API key or secret token found in source code.",
            pattern=re.compile(
                r'(?:api[_-]?key|apikey|api[_-]?secret|api[_-]?token)\s*[=:]\s*["\']([A-Za-z0-9_\-]{20,})["\']',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.MEDIUM,
            vulnerability_type="api_key_exposure",
            impact="Unauthorized access to third-party services. Cost implications if API has usage charges.",
            root_cause="API credentials stored in source code.",
            suggested_fix="Move API keys to environment variables or a secrets management system like HashiCorp Vault.",
            cwe_id="CWE-798",
            exclude_patterns=[re.compile(r'example|test|fake|dummy|sample|YOUR_|xxx|placeholder', re.IGNORECASE)]
        ),
        VulnerabilityPattern(
            id="SECRET005",
            title="Private Key File Content",
            description="Private key content (RSA/DSA/EC/OpenSSH) found in source code.",
            pattern=re.compile(
                r'-----BEGIN\s+(?:RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY-----',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="private_key_exposure",
            impact="Complete compromise of encrypted communications and authentication systems using this key.",
            root_cause="Private key committed to source code repository.",
            suggested_fix="Remove the file, generate new keys, and store private keys securely outside of version control.",
            cwe_id="CWE-321"
        ),
        VulnerabilityPattern(
            id="SECRET006",
            title="Database Connection String with Credentials",
            description="Database connection string with embedded credentials found.",
            pattern=re.compile(
                r'(?:mongodb(?:\+srv)?|mysql|postgresql|postgres|redis|mssql):\/\/[^:]+:[^@]+@[^\/\s]+',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="hardcoded_secret",
            impact="Direct database access allowing data theft, modification, or deletion.",
            root_cause="Database credentials embedded in connection string in source code.",
            suggested_fix="Use environment variables for database credentials and connection strings.",
            cwe_id="CWE-798",
            exclude_patterns=[re.compile(r'localhost|127\.0\.0\.1|example\.com|test|user:pass', re.IGNORECASE)]
        ),
        VulnerabilityPattern(
            id="SECRET007",
            title="JWT Secret Key Exposed",
            description="JWT secret key found in source code.",
            pattern=re.compile(
                r'(?:jwt[_-]?secret|secret[_-]?key|signing[_-]?key)\s*[=:]\s*["\']([A-Za-z0-9_\-!@#$%^&*]{16,})["\']',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.MEDIUM,
            vulnerability_type="hardcoded_secret",
            impact="Attackers can forge valid JWT tokens, bypassing authentication entirely.",
            root_cause="JWT signing secret hardcoded in source code.",
            suggested_fix="Move JWT secret to environment variable and rotate the secret.",
            cwe_id="CWE-798",
            exclude_patterns=[re.compile(r'your[_-]?secret|change[_-]?me|example', re.IGNORECASE)]
        ),
        VulnerabilityPattern(
            id="SECRET008",
            title="Slack Webhook URL Exposed",
            description="Slack incoming webhook URL found in source code.",
            pattern=re.compile(
                r'https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+',
                re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.HIGH,
            vulnerability_type="api_key_exposure",
            impact="Attackers can send messages to your Slack workspace, potentially for phishing or spam.",
            root_cause="Slack webhook URL committed to source code.",
            suggested_fix="Regenerate the webhook URL in Slack and store it as an environment variable.",
            cwe_id="CWE-798"
        ),
        VulnerabilityPattern(
            id="SECRET009",
            title="Google Cloud API Key Exposed",
            description="Google Cloud API key found in source code.",
            pattern=re.compile(
                r'AIza[A-Za-z0-9_\-]{35}',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            vulnerability_type="api_key_exposure",
            impact="Unauthorized use of Google Cloud services, potentially incurring costs or accessing data.",
            root_cause="Google API key committed to source code.",
            suggested_fix="Restrict the API key in Google Cloud Console and regenerate it. Use environment variables.",
            cwe_id="CWE-798"
        ),
        VulnerabilityPattern(
            id="SECRET010",
            title="Stripe API Key Exposed",
            description="Stripe API key (live or test) found in source code.",
            pattern=re.compile(
                r'(?:sk_live_|rk_live_|sk_test_|rk_test_)[A-Za-z0-9]{24,}',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="api_key_exposure",
            impact="Financial fraud, unauthorized transactions, access to customer payment data.",
            root_cause="Stripe API key committed to source code.",
            suggested_fix="Roll the API key immediately in Stripe Dashboard and use environment variables.",
            cwe_id="CWE-798"
        ),
        VulnerabilityPattern(
            id="SECRET011",
            title="Hardcoded Password",
            description="Hardcoded password found in source code.",
            pattern=re.compile(
                r'(?:password|passwd|pwd|pass)\s*[=:]\s*["\'](?![\s\'"]*(?:$|["\']))([^"\']{8,})["\']',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.MEDIUM,
            vulnerability_type="hardcoded_password",
            impact="Unauthorized system access if password is used for authentication.",
            root_cause="Password hardcoded in source code instead of using secure configuration.",
            suggested_fix="Remove hardcoded password and use environment variables or secrets management.",
            cwe_id="CWE-259",
            exclude_patterns=[re.compile(r'example|dummy|test|fake|password123|changeme|your_password', re.IGNORECASE)]
        ),
    ]
    
    # ==================== SQL INJECTION ====================
    SQL_INJECTION_PATTERNS: List[VulnerabilityPattern] = [
        VulnerabilityPattern(
            id="SQLI001",
            title="SQL Injection - String Concatenation (Python)",
            description="SQL query built using string concatenation with user input.",
            pattern=re.compile(
                r'(?:execute|cursor\.execute|raw|rawQuery)\s*\(\s*["\'][^"\']*(?:\%s|\{|\+)[^"\']*["\'](?:\s*%|\s*\.format|\s*\+)',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="sql_injection",
            impact="Complete database compromise. Attackers can read, modify, or delete all data.",
            root_cause="SQL query constructed by concatenating user input without proper sanitization.",
            suggested_fix="Use parameterized queries or ORM. Example: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
            cwe_id="CWE-89",
            file_extensions=['.py']
        ),
        VulnerabilityPattern(
            id="SQLI002",
            title="SQL Injection - f-string (Python)",
            description="SQL query built using f-string with variable interpolation.",
            pattern=re.compile(
                r'(?:execute|cursor\.execute)\s*\(\s*f["\'][^"\']*\{[^}]+\}[^"\']*["\']',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="sql_injection",
            impact="Complete database compromise through SQL injection.",
            root_cause="f-string used to build SQL query allows injection of malicious SQL.",
            suggested_fix="Never use f-strings for SQL. Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
            cwe_id="CWE-89",
            file_extensions=['.py']
        ),
        VulnerabilityPattern(
            id="SQLI003",
            title="SQL Injection - Template Literal (JavaScript/Node.js)",
            description="SQL query built using template literals with variable interpolation.",
            pattern=re.compile(
                r'(?:query|execute|raw)\s*\(\s*`[^`]*\$\{[^}]+\}[^`]*`',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="sql_injection",
            impact="Complete database compromise through SQL injection.",
            root_cause="Template literal used to build SQL query allows variable injection.",
            suggested_fix="Use parameterized queries. Example: db.query('SELECT * FROM users WHERE id = $1', [userId])",
            cwe_id="CWE-89",
            file_extensions=['.js', '.ts', '.jsx', '.tsx']
        ),
        VulnerabilityPattern(
            id="SQLI004",
            title="SQL Injection - String Concatenation (JavaScript)",
            description="SQL query built by concatenating strings in JavaScript.",
            pattern=re.compile(
                r'(?:query|execute)\s*\(\s*["\'][^"\']+["\']?\s*\+\s*(?:req\.|request\.|params\.|query\.)',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="sql_injection",
            impact="Database compromise through SQL injection.",
            root_cause="User input concatenated directly into SQL query string.",
            suggested_fix="Use prepared statements with placeholders.",
            cwe_id="CWE-89",
            file_extensions=['.js', '.ts', '.jsx', '.tsx']
        ),
        # More flexible SQL patterns
        VulnerabilityPattern(
            id="SQLI005",
            title="SQL Query String Concatenation",
            description="SQL query string built using string concatenation, which can lead to SQL injection.",
            pattern=re.compile(
                r'["\']SELECT\s+.*\s+FROM\s+.*\s+WHERE\s+.*["\'](?:\s*\+|\s*%|\s*\.format)',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            vulnerability_type="sql_injection",
            impact="SQL injection vulnerability allowing data theft or manipulation.",
            root_cause="SQL query string is built using concatenation instead of parameterized queries.",
            suggested_fix="Use parameterized queries or an ORM to prevent SQL injection.",
            cwe_id="CWE-89"
        ),
        VulnerabilityPattern(
            id="SQLI006",
            title="SQL Query with Variable Concatenation",
            description="SQL query appears to concatenate a variable directly into the query string.",
            pattern=re.compile(
                r'(?:query|sql)\s*=\s*["\'](?:SELECT|INSERT|UPDATE|DELETE)\s+[^"\']*["\']?\s*\+\s*\w+',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.MEDIUM,
            vulnerability_type="sql_injection",
            impact="Potential SQL injection if the concatenated variable contains user input.",
            root_cause="Variable directly concatenated into SQL query string.",
            suggested_fix="Use parameterized queries instead of string concatenation.",
            cwe_id="CWE-89"
        ),
    ]
    
    # ==================== COMMAND INJECTION ====================
    COMMAND_INJECTION_PATTERNS: List[VulnerabilityPattern] = [
        VulnerabilityPattern(
            id="CMDI001",
            title="Command Injection - os.system (Python)",
            description="os.system() called with user-controlled input.",
            pattern=re.compile(
                r'os\.system\s*\(\s*(?:f["\']|["\'][^"\']*(?:\%|\{|\+)|[^"\')]+\+)',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="command_injection",
            impact="Remote code execution. Attackers can run arbitrary commands on the server.",
            root_cause="User input passed directly to shell command without sanitization.",
            suggested_fix="Use subprocess module with shell=False and pass arguments as a list: subprocess.run(['ls', '-la', path], shell=False)",
            cwe_id="CWE-78",
            file_extensions=['.py']
        ),
        VulnerabilityPattern(
            id="CMDI002",
            title="Command Injection - subprocess with shell=True",
            description="subprocess called with shell=True and string command.",
            pattern=re.compile(
                r'subprocess\.(?:call|run|Popen|check_output|check_call)\s*\([^)]*shell\s*=\s*True',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.MEDIUM,
            vulnerability_type="command_injection",
            impact="Potential command injection if command includes user input.",
            root_cause="shell=True allows shell metacharacter interpretation.",
            suggested_fix="Use shell=False and pass command as a list: subprocess.run(['cmd', 'arg1'], shell=False)",
            cwe_id="CWE-78",
            file_extensions=['.py']
        ),
        VulnerabilityPattern(
            id="CMDI003",
            title="Command Injection - eval() (Python)",
            description="eval() function used with potentially user-controlled input.",
            pattern=re.compile(
                r'eval\s*\(\s*(?:request\.|input\(|sys\.argv|os\.environ)',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="rce",
            impact="Arbitrary code execution. Complete server compromise possible.",
            root_cause="eval() executes arbitrary Python code from user input.",
            suggested_fix="Never use eval() with user input. Use ast.literal_eval() for parsing literals or implement proper input handling.",
            cwe_id="CWE-94",
            file_extensions=['.py']
        ),
        VulnerabilityPattern(
            id="CMDI004",
            title="Command Injection - exec() (JavaScript/Node.js)",
            description="child_process.exec() used with user input.",
            pattern=re.compile(
                r'(?:exec|execSync|spawn|spawnSync)\s*\(\s*(?:`[^`]*\$\{|["\'][^"\']+["\']\s*\+\s*(?:req\.|request\.|params\.|query\.))',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="command_injection",
            impact="Remote code execution on the server.",
            root_cause="User input passed to shell command.",
            suggested_fix="Use execFile() with arguments as array, or properly escape shell arguments.",
            cwe_id="CWE-78",
            file_extensions=['.js', '.ts']
        ),
        # More flexible patterns for dangerous functions
        VulnerabilityPattern(
            id="CMDI005",
            title="Dangerous Function - os.system() Usage",
            description="os.system() is used which can lead to command injection if input is not properly sanitized.",
            pattern=re.compile(
                r'os\.system\s*\(\s*\w+\s*\)',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.MEDIUM,
            vulnerability_type="command_injection",
            impact="Potential command injection if the argument contains user input.",
            root_cause="os.system() executes shell commands and is vulnerable if input is not sanitized.",
            suggested_fix="Replace with subprocess.run() with shell=False and pass arguments as a list.",
            cwe_id="CWE-78",
            file_extensions=['.py']
        ),
        VulnerabilityPattern(
            id="CMDI006",
            title="Dangerous Function - eval() Usage",
            description="eval() is used which can execute arbitrary code.",
            pattern=re.compile(
                r'\beval\s*\(\s*\w+\s*\)',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.MEDIUM,
            vulnerability_type="rce",
            impact="Arbitrary code execution if the argument contains malicious input.",
            root_cause="eval() executes any Python expression passed to it.",
            suggested_fix="Avoid eval(). Use ast.literal_eval() for safe literal evaluation or implement safer alternatives.",
            cwe_id="CWE-94",
            file_extensions=['.py']
        ),
        VulnerabilityPattern(
            id="CMDI007",
            title="Dangerous Function - exec() Usage (Python)",
            description="exec() is used which can execute arbitrary code.",
            pattern=re.compile(
                r'\bexec\s*\(\s*\w+',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.MEDIUM,
            vulnerability_type="rce",
            impact="Arbitrary code execution if the argument contains malicious input.",
            root_cause="exec() executes any Python code passed to it.",
            suggested_fix="Avoid exec(). Implement safer alternatives for dynamic code execution.",
            cwe_id="CWE-94",
            file_extensions=['.py']
        ),
    ]
    
    # ==================== XSS (Cross-Site Scripting) ====================
    XSS_PATTERNS: List[VulnerabilityPattern] = [
        VulnerabilityPattern(
            id="XSS001",
            title="XSS - innerHTML with user input",
            description="innerHTML property set with potentially user-controlled content.",
            pattern=re.compile(
                r'\.innerHTML\s*=\s*(?:req\.|request\.|params\.|query\.|`[^`]*\$\{)',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            vulnerability_type="xss",
            impact="Session hijacking, cookie theft, defacement, malware distribution.",
            root_cause="User input rendered as HTML without sanitization.",
            suggested_fix="Use textContent instead of innerHTML, or sanitize with DOMPurify.",
            cwe_id="CWE-79",
            file_extensions=['.js', '.ts', '.jsx', '.tsx', '.html']
        ),
        VulnerabilityPattern(
            id="XSS002",
            title="XSS - dangerouslySetInnerHTML (React)",
            description="dangerouslySetInnerHTML used without proper sanitization.",
            pattern=re.compile(
                r'dangerouslySetInnerHTML\s*=\s*\{\s*\{\s*__html\s*:\s*(?!DOMPurify|sanitize)',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.MEDIUM,
            vulnerability_type="xss",
            impact="Cross-site scripting leading to session hijacking.",
            root_cause="React's dangerouslySetInnerHTML bypasses XSS protection.",
            suggested_fix="Sanitize HTML with DOMPurify before using dangerouslySetInnerHTML.",
            cwe_id="CWE-79",
            file_extensions=['.jsx', '.tsx', '.js', '.ts']
        ),
        VulnerabilityPattern(
            id="XSS003",
            title="XSS - document.write with user input",
            description="document.write() called with potentially user-controlled content.",
            pattern=re.compile(
                r'document\.write\s*\(\s*(?:location\.|window\.|`[^`]*\$\{)',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            vulnerability_type="xss",
            impact="DOM-based XSS allowing script injection.",
            root_cause="User-controlled content written directly to document.",
            suggested_fix="Use DOM manipulation methods with proper escaping instead of document.write().",
            cwe_id="CWE-79",
            file_extensions=['.js', '.html']
        ),
    ]
    
    # ==================== INSECURE DESERIALIZATION ====================
    DESERIALIZATION_PATTERNS: List[VulnerabilityPattern] = [
        VulnerabilityPattern(
            id="DESER001",
            title="Insecure Deserialization - pickle (Python)",
            description="pickle.loads() used to deserialize data, potentially from untrusted source.",
            pattern=re.compile(
                r'pickle\.(?:loads?|Unpickler)\s*\(',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.MEDIUM,
            vulnerability_type="insecure_deserialization",
            impact="Remote code execution through crafted pickle payloads.",
            root_cause="pickle can execute arbitrary code during deserialization.",
            suggested_fix="Use JSON for serialization, or cryptographically sign pickle data before deserializing.",
            cwe_id="CWE-502",
            file_extensions=['.py']
        ),
        VulnerabilityPattern(
            id="DESER002",
            title="Insecure Deserialization - yaml.load (Python)",
            description="yaml.load() without safe_load can execute arbitrary code.",
            pattern=re.compile(
                r'yaml\.load\s*\([^)]*\)\s*(?!.*Loader\s*=)',
                re.IGNORECASE
            ),
            severity=Severity.CRITICAL,
            confidence=Confidence.HIGH,
            vulnerability_type="insecure_deserialization",
            impact="Remote code execution through crafted YAML payloads.",
            root_cause="yaml.load() without explicit Loader can construct arbitrary Python objects.",
            suggested_fix="Use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader)",
            cwe_id="CWE-502",
            file_extensions=['.py']
        ),
    ]
    
    # ==================== PATH TRAVERSAL ====================
    PATH_TRAVERSAL_PATTERNS: List[VulnerabilityPattern] = [
        VulnerabilityPattern(
            id="PATH001",
            title="Path Traversal - open() with user input (Python)",
            description="File opened using path that may contain user input.",
            pattern=re.compile(
                r'open\s*\(\s*(?:f["\']|request\.|os\.path\.join\s*\([^)]*request)',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.MEDIUM,
            vulnerability_type="path_traversal",
            impact="Unauthorized file access, reading sensitive files like /etc/passwd.",
            root_cause="User input used in file path without validation.",
            suggested_fix="Use os.path.realpath() and validate that the final path is within expected directory.",
            cwe_id="CWE-22",
            file_extensions=['.py']
        ),
        VulnerabilityPattern(
            id="PATH002",
            title="Path Traversal - fs operations with user input (Node.js)",
            description="File system operations with user-controlled path.",
            pattern=re.compile(
                r'fs\.(?:readFile|writeFile|unlink|readdir|stat)\s*\(\s*(?:req\.|request\.|params\.)',
                re.IGNORECASE
            ),
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            vulnerability_type="path_traversal",
            impact="Unauthorized file access or modification.",
            root_cause="Request parameter used directly in file path.",
            suggested_fix="Use path.resolve() and validate path is within allowed directory.",
            cwe_id="CWE-22",
            file_extensions=['.js', '.ts']
        ),
    ]
    
    # ==================== WEAK CRYPTOGRAPHY ====================
    CRYPTO_PATTERNS: List[VulnerabilityPattern] = [
        VulnerabilityPattern(
            id="CRYPTO001",
            title="Weak Hash Algorithm - MD5",
            description="MD5 is cryptographically broken and should not be used for security.",
            pattern=re.compile(
                r'(?:hashlib\.md5|crypto\.createHash\s*\(\s*["\']md5["\']|MD5\s*\()',
                re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.HIGH,
            vulnerability_type="weak_cryptography",
            impact="Hash collisions possible. Not suitable for passwords or integrity verification.",
            root_cause="MD5 has known vulnerability to collision attacks.",
            suggested_fix="Use SHA-256 or better. For passwords, use bcrypt, scrypt, or Argon2.",
            cwe_id="CWE-328"
        ),
        VulnerabilityPattern(
            id="CRYPTO002",
            title="Weak Hash Algorithm - SHA1",
            description="SHA1 is considered weak for security-critical operations.",
            pattern=re.compile(
                r'(?:hashlib\.sha1|crypto\.createHash\s*\(\s*["\']sha1["\']|SHA1\s*\()',
                re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.HIGH,
            vulnerability_type="weak_cryptography",
            impact="SHA1 is vulnerable to collision attacks and not recommended for security.",
            root_cause="SHA1 has known collision vulnerabilities.",
            suggested_fix="Use SHA-256 or SHA-3 for hash operations.",
            cwe_id="CWE-328"
        ),
        VulnerabilityPattern(
            id="CRYPTO003",
            title="Insecure Random Number Generation",
            description="Using predictable random number generator for security operations.",
            pattern=re.compile(
                r'(?:random\.(random|randint|choice|randrange)|Math\.random\s*\(\))',
                re.IGNORECASE
            ),
            severity=Severity.MEDIUM,
            confidence=Confidence.LOW,
            vulnerability_type="weak_cryptography",
            impact="Predictable values may allow session hijacking or token forgery.",
            root_cause="Standard random is not cryptographically secure.",
            suggested_fix="Use secrets module (Python) or crypto.randomBytes (Node.js) for security-sensitive random values.",
            cwe_id="CWE-338"
        ),
    ]
    
    @classmethod
    def get_all_patterns(cls) -> List[VulnerabilityPattern]:
        """Get all vulnerability patterns."""
        all_patterns = []
        all_patterns.extend(cls.SECRET_PATTERNS)
        all_patterns.extend(cls.SQL_INJECTION_PATTERNS)
        all_patterns.extend(cls.COMMAND_INJECTION_PATTERNS)
        all_patterns.extend(cls.XSS_PATTERNS)
        all_patterns.extend(cls.DESERIALIZATION_PATTERNS)
        all_patterns.extend(cls.PATH_TRAVERSAL_PATTERNS)
        all_patterns.extend(cls.CRYPTO_PATTERNS)
        return all_patterns
    
    @classmethod
    def get_patterns_for_file(cls, filename: str) -> List[VulnerabilityPattern]:
        """Get patterns applicable to a specific file type."""
        import os
        _, ext = os.path.splitext(filename.lower())
        
        applicable = []
        for pattern in cls.get_all_patterns():
            if pattern.file_extensions is None:
                applicable.append(pattern)
            elif ext in pattern.file_extensions:
                applicable.append(pattern)
        
        return applicable
