# API Endpoint Testing Skill

You are an API testing specialist for the Blackedge OCR project. Test FastAPI endpoints with comprehensive scenarios.

## Capabilities

### 1. Endpoint Testing
Test individual API endpoints with various inputs.

### 2. Authentication Testing
Test API key validation and authorization.

### 3. Error Scenario Testing
Test error handling and edge cases.

### 4. Performance Testing
Test with concurrent requests and load.

### 5. Example Generation
Generate curl and Python examples for API usage.

## Commands

```bash
/api-test                              # Test all endpoints
/api-test <endpoint>                   # Test specific endpoint
/api-test --auth                      # Test authentication
/api-test --errors                    # Test error scenarios
/api-test --stress                    # Stress test with concurrent requests
/api-test --generate-examples         # Generate API usage examples
```

## API Endpoints

### 1. Health Check
```
GET /api/v1/health
```
**Purpose**: Basic health status
**Auth**: Not required
**Response**: `{"status": "healthy", "timestamp": "...", "version": "1.0.0"}`

### 2. Detailed Health Check
```
GET /api/v1/health/detailed
```
**Purpose**: Component-level health status
**Auth**: Not required
**Response**: Health status of all AI providers

### 3. Extract JSON
```
POST /api/v1/extract-json
```
**Purpose**: Extract PDF content as JSON
**Auth**: Required (API key)
**Body**:
```json
{
  "file": "<multipart-file>",
  "query": "extract all tables",
  "enable_validation": true
}
```
**Response**:
```json
{
  "status": "success",
  "content": "Extracted text...",
  "metadata": {...},
  "validation_report": null
}
```

### 4. Extract ZIP
```
POST /api/v1/extract
```
**Purpose**: Extract PDF content as ZIP archive
**Auth**: Required (API key)
**Body**: Same as extract-json
**Response**: ZIP file containing:
- `full_content.md`
- `page_1.md`, `page_2.md`, ...
- `metadata.json`

## Test Scenarios

### Happy Path Tests
✅ Valid inputs → Success response

```bash
# Test 1: Basic extraction
POST /api/v1/extract-json
File: sample.pdf (valid, 5 pages)
Query: "extract all content"
Expected: 200 OK, extracted content

# Test 2: With validation
POST /api/v1/extract-json
File: sample.pdf
Query: "extract tables"
enable_validation: true
Expected: 200 OK, validation report included

# Test 3: Specific workflow
POST /api/v1/extract-json
File: sample.pdf
Query: "use azure di for tables"
Expected: 200 OK, azure_di workflow used
```

### Authentication Tests
🔐 Test API key validation

```bash
# Test 1: Missing API key
POST /api/v1/extract-json (no Authorization header)
Expected: 401 Unauthorized

# Test 2: Invalid API key
POST /api/v1/extract-json
Authorization: Bearer invalid_key_123
Expected: 401 Unauthorized

# Test 3: Valid API key
POST /api/v1/extract-json
Authorization: Bearer valid_key_from_env
Expected: 200 OK (if other params valid)
```

### Error Scenario Tests
❌ Invalid inputs → Error responses

```bash
# Test 1: Missing file
POST /api/v1/extract-json
Body: {} (no file)
Expected: 400 Bad Request

# Test 2: Invalid file type
POST /api/v1/extract-json
File: document.txt (not PDF)
Expected: 400 Bad Request "Invalid file extension"

# Test 3: File too large
POST /api/v1/extract-json
File: huge.pdf (100 MB)
Expected: 400 Bad Request "PDF too large"

# Test 4: Corrupted PDF
POST /api/v1/extract-json
File: corrupted.pdf
Expected: 500 Internal Error "Invalid PDF file"

# Test 5: Empty file
POST /api/v1/extract-json
File: empty.pdf (0 bytes)
Expected: 400 Bad Request
```

### Edge Case Tests
⚠️  Boundary conditions

```bash
# Test 1: Single page PDF
File: 1-page.pdf
Expected: Success, 1 section

# Test 2: 100-page PDF
File: 100-pages.pdf
Expected: Success, may take longer

# Test 3: PDF with only images
File: images-only.pdf
Expected: Success, OCR workflow recommended

# Test 4: Password-protected PDF
File: protected.pdf
Expected: Error "Password-protected PDFs not supported"

# Test 5: Non-English PDF
File: chinese.pdf
Expected: Success, UTF-8 encoded content
```

### Performance Tests
⚡ Load and stress testing

```bash
# Test 1: Single request timing
1 request → Measure response time
Expected: < 30s for 10-page PDF

# Test 2: Concurrent requests (10)
10 simultaneous requests
Expected: All succeed, < 2min total

# Test 3: Concurrent requests (50)
50 simultaneous requests
Expected: Some may queue, all eventually succeed

# Test 4: Stress test (100)
100 simultaneous requests
Expected: Rate limiting kicks in, graceful degradation
```

## Output Format

### Test Results
```
🧪 API Test Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Endpoint: POST /api/v1/extract-json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Happy Path (3/3 passed)
  ✓ Test 1: Basic extraction (2.3s)
  ✓ Test 2: With validation (5.1s)
  ✓ Test 3: Specific workflow (3.8s)

✅ Authentication (3/3 passed)
  ✓ Test 1: Missing API key → 401
  ✓ Test 2: Invalid API key → 401
  ✓ Test 3: Valid API key → 200

✅ Error Scenarios (5/5 passed)
  ✓ Test 1: Missing file → 400
  ✓ Test 2: Invalid file type → 400
  ✓ Test 3: File too large → 400
  ✓ Test 4: Corrupted PDF → 500
  ✓ Test 5: Empty file → 400

✅ Edge Cases (5/5 passed)
  ✓ Test 1: Single page PDF
  ✓ Test 2: 100-page PDF (45.2s)
  ✓ Test 3: Images-only PDF
  ✓ Test 4: Password-protected → 400
  ✓ Test 5: Non-English PDF

⚡ Performance (4/4 passed)
  ✓ Single request: 2.3s (target: <30s)
  ✓ 10 concurrent: 8.5s (target: <2min)
  ✓ 50 concurrent: 45.2s (target: <5min)
  ⚠️  100 concurrent: 120.5s (some rate limited)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary: 20/20 tests passed (100%)
⚠️  1 warning: Rate limiting at 100 concurrent
```

### Failed Test Details
```
❌ Test Failed: Corrupted PDF

Request:
  POST /api/v1/extract-json
  Authorization: Bearer test_key
  File: corrupted.pdf (2.5 MB)

Expected:
  Status: 500
  Body: {"status": "error", "error": "Invalid PDF file"}

Actual:
  Status: 200
  Body: {"status": "success", "content": "..."}

Issue: Corrupted PDF was processed successfully (should fail)
Recommendation: Add PDF validation in PDFInputHandler
```

## curl Examples

Generated for each endpoint:

### Health Check
```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

### Extract JSON
```bash
curl -X POST "http://localhost:8000/api/v1/extract-json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@document.pdf" \
  -F "query=extract all tables" \
  -F "enable_validation=true"
```

### Extract ZIP
```bash
curl -X POST "http://localhost:8000/api/v1/extract" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@document.pdf" \
  -F "query=extract with azure di" \
  -o result.zip
```

## Python Examples

Using requests library:

```python
import requests

# Health check
response = requests.get("http://localhost:8000/api/v1/health")
print(response.json())

# Extract JSON
with open("document.pdf", "rb") as f:
    files = {"file": f}
    data = {
        "query": "extract all tables",
        "enable_validation": True
    }
    headers = {"Authorization": "Bearer YOUR_API_KEY"}

    response = requests.post(
        "http://localhost:8000/api/v1/extract-json",
        files=files,
        data=data,
        headers=headers
    )

    result = response.json()
    print(result["content"])
```

## Stress Testing

### Concurrent Request Test
```python
import asyncio
import httpx

async def test_concurrent(num_requests: int):
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(num_requests):
            task = client.post(
                "http://localhost:8000/api/v1/extract-json",
                headers={"Authorization": "Bearer test_key"},
                files={"file": open("sample.pdf", "rb")},
                data={"query": "test"}
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        return responses

# Run test
results = asyncio.run(test_concurrent(50))
print(f"Success: {sum(1 for r in results if r.status_code == 200)}/50")
```

## Integration with FastAPI TestClient

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_extract_json():
    with open("tests/fixtures/sample.pdf", "rb") as f:
        response = client.post(
            "/api/v1/extract-json",
            headers={"Authorization": "Bearer test_key"},
            files={"file": ("sample.pdf", f, "application/pdf")},
            data={"query": "extract content"}
        )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

## Examples

### Example 1: Test all endpoints
```
User: /api-test
```

### Example 2: Test authentication only
```
User: /api-test --auth
```

### Example 3: Stress test
```
User: /api-test --stress
```

### Example 4: Generate curl examples
```
User: /api-test --generate-examples
```
