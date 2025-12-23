# 🔐 Security Scanner

A production-grade, AI-powered security scanner for GitHub repositories. Performs deep analysis of dependencies, source code, configurations, and CI/CD pipelines.

## 🎯 Features

### Scanning Capabilities

| Scanner | Description | Detects |
|---------|-------------|---------|
| **Dependency Scanner** | Checks dependencies against OSV.dev | Known CVEs, outdated packages |
| **Secret Scanner** | Finds hardcoded credentials | API keys, passwords, tokens, private keys |
| **Code Pattern Scanner** | Analyzes source code patterns | SQL injection, XSS, command injection, RCE |
| **Config Scanner** | Checks configuration files | Debug mode, weak secrets, misconfigurations |
| **CI/CD Scanner** | Audits pipeline configs | Script injection, unpinned actions, secrets exposure |

### Supported Languages & Ecosystems

- **Python**: requirements.txt, Pipfile, pyproject.toml
- **JavaScript/Node.js**: package.json, package-lock.json, yarn.lock
- **Go**: go.mod, go.sum
- **Rust**: Cargo.toml, Cargo.lock
- **Ruby**: Gemfile, Gemfile.lock
- **PHP**: composer.json, composer.lock
- **Java**: pom.xml, build.gradle

### Supported CI/CD Platforms

- GitHub Actions
- GitLab CI
- Jenkins
- CircleCI
- Travis CI
- Azure Pipelines

## 📁 Architecture

```
security_scanner/
├── __init__.py
├── apps.py                      # Django app config
├── models.py                    # ScanHistory model
├── views.py                     # API endpoints
├── serializers.py               # DRF serializers
├── urls.py                      # URL routing
├── admin.py                     # Admin interface
├── tests.py                     # Unit tests
│
├── core/                        # Core utilities
│   ├── __init__.py
│   ├── severity.py              # Severity classification (CVSS)
│   ├── result.py                # VulnerabilityResult, ScanResult
│   └── patterns.py              # Vulnerability regex patterns
│
├── engine/                      # Scanning engines
│   ├── __init__.py
│   ├── base_scanner.py          # Abstract base scanner
│   ├── dependency_scanner.py    # OSV.dev integration
│   ├── secret_scanner.py        # Secret detection
│   ├── code_pattern_scanner.py  # Code vulnerability patterns
│   ├── config_scanner.py        # Configuration misconfigurations
│   ├── cicd_scanner.py          # CI/CD pipeline vulnerabilities
│   └── orchestrator.py          # Scanner coordination
│
├── services/                    # External integrations
│   ├── __init__.py
│   ├── github_fetcher.py        # GitHub API integration
│   ├── osv_client.py            # OSV.dev API client
│   └── dependency_parser.py     # Multi-format dependency parsing
│
└── migrations/                  # Database migrations
    └── 0001_initial.py
```

## 🚀 API Endpoints

### Scan Repository

```
POST /api/security/scan/
Content-Type: application/json
Authorization: Required (JWT Cookie)

{
    "repository_url": "https://github.com/owner/repo",
    "include_low_confidence": false,
    "max_files": 500
}
```

**Response:**
```json
{
    "success": true,
    "repository_url": "https://github.com/owner/repo",
    "scan_duration_ms": 5432,
    "files_scanned": 156,
    "total_vulnerabilities": 8,
    "summary": {
        "critical": 2,
        "high": 3,
        "medium": 2,
        "low": 1
    },
    "critical": [...],
    "high": [...],
    "medium": [...],
    "low": [...]
}
```

### Vulnerability Object

```json
{
    "title": "SQL Injection - String Concatenation",
    "description": "SQL query built using string concatenation with user input.",
    "file_path": "src/api/users.py",
    "line": 42,
    "severity": "critical",
    "confidence": "high",
    "vulnerability_type": "sql_injection",
    "impact": "Complete database compromise...",
    "root_cause": "SQL query constructed by concatenating user input...",
    "suggested_fix": "Use parameterized queries...",
    "suggested_version": "",
    "cve_id": "CWE-89",
    "scanner": "code_pattern"
}
```

### Get Scan History

```
GET /api/security/history/
Authorization: Required
```

### Get Scan Details

```
GET /api/security/scan/<id>/
Authorization: Required
```

## 🔧 Configuration

No additional configuration required! The scanner uses:

- **GitHub API**: Uses your existing `GITHUB_PAT` environment variable
- **OSV.dev**: Free API, no key required

## 🧪 Testing

```bash
# Run all security scanner tests
python manage.py test security_scanner

# Run with verbosity
python manage.py test security_scanner --verbosity=2
```

## 📊 Severity Classification

| Level | CVSS Score | Examples |
|-------|------------|----------|
| **Critical** | 9.0-10.0 | RCE, SQL Injection, Hardcoded Secrets |
| **High** | 7.0-8.9 | XSS, Path Traversal, Command Injection |
| **Medium** | 4.0-6.9 | Weak Crypto, Debug Mode, Misconfigurations |
| **Low** | 0.1-3.9 | Info Disclosure, Missing Headers |

## 🛡️ False Positive Reduction

The scanner implements multiple layers of false positive reduction:

1. **Pattern Exclusions**: Known test/example patterns ignored
2. **Context Analysis**: Comments and documentation filtered
3. **Entropy Checking**: Low-entropy "secrets" filtered
4. **Confidence Scoring**: Low-confidence findings can be excluded
5. **Deduplication**: Same issue reported once

## 📝 Adding Custom Patterns

To add new vulnerability patterns, edit `core/patterns.py`:

```python
VulnerabilityPattern(
    id="CUSTOM001",
    title="My Custom Pattern",
    description="Description of the vulnerability",
    pattern=re.compile(r'your_regex_pattern'),
    severity=Severity.HIGH,
    confidence=Confidence.HIGH,
    vulnerability_type="custom_type",
    impact="Impact description",
    root_cause="Why this is vulnerable",
    suggested_fix="How to fix it",
    file_extensions=['.py', '.js'],  # Optional
    cwe_id="CWE-XXX"  # Optional
)
```

## 🔐 Security Notes

- The scanner **does not clone** repositories - it uses GitHub API
- Files are processed **in memory only**
- Maximum file size limit: 1MB per file
- Maximum files per scan: 1000
- All scans are authenticated and logged
