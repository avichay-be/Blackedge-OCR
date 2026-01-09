# System Health Check Skill

You are a system health monitoring specialist for the Blackedge OCR project. Check the health and performance of all system components.

## Capabilities

### 1. Component Health
Check health status of all components (AI providers, internal services).

### 2. Performance Monitoring
Measure response times and throughput.

### 3. Dependency Health
Verify external dependencies are accessible.

### 4. Continuous Monitoring
Run periodic health checks and alert on issues.

### 5. Historical Tracking
Track health metrics over time.

## Commands

```bash
/health-check                          # Check all components
/health-check --providers             # Check only AI providers
/health-check --services              # Check internal services
/health-check --detailed              # Detailed health report
/health-check --monitor               # Continuous monitoring (30s intervals)
```

## Components to Check

### AI Providers
1. **Mistral** (via Azure)
   - Test: Simple completion request
   - Expected latency: < 500ms
   - Rate limit: 60 req/min

2. **OpenAI GPT-4o** (via Azure)
   - Test: Model list request
   - Expected latency: < 1000ms
   - Rate limit: 50 req/min

3. **Google Gemini**
   - Test: Simple generation request
   - Expected latency: < 800ms
   - Rate limit: 60 req/min

4. **Azure Document Intelligence**
   - Test: Account info request
   - Expected latency: < 500ms
   - Rate limit: 30 req/min

### Internal Services
1. **Configuration System**
   - Test: Load settings
   - Check: All required keys present

2. **Logging System**
   - Test: Write to log file
   - Check: Log file exists and writable

3. **Error Handling**
   - Test: Custom exceptions work
   - Check: Decorators function correctly

4. **File System**
   - Test: Create/read/delete temp files
   - Check: Permissions correct

### External Dependencies
1. **Network Connectivity**
   - Test: DNS resolution
   - Check: Internet accessible

2. **File System**
   - Check: Disk space available (> 1GB)
   - Check: logs/ directory writable

## Health Check Process

### 1. Quick Health Check (Default)
```python
# Test each component with simple request
# Return status: 🟢 Healthy | 🟡 Degraded | 🔴 Unhealthy
```

### 2. Detailed Health Check
```python
# Include:
# - Response times
# - Error rates
# - Resource usage
# - Recent failures
```

### 3. Continuous Monitoring
```python
# Run health checks every 30 seconds
# Alert on status changes
# Log all checks
```

## Output Format

### Standard Output
```
🏥 System Health Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Timestamp: 2026-01-09 12:30:00 UTC

AI Providers:
  🟢 Mistral          OK        (150ms)
  🟢 OpenAI           OK        (280ms)
  🟡 Gemini           Slow      (2100ms)
  🔴 Azure DI         Failed    (timeout)

Internal Services:
  🟢 Configuration    OK
  🟢 Logging          OK
  🟢 Error Handling   OK
  🟢 File System      OK

System Resources:
  🟢 Disk Space       15.2 GB free
  🟢 Memory           2.1 GB available
  🟢 Network          Connected

Overall Status: 🟡 DEGRADED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  Issues Detected:
  1. Gemini response time > 2s (threshold: 1s)
  2. Azure DI health check timeout

💡 Recommendations:
  1. Check Azure DI API key and endpoint
  2. Monitor Gemini performance over time
```

### Detailed Output
```
🏥 Detailed Health Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Component: Mistral (via Azure OpenAI)
├─ Status: 🟢 Healthy
├─ Response Time: 150ms (avg: 145ms, p95: 180ms)
├─ Success Rate: 99.8% (last 1000 requests)
├─ Rate Limit: 45/60 req/min
├─ Last Error: None
└─ Endpoint: https://xxx.openai.azure.com/

Component: OpenAI GPT-4o
├─ Status: 🟢 Healthy
├─ Response Time: 280ms (avg: 310ms, p95: 450ms)
├─ Success Rate: 99.5% (last 1000 requests)
├─ Rate Limit: 38/50 req/min
├─ Last Error: 2 hours ago (rate limit)
└─ Endpoint: https://api.openai.com/v1/

Component: Google Gemini
├─ Status: 🟡 Degraded (Slow Response)
├─ Response Time: 2100ms (avg: 1850ms, p95: 2500ms)
├─ Success Rate: 98.2% (last 1000 requests)
├─ Rate Limit: 52/60 req/min
├─ Last Error: 30 minutes ago (timeout)
└─ Endpoint: https://generativelanguage.googleapis.com/

Component: Azure Document Intelligence
├─ Status: 🔴 Unhealthy (Timeout)
├─ Response Time: N/A (timeout after 30s)
├─ Success Rate: 45.2% (last 100 requests)
├─ Rate Limit: Unknown
├─ Last Error: Just now (connection timeout)
└─ Endpoint: https://xxx.cognitiveservices.azure.com/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Health Status Definitions

### 🟢 Healthy
- Response time < threshold
- Success rate > 99%
- No recent errors
- Within rate limits

### 🟡 Degraded
- Response time 1-2x threshold
- Success rate 95-99%
- Occasional errors
- Approaching rate limits

### 🔴 Unhealthy
- Response time > 2x threshold
- Success rate < 95%
- Frequent errors
- Rate limit exceeded

## Alert Rules

### Critical Alerts (🔴)
- Any component completely unavailable
- Success rate < 90%
- All providers failing
- Disk space < 500MB

### Warning Alerts (🟡)
- Response time > 2x normal
- Success rate < 98%
- Single provider degraded
- Disk space < 2GB

### Info (🟢)
- All systems healthy
- Performance within normal range

## Monitoring Mode

When running with `--monitor` flag:

```bash
# Run health check every 30 seconds
# Display status changes
# Log all checks to logs/health-checks.log
# Alert on status changes

🏥 Continuous Health Monitoring
Press Ctrl+C to stop

12:30:00  🟢 All systems healthy
12:30:30  🟢 All systems healthy
12:31:00  🟡 Gemini response time increased (1850ms)
12:31:30  🟡 Gemini still slow (2100ms)
12:32:00  🔴 Azure DI timeout
12:32:30  🔴 Azure DI still unavailable
```

## Integration with Application

The health check can be used:

1. **API Endpoint**: `/api/v1/health`
   ```python
   @router.get("/health")
   async def health_check():
       # Use this skill's logic
       return HealthResponse(status="healthy")
   ```

2. **Startup Checks**: Before starting server
   ```python
   # In main.py
   @app.on_event("startup")
   async def startup_health_check():
       # Run /health-check
       # Log results
       # Warn if any issues
   ```

3. **CI/CD Pipeline**:
   ```yaml
   # In GitHub Actions
   - name: Health Check
     run: claude /health-check --providers
   ```

## Examples

### Example 1: Quick check
```
User: /health-check
```

### Example 2: Check only AI providers
```
User: /health-check --providers
```

### Example 3: Detailed report
```
User: /health-check --detailed
```

### Example 4: Start monitoring
```
User: /health-check --monitor
```
