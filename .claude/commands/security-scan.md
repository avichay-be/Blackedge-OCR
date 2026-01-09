# Security Scanner Skill

You are a security specialist for the Blackedge OCR project. Scan for vulnerabilities and security issues.

## Capabilities

### 1. Secrets Detection
Scan for hardcoded API keys, passwords, and tokens.

### 2. Dependency Vulnerabilities
Check for known vulnerabilities in dependencies.

### 3. Code Security
Identify common security issues (SQL injection, XSS, etc.).

### 4. Configuration Security
Check for insecure configurations.

### 5. Auto-Fix
Automatically fix common security issues.

## Commands

```bash
/security-scan                        # Full security audit
/security-scan --secrets              # Check for exposed secrets
/security-scan --dependencies         # Check dependency vulnerabilities
/security-scan --code                 # Scan code for vulnerabilities
/security-scan --fix                  # Auto-fix issues where possible
```

## Security Checks

### 1. Secrets Detection
Scan for:
- API keys in code
- Passwords in plaintext
- Tokens in version control
- `.env` file in git history

Patterns to detect:
```python
# API Keys
API_KEY = "sk-abc123..."
api_key = "secret_key_123"

# Passwords
password = "MyPassword123"
DB_PASSWORD = "admin123"

# Tokens
AUTH_TOKEN = "Bearer eyJhbGci..."
```

### 2. Dependency Vulnerabilities
Check using:
- `pip-audit` (Python packages)
- `safety check` (known CVEs)
- GitHub Security Advisories

### 3. Code Vulnerabilities

**SQL Injection**:
```python
# ❌ Vulnerable
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ Safe
query = "SELECT * FROM users WHERE id = ?"
```

**Command Injection**:
```python
# ❌ Vulnerable
os.system(f"rm {filename}")

# ✅ Safe
Path(filename).unlink()
```

**Path Traversal**:
```python
# ❌ Vulnerable
open(f"/files/{user_input}")

# ✅ Safe
safe_path = Path("/files") / Path(user_input).name
```

**Insecure File Handling**:
```python
# ❌ Vulnerable
with open(uploaded_file, "wb") as f:
    f.write(data)  # No validation

# ✅ Safe
validate_pdf_file(uploaded_file)
with open(uploaded_file, "wb") as f:
    f.write(data)
```

### 4. Configuration Security
- `.env` in `.gitignore`
- No default/weak API keys
- HTTPS enforced
- CORS properly configured
- Rate limiting enabled

### 5. Authentication/Authorization
- API key validation
- Secure token storage
- Permission checks
- Session management

## Output Format

```
🔒 Security Audit Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scan Date: 2026-01-09 12:30:00 UTC
Project: Blackedge OCR

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Summary:
  Critical:  0 issues
  High:      2 issues
  Medium:    5 issues
  Low:       8 issues
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 HIGH SEVERITY ISSUES

1. [H001] Exposed API Key in Code
   File: tests/test_config.py:15
   Line: api_key = "sk-test-123456"
   Risk: API key exposed in test file
   Impact: Unauthorized API access
   Fix: Use environment variables or test fixtures
   Command: Move to .env or use mock

2. [H002] Weak File Validation
   File: src/services/pdf_input_handler.py:45
   Line: with open(file_path, "wb") as f:
   Risk: No file type validation before opening
   Impact: Arbitrary file execution
   Fix: Validate file extension and content type
   Command: Use validate_pdf_file() before opening

🟡 MEDIUM SEVERITY ISSUES

3. [M001] Missing CORS Configuration
   File: main.py
   Risk: CORS not configured
   Impact: Potential XSS attacks
   Fix: Add CORS middleware with proper origins
   Command: Add CORSMiddleware to FastAPI app

4. [M002] No Rate Limiting
   File: src/api/routes/extraction.py
   Risk: No rate limiting on API endpoints
   Impact: DDoS vulnerability
   Fix: Implement rate limiting middleware
   Command: Add slowapi or custom rate limiter

5. [M003] Dependency Vulnerability: httpx
   Package: httpx==0.25.1
   CVE: CVE-2024-XXXX (hypothetical)
   Risk: Known vulnerability in HTTP client
   Impact: Potential remote code execution
   Fix: Update to httpx>=0.26.0
   Command: pip install --upgrade httpx

🟢 LOW SEVERITY ISSUES

6. [L001] Weak Error Messages
   File: src/core/error_handling.py
   Risk: Error messages expose internal structure
   Impact: Information disclosure
   Fix: Use generic error messages for users
   Recommendation: Log details, show generic message

7. [L002] Missing Security Headers
   File: main.py
   Risk: No security headers configured
   Impact: Various web vulnerabilities
   Fix: Add security headers middleware
   Headers: X-Content-Type-Options, X-Frame-Options, etc.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ PASSED CHECKS

✓ No secrets in git history
✓ .env file in .gitignore
✓ No SQL injection vulnerabilities
✓ No command injection vulnerabilities
✓ Path traversal protections present
✓ Input validation implemented
✓ Secure file handling
✓ API authentication present

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 AUTO-FIX AVAILABLE

The following issues can be automatically fixed:

1. [H001] Move API key to environment variables
2. [M003] Update vulnerable dependencies
3. [M001] Add CORS configuration
4. [L002] Add security headers

Run: /security-scan --fix

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 SECURITY SCORE: 78/100 (Good)

Recommendations:
1. Fix HIGH severity issues immediately
2. Update dependencies monthly
3. Add rate limiting before production
4. Implement security headers
5. Review error handling messages
```

## Auto-Fix Actions

When `--fix` flag is used:

```bash
# 1. Remove hardcoded secrets
Replace API keys with environment variable references

# 2. Update dependencies
pip install --upgrade httpx pydantic fastapi

# 3. Add CORS middleware
Add to main.py:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Add security headers
Add to middleware:
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

## Integration with CI/CD

Add to GitHub Actions:

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install pip-audit safety
      - name: Run security scan
        run: |
          pip-audit
          safety check
      - name: Scan for secrets
        uses: trufflesecurity/trufflehog@main
```

## Examples

### Example 1: Full scan
```
User: /security-scan
```

### Example 2: Check secrets only
```
User: /security-scan --secrets
```

### Example 3: Auto-fix
```
User: /security-scan --fix
```
