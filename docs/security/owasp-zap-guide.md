# OWASP ZAP Security Testing Guide

This guide explains how to use OWASP ZAP (Zed Attack Proxy) to perform security testing on the Decentralized DID API servers.

## Overview

OWASP ZAP is a free, open-source web application security scanner that helps identify vulnerabilities in web applications and APIs. This guide covers:

- Installing and configuring OWASP ZAP
- Running automated scans against API servers
- Interpreting scan results
- Remediation guidelines for common vulnerabilities

## Prerequisites

- OWASP ZAP installed (see Installation section)
- API server running locally or accessible endpoint
- Basic understanding of HTTP and API security concepts

## Installation

### Linux (Debian/Ubuntu)

```bash
# Download OWASP ZAP
wget https://github.com/zaproxy/zaproxy/releases/download/v2.14.0/ZAP_2_14_0_unix.sh

# Make executable
chmod +x ZAP_2_14_0_unix.sh

# Install
./ZAP_2_14_0_unix.sh

# Or use snap
sudo snap install zaproxy --classic
```

### macOS

```bash
# Using Homebrew
brew install --cask owasp-zap

# Or download from https://www.zaproxy.org/download/
```

### Docker

```bash
# Pull the stable image
docker pull ghcr.io/zaproxy/zaproxy:stable

# Run ZAP in daemon mode
docker run -u zap -p 8080:8080 -i ghcr.io/zaproxy/zaproxy:stable zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true
```

## Configuration for API Testing

### 1. Start Your API Server

```bash
# Start the API server
cd /workspaces/decentralized-did
python -m uvicorn src.decentralized_did.api.server:app --host 0.0.0.0 --port 8000

# Verify it's running
curl http://localhost:8000/health
```

### 2. Configure ZAP API Context

Create a ZAP context file (`api-context.context`) for your API:

```xml
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<configuration>
    <context>
        <name>DID API</name>
        <desc>Decentralized DID API Security Testing</desc>
        <inscope>true</inscope>
        <incregexes>http://localhost:8000/.*</incregexes>
        <tech>
            <include>Language.Python</include>
            <include>OS</include>
            <include>Db</include>
        </tech>
        <urlparser>
            <class>org.zaproxy.zap.model.StandardParameterParser</class>
            <config>{}
            </config>
        </urlparser>
        <authentication>
            <type>0</type>
        </authentication>
    </context>
</configuration>
```

### 3. Configure Authentication (if using API keys)

For API servers with authentication:

```bash
# In ZAP, set authentication header
# Tools -> Options -> Authentication -> Header Based Authentication
# Header: X-API-Key
# Value: your-api-key-here
```

## Running Automated Scans

### Quick Scan (5-10 minutes)

```bash
# Using ZAP API
curl "http://localhost:8080/JSON/ascan/action/scan/?url=http://localhost:8000&recurse=true&inScopeOnly=false&scanPolicyName=Default%20Policy&method=&postData=&contextId="

# Get scan status
curl "http://localhost:8080/JSON/ascan/view/status/?scanId=0"

# Get results when complete
curl "http://localhost:8080/JSON/core/view/alerts/?baseurl=http://localhost:8000" > zap-results.json
```

### Full Scan (30-60 minutes)

```bash
# Using ZAP CLI (install: pip install zaproxy)
zap-cli quick-scan --self-contained --start-options '-config api.disablekey=true' http://localhost:8000

# Or using Docker
docker run -v $(pwd):/zap/wrk/:rw -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
    -t http://host.docker.internal:8000 \
    -g gen.conf \
    -r zap-report.html
```

### API-Specific Scan with OpenAPI Definition

If you have an OpenAPI specification:

```bash
# Generate OpenAPI spec from FastAPI
python -c "
from src.decentralized_did.api.server import app
import json
with open('openapi.json', 'w') as f:
    json.dump(app.openapi(), f, indent=2)
"

# Import into ZAP and scan
zap-cli open-url http://localhost:8080
zap-cli import-openapi openapi.json http://localhost:8000
zap-cli active-scan -r http://localhost:8000
```

## Interpreting Scan Results

### Alert Risk Levels

ZAP categorizes vulnerabilities by risk:

- **High Risk**: Critical security issues requiring immediate attention
  - SQL Injection
  - Cross-Site Scripting (XSS)
  - Remote Code Execution
  - Authentication Bypass

- **Medium Risk**: Significant security concerns
  - CSRF vulnerabilities
  - Insecure session management
  - Information disclosure
  - Missing security headers

- **Low Risk**: Best practice violations
  - Missing Content-Type headers
  - Insecure cookies (missing HttpOnly/Secure)
  - Weak password policy

- **Informational**: Non-security findings
  - Server version disclosure
  - Debug information exposure

### Common Findings and Expected Results

For the DID API servers with security hardening in place, you should see:

✅ **Expected PASS**:
- Authentication required (401 on protected endpoints)
- Rate limiting enforced (429 Too Many Requests)
- Security headers present (HSTS, CSP, X-Frame-Options, etc.)
- No SQL injection vulnerabilities (no SQL database)
- No XSS vulnerabilities (API returns JSON, not HTML)
- Input validation working (400 Bad Request on invalid input)

⚠️ **Expected INFORMATIONAL**:
- Server header disclosure (FastAPI version)
- API version information in responses

❌ **Unexpected FAILURES** (should NOT appear):
- Missing authentication on protected endpoints
- Missing rate limiting
- Missing security headers
- Information disclosure (stack traces in production)
- Unvalidated input accepted

## Remediation Guidelines

### High Risk Findings

If you see high-risk findings:

1. **SQL Injection**
   - Verify input validation is working
   - Check parameterized queries (not applicable for this API - no SQL database)
   - Review error messages for information disclosure

2. **Authentication Bypass**
   - Verify authentication middleware is configured
   - Check JWT token validation
   - Review API key validation logic

3. **Remote Code Execution**
   - Review file upload handling (not applicable for this API)
   - Check deserialization of user input
   - Verify command injection protection

### Medium Risk Findings

1. **Missing Security Headers**
   - Already implemented in Phase 4 - verify headers are present:
     ```python
     # Check headers
     curl -I http://localhost:8000/health
     # Should include:
     # Strict-Transport-Security: max-age=31536000; includeSubDomains
     # X-Content-Type-Options: nosniff
     # X-Frame-Options: DENY
     # X-XSS-Protection: 1; mode=block
     # Content-Security-Policy: default-src 'self'
     ```

2. **Information Disclosure**
   - Verify error handling returns generic messages in production
   - Check that stack traces are disabled in production mode
   - Review audit logs don't contain sensitive data

### Low Risk Findings

1. **Insecure Cookies**
   - Set `secure=True` and `httponly=True` on session cookies
   - Use `samesite='strict'` to prevent CSRF

2. **Missing Rate Limiting**
   - Already implemented in Phase 1 - verify limits are enforced
   - Check rate limit headers are present (X-RateLimit-*)

## Automated Scan Scripts

### Baseline Scan Script

Create `scripts/security/zap-baseline-scan.sh`:

```bash
#!/bin/bash
set -e

API_URL="${API_URL:-http://localhost:8000}"
ZAP_PORT="${ZAP_PORT:-8080}"
REPORT_DIR="./security-reports"

echo "Starting OWASP ZAP baseline scan..."
echo "Target: $API_URL"

# Create report directory
mkdir -p "$REPORT_DIR"

# Start ZAP in daemon mode
docker run -d --name zap-daemon \
    -u zap \
    -p "$ZAP_PORT:$ZAP_PORT" \
    ghcr.io/zaproxy/zaproxy:stable \
    zap.sh -daemon -host 0.0.0.0 -port "$ZAP_PORT" \
    -config api.addrs.addr.name=.* \
    -config api.addrs.addr.regex=true

# Wait for ZAP to start
echo "Waiting for ZAP to start..."
sleep 10

# Run baseline scan
docker run --rm \
    -v "$(pwd):/zap/wrk/:rw" \
    --network host \
    ghcr.io/zaproxy/zaproxy:stable \
    zap-baseline.py \
    -t "$API_URL" \
    -g gen.conf \
    -r "$REPORT_DIR/zap-baseline-report.html" \
    -J "$REPORT_DIR/zap-baseline-report.json"

# Stop ZAP daemon
docker stop zap-daemon
docker rm zap-daemon

echo "Scan complete! Reports saved to $REPORT_DIR/"
```

Make it executable:

```bash
chmod +x scripts/security/zap-baseline-scan.sh
```

### CI/CD Integration

Add to `.github/workflows/security-scan.yml`:

```yaml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Mondays at 2 AM

jobs:
  zap-scan:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -e ".[api]"

    - name: Start API server
      run: |
        uvicorn src.decentralized_did.api.server:app --host 0.0.0.0 --port 8000 &
        sleep 5

    - name: Run ZAP Baseline Scan
      uses: zaproxy/action-baseline@v0.11.0
      with:
        target: 'http://localhost:8000'
        rules_file_name: '.zap/rules.tsv'
        cmd_options: '-a'

    - name: Upload ZAP Report
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: zap-report
        path: report_html.html
```

## Best Practices

1. **Regular Scans**: Run security scans weekly or after major changes
2. **Baseline Reports**: Establish a baseline and track improvements
3. **False Positives**: Review and document false positives in `.zap/rules.tsv`
4. **Test Environments**: Test on staging before production
5. **Scope Control**: Configure context to avoid scanning external services
6. **Rate Limiting**: Be aware ZAP scans can trigger rate limits
7. **Authentication**: Configure proper authentication for protected endpoints

## Troubleshooting

### ZAP Can't Connect to API

```bash
# Check API is running
curl http://localhost:8000/health

# Check firewall rules
sudo ufw status

# Try host.docker.internal (if using Docker)
docker run --rm ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t http://host.docker.internal:8000
```

### Scan Times Out

```bash
# Increase timeout in ZAP options
# Tools -> Options -> Connection -> Timeout: 120 seconds

# Or reduce scan depth
zap-cli active-scan --recurse=false http://localhost:8000
```

### False Positives

Create `.zap/rules.tsv` to suppress known false positives:

```tsv
10021	IGNORE	http://localhost:8000/api/v1/did/generate
10202	IGNORE	http://localhost:8000/health
```

## References

- [OWASP ZAP Documentation](https://www.zaproxy.org/docs/)
- [ZAP API Documentation](https://www.zaproxy.org/docs/api/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [ZAP Docker Guide](https://www.zaproxy.org/docs/docker/)

## Next Steps

After running OWASP ZAP scans:

1. Review all findings and prioritize by risk level
2. Implement fixes for high/medium risk findings
3. Document false positives and expected findings
4. Set up automated scanning in CI/CD pipeline
5. Proceed to [Load Testing Guide](./load-testing-guide.md)
6. Run [Performance Benchmarking](./performance-benchmarking.md)
7. Complete [Security Testing Checklist](./security-testing-checklist.md)
