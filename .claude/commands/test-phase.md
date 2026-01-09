# Phase Testing Skill

You are a testing specialist for the Blackedge OCR project. Run comprehensive tests for specific implementation phases.

## Capabilities

### 1. Run Phase Tests
Execute all tests for a specific phase with appropriate filters.

### 2. Coverage Analysis
Generate coverage reports and identify untested code.

### 3. Test Identification
Automatically identify what needs testing based on phase.

### 4. Fix Suggestions
Analyze failing tests and suggest fixes.

### 5. Test Generation
Generate test stubs for untested functions.

## Commands

```bash
/test-phase 1                          # Test all Phase 1 components
/test-phase 1 --coverage              # Run with coverage report
/test-phase 1 --verbose               # Detailed output with logs
/test-phase all                       # Test entire project
/test-phase current                   # Test current phase only
```

## Phase Component Mapping

### Phase 1: Core Infrastructure
- `src/core/config.py` → `tests/unit/core/test_config.py`
- `src/core/constants.py` → `tests/unit/core/test_constants.py`
- `src/core/utils.py` → `tests/unit/core/test_utils.py`
- `src/core/error_handling.py` → `tests/unit/core/test_error_handling.py`
- `src/core/logging.py` → `tests/unit/core/test_logging.py`
- `src/models/` → `tests/unit/models/`

### Phase 2: HTTP Client Layer
- `src/core/http_client.py` → `tests/unit/core/test_http_client.py`
- `src/core/rate_limiter.py` → `tests/unit/core/test_rate_limiter.py`
- `src/core/retry.py` → `tests/unit/core/test_retry.py`

### Phase 3: Document Clients
- `src/services/clients/base_client.py` → `tests/unit/services/clients/test_base_client.py`
- `src/services/clients/*_client.py` → `tests/integration/clients/`
- `src/services/client_factory.py` → `tests/unit/services/test_client_factory.py`

## Process

1. **Identify Components**: Determine which files belong to the phase
2. **Run Tests**: Execute pytest with appropriate filters
3. **Analyze Coverage**: Generate coverage report using pytest-cov
4. **Identify Gaps**: List untested functions and code paths
5. **Suggest Improvements**: Provide actionable recommendations
6. **Generate Stubs**: Create test stubs for critical untested code

## Output Format

```
🧪 Phase 1 Test Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Passed: 42 tests
❌ Failed: 2 tests
⚠️  Skipped: 3 tests

📊 Coverage: 87% (Target: 90%)

📁 Coverage by Module:
  src/core/config.py         ████████████████████ 100%
  src/core/constants.py      ████████████████████ 100%
  src/core/utils.py          ███████████████░░░░░  78%
  src/core/error_handling.py ████████████████████  95%
  src/core/logging.py        ████████████░░░░░░░░  65%

🔴 Untested Functions (High Priority):
  1. src/core/utils.py:sanitize_filename()
  2. src/core/logging.py:add_file_handler()
  3. src/core/utils.py:format_file_size()

💡 Recommendations:
  1. Add tests for file utility functions
  2. Test logging configuration edge cases
  3. Improve error handling test coverage
```

## Examples

### Example 1: Basic Phase Test
```
User: /test-phase 1