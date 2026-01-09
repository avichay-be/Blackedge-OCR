# GitHub Issues Implementation Plan

## Overview
This document contains the complete plan for creating GitHub issues to track the Blackedge OCR project implementation, broken down into 10 phases.

## Project Context
- **Project**: Blackedge OCR - Michman PDF Extractor
- **Repository**: https://github.com/avichay-be/Blackedge-OCR.git
- **Current State**: Initial project structure created, comprehensive documentation in place
- **Implementation Plan**: 10 phases with detailed tasks in `docs/IMPLEMENTATION_PLAN.md`
- **Architecture**: Documented in `docs/ARCHITECTURE.md`

---

## Approach

### Issue Granularity
**One issue per component (30-40 total issues across all phases)**
- Balanced approach - trackable but not overwhelming
- Each issue represents 1-3 days of work
- Example: "Build Configuration System" combines all config sub-tasks

### Milestones
**Create 10 phase milestones** for clear progress tracking
- One milestone per phase
- Helps with sprint planning and estimations
- Provides completion metrics

### Initial Scope
**Phase 1 only to start**
- Create issues for Phase 1 (Core Infrastructure) first
- Create subsequent phase issues as we progress
- Allows for learning and adaptation based on actual implementation

---

## Prerequisites

### GitHub CLI Authentication (Required First)
```bash
gh auth login
```

Follow prompts to authenticate with GitHub.com

---

## Setup Commands

### Create All Labels (Run Once)

```bash
# Phase labels
gh label create "phase-1" --color "0052CC" --description "Phase 1: Core Infrastructure"
gh label create "phase-2" --color "1976D2" --description "Phase 2: HTTP Client Layer"
gh label create "phase-3" --color "1E88E5" --description "Phase 3: Document Clients"
gh label create "phase-4" --color "42A5F5" --description "Phase 4: Workflow System"
gh label create "phase-5" --color "64B5F6" --description "Phase 5: Validation System"
gh label create "phase-6" --color "90CAF9" --description "Phase 6: API Layer"
gh label create "phase-7" --color "BBDEFB" --description "Phase 7: Security & Error Handling"
gh label create "phase-8" --color "E3F2FD" --description "Phase 8: Logging & Monitoring"
gh label create "phase-9" --color "F3E5F5" --description "Phase 9: Testing"
gh label create "phase-10" --color "FCE4EC" --description "Phase 10: Deployment"

# Type labels
gh label create "infrastructure" --color "7057ff" --description "Infrastructure/setup tasks"
gh label create "feature" --color "008672" --description "New feature implementation"
gh label create "testing" --color "FFA500" --description "Testing related"
gh label create "documentation" --color "0075ca" --description "Documentation"
gh label create "milestone" --color "ededed" --description "Milestone tracking"

# Priority labels
gh label create "priority-high" --color "d73a4a" --description "High priority"
gh label create "priority-medium" --color "fbca04" --description "Medium priority"
gh label create "priority-low" --color "c5def5" --description "Low priority"
```

---

## Phase 1: Core Infrastructure

### Create Milestone

```bash
gh milestone create "Phase 1: Core Infrastructure" \
  --description "Foundation layer: config, models, utils, error handling" \
  --due-date "2026-01-24"
```

### Issue 1: Setup Development Environment

```bash
gh issue create \
  --title "[Phase 1] Setup Development Environment" \
  --label "phase-1,infrastructure,priority-high" \
  --milestone "Phase 1: Core Infrastructure" \
  --body "## Description
Set up the local development environment for the Blackedge OCR project.

## Tasks
- [ ] Clone repository
- [ ] Create virtual environment: \`python -m venv venv\`
- [ ] Activate venv: \`source venv/bin/activate\`
- [ ] Install dependencies: \`pip install -r requirements.txt\`
- [ ] Copy \`.env.example\` to \`.env\`
- [ ] Verify Python 3.9+ installed

## Acceptance Criteria
- All dependencies installed without errors
- Virtual environment active
- \`.env\` file exists with placeholder values
- Can import project packages

## Files
- \`requirements.txt\`
- \`.env.example\`
- \`.env\`"
```

### Issue 2: Build Configuration System

```bash
gh issue create \
  --title "[Phase 1] Build Configuration System (src/core/config.py)" \
  --label "phase-1,feature,priority-high" \
  --milestone "Phase 1: Core Infrastructure" \
  --body "## Description
Create the Pydantic-based configuration system that loads and validates environment variables.

## Requirements
- Use Pydantic Settings for type safety
- Load from .env file
- Validate required fields
- Provide sensible defaults for optional fields

## Implementation
\`\`\`python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    AZURE_API_KEY: str
    MISTRAL_API_URL: str
    OPENAI_API_KEY: str
    GEMINI_API_KEY: str

    # Validation
    ENABLE_CROSS_VALIDATION: bool = False
    VALIDATION_SIMILARITY_THRESHOLD: float = 0.95

    class Config:
        env_file = \".env\"

settings = Settings()
\`\`\`

## Acceptance Criteria
- Settings class loads environment variables
- Required fields raise errors if missing
- Optional fields use defaults
- Can access settings.AZURE_API_KEY, etc.
- Write unit tests in tests/unit/core/test_config.py

## Files
- \`src/core/config.py\` (create)
- \`tests/unit/core/test_config.py\` (create)"
```

### Issue 3: Define Data Models

```bash
gh issue create \
  --title "[Phase 1] Define Data Models (src/models/)" \
  --label "phase-1,feature,priority-high" \
  --milestone "Phase 1: Core Infrastructure" \
  --body "## Description
Create Pydantic data models that define contracts between layers.

## Models to Create

### 1. workflow_models.py
- ExtractedSection: page content with metadata
- WorkflowResult: complete extraction result
- ValidationResult: validation output

### 2. api_models.py
- ExtractionRequest: API request model
- ExtractionResponse: API response model
- HealthResponse: health check response

## Example
\`\`\`python
from pydantic import BaseModel
from typing import Optional, List, Dict

class ExtractedSection(BaseModel):
    page_number: int
    content: str
    metadata: Optional[Dict] = None

class WorkflowResult(BaseModel):
    content: str
    metadata: Dict
    sections: Optional[List[ExtractedSection]] = None
    validation_report: Optional[Dict] = None
\`\`\`

## Acceptance Criteria
- All models defined with proper types
- Models validate input correctly
- Models serialize to JSON
- Unit tests verify validation logic

## Files
- \`src/models/workflow_models.py\` (create)
- \`src/models/api_models.py\` (create)
- \`tests/unit/models/test_workflow_models.py\` (create)
- \`tests/unit/models/test_api_models.py\` (create)"
```

### Issue 4: Build Core Constants

```bash
gh issue create \
  --title "[Phase 1] Build Core Constants (src/core/constants.py)" \
  --label "phase-1,feature,priority-medium" \
  --milestone "Phase 1: Core Infrastructure" \
  --body "## Description
Define application-wide constants used across the codebase.

## Constants to Define
\`\`\`python
# Content formatting
CONTENT_SEPARATOR = \"\\n---PAGE-BREAK---\\n\"
SECTION_SEPARATOR = \"\\n\\n---\\n\\n\"

# Processing
DEFAULT_CHUNK_SIZE = 50  # pages
MAX_CONCURRENT_REQUESTS = 5
REQUEST_TIMEOUT = 120  # seconds

# Workflow keywords
WORKFLOW_KEYWORDS = {
    \"text_extraction\": [\"text extraction\", \"pdfplumber\", \"no ai\"],
    \"azure_di\": [\"azure di\", \"document intelligence\", \"smart tables\"],
    \"ocr_images\": [\"ocr\", \"images\", \"charts\", \"diagrams\"],
    \"gemini\": [\"gemini\", \"google\"],
}

# File limits
MAX_FILE_SIZE_MB = 50
ALLOWED_EXTENSIONS = [\".pdf\"]
\`\`\`

## Acceptance Criteria
- All constants defined and documented
- Constants grouped logically
- Can import and use across modules

## Files
- \`src/core/constants.py\` (create)"
```

### Issue 5: Build Core Utilities

```bash
gh issue create \
  --title "[Phase 1] Build Core Utilities (src/core/utils.py)" \
  --label "phase-1,feature,priority-high" \
  --milestone "Phase 1: Core Infrastructure" \
  --body "## Description
Implement utility functions for PDF processing and file operations.

## Functions to Implement
\`\`\`python
import base64
from pathlib import Path
from PyPDF2 import PdfReader

def encode_pdf_to_base64(pdf_path: str) -> str:
    \"\"\"Convert PDF file to base64 string\"\"\"
    with open(pdf_path, \"rb\") as f:
        return base64.b64encode(f.read()).decode()

def decode_base64_to_pdf(base64_string: str, output_path: str) -> str:
    \"\"\"Decode base64 string and save as PDF\"\"\"
    pdf_bytes = base64.b64decode(base64_string)
    with open(output_path, \"wb\") as f:
        f.write(pdf_bytes)
    return output_path

def get_pdf_page_count(pdf_path: str) -> int:
    \"\"\"Get number of pages in PDF\"\"\"
    reader = PdfReader(pdf_path)
    return len(reader.pages)

def get_file_size_mb(file_path: str) -> float:
    \"\"\"Get file size in megabytes\"\"\"
    size_bytes = Path(file_path).stat().st_size
    return size_bytes / (1024 * 1024)

def validate_pdf_file(file_path: str, max_size_mb: int = 50) -> bool:
    \"\"\"Validate PDF file exists and within size limit\"\"\"
    if not Path(file_path).exists():
        raise FileNotFoundError(f\"PDF not found: {file_path}\")

    size_mb = get_file_size_mb(file_path)
    if size_mb > max_size_mb:
        raise ValueError(f\"PDF too large: {size_mb}MB > {max_size_mb}MB\")

    return True
\`\`\`

## Acceptance Criteria
- All utility functions implemented
- Functions handle errors gracefully
- Unit tests cover all functions
- Tests use sample PDF fixtures

## Files
- \`src/core/utils.py\` (create)
- \`tests/unit/core/test_utils.py\` (create)
- \`tests/fixtures/sample.pdf\` (create test fixture)"
```

### Issue 6: Implement Error Handling Framework

```bash
gh issue create \
  --title "[Phase 1] Implement Error Handling Framework (src/core/error_handling.py)" \
  --label "phase-1,feature,priority-high" \
  --milestone "Phase 1: Core Infrastructure" \
  --body "## Description
Build centralized error handling with custom exceptions and decorators.

## Implementation
\`\`\`python
from functools import wraps
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Exception hierarchy
class ExtractionError(Exception):
    \"\"\"Base exception for extraction errors\"\"\"
    pass

class APIClientError(ExtractionError):
    \"\"\"External API call errors\"\"\"
    pass

class ValidationError(ExtractionError):
    \"\"\"Validation errors\"\"\"
    pass

class ConfigurationError(ExtractionError):
    \"\"\"Configuration/setup errors\"\"\"
    pass

# Error handler decorator
def handle_extraction_errors(context: str):
    \"\"\"Decorator for consistent error handling\"\"\"
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ExtractionError as e:
                logger.error(f\"{context}: {e}\")
                raise HTTPException(status_code=500, detail=str(e))
            except Exception as e:
                logger.exception(f\"{context}: Unexpected error\")
                raise HTTPException(status_code=500, detail=\"Internal server error\")
        return wrapper
    return decorator
\`\`\`

## Acceptance Criteria
- Exception hierarchy defined
- Decorator handles errors consistently
- Errors are logged with context
- Unit tests verify error handling

## Files
- \`src/core/error_handling.py\` (create)
- \`tests/unit/core/test_error_handling.py\` (create)"
```

### Issue 7: Setup Logging Infrastructure

```bash
gh issue create \
  --title "[Phase 1] Setup Logging Infrastructure (src/core/logging.py)" \
  --label "phase-1,infrastructure,priority-medium" \
  --milestone "Phase 1: Core Infrastructure" \
  --body "## Description
Configure structured logging for the application.

## Implementation
\`\`\`python
import logging
import sys
from typing import Any

def setup_logging(log_level: str = \"INFO\") -> None:
    \"\"\"Configure application logging\"\"\"
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/app.log')
        ]
    )

    # Set third-party loggers to WARNING
    logging.getLogger(\"httpx\").setLevel(logging.WARNING)
    logging.getLogger(\"httpcore\").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    \"\"\"Get logger instance\"\"\"
    return logging.getLogger(name)
\`\`\`

## Acceptance Criteria
- Logging configured with proper format
- Log files created in logs/ directory
- Can get logger instances
- Third-party logs filtered

## Files
- \`src/core/logging.py\` (create)
- \`logs/.gitkeep\` (create directory)"
```

### Issue 8: Write Phase 1 Tests

```bash
gh issue create \
  --title "[Phase 1] Write Comprehensive Tests for Core Infrastructure" \
  --label "phase-1,testing,priority-high" \
  --milestone "Phase 1: Core Infrastructure" \
  --body "## Description
Create comprehensive unit tests for all Phase 1 components.

## Test Coverage Required
- \`test_config.py\`: Configuration loading, validation, defaults
- \`test_models.py\`: Model validation, serialization
- \`test_utils.py\`: Utility functions with fixtures
- \`test_error_handling.py\`: Exception handling, decorators

## Test Structure
\`\`\`python
# tests/unit/core/test_config.py
import pytest
from src.core.config import Settings

def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv(\"AZURE_API_KEY\", \"test_key\")
    settings = Settings()
    assert settings.AZURE_API_KEY == \"test_key\"

def test_settings_requires_api_keys():
    with pytest.raises(ValidationError):
        Settings()  # Missing required fields
\`\`\`

## Acceptance Criteria
- All components have unit tests
- Test coverage > 90% for Phase 1 code
- All tests pass
- Tests use fixtures appropriately

## Files
- \`tests/unit/core/test_config.py\`
- \`tests/unit/core/test_utils.py\`
- \`tests/unit/core/test_error_handling.py\`
- \`tests/unit/models/test_workflow_models.py\`
- \`tests/unit/models/test_api_models.py\`
- \`tests/conftest.py\` (pytest configuration)"
```

### Issue 9: Phase 1 Documentation

```bash
gh issue create \
  --title "[Phase 1] Document Core Infrastructure Components" \
  --label "phase-1,documentation,priority-low" \
  --milestone "Phase 1: Core Infrastructure" \
  --body "## Description
Add docstrings and update documentation for Phase 1 components.

## Documentation Requirements
- Add module docstrings to all core files
- Add function docstrings with type hints
- Add usage examples in docstrings
- Update README with Phase 1 completion status

## Example
\`\`\`python
\"\"\"
Core configuration module.

This module provides the Settings class for loading and validating
application configuration from environment variables.

Example:
    from src.core.config import settings

    api_key = settings.AZURE_API_KEY
    timeout = settings.REQUEST_TIMEOUT
\"\"\"
\`\`\`

## Acceptance Criteria
- All public functions documented
- Module-level docstrings present
- Examples provided where helpful
- README updated with Phase 1 status

## Files
- All \`src/core/*.py\` files
- All \`src/models/*.py\` files
- \`README.md\`"
```

### Issue 10: Phase 1 Completion Milestone

```bash
gh issue create \
  --title "Phase 1 Complete: Core Infrastructure Ready" \
  --label "phase-1,milestone" \
  --milestone "Phase 1: Core Infrastructure" \
  --body "## Description
Meta-issue tracking Phase 1 completion.

## Phase 1 Components
- [ ] Development environment setup
- [ ] Configuration system
- [ ] Data models
- [ ] Core constants
- [ ] Core utilities
- [ ] Error handling framework
- [ ] Logging infrastructure
- [ ] Comprehensive tests
- [ ] Documentation

## Success Criteria
- All Phase 1 issues closed
- All core modules importable
- Configuration loads from .env
- Models validate correctly
- Utilities work with sample PDFs
- Error handlers catch and log exceptions
- Test coverage > 90%

## Next Steps
- Proceed to Phase 2: HTTP Client Layer"
```

---

## Summary

This plan creates **10 issues for Phase 1** (9 implementation + 1 milestone tracker):

1. Setup Development Environment
2. Build Configuration System
3. Define Data Models
4. Build Core Constants
5. Build Core Utilities
6. Implement Error Handling Framework
7. Setup Logging Infrastructure
8. Write Comprehensive Tests
9. Document Components
10. Phase 1 Completion Milestone

Each issue includes:
- Clear title and description
- Detailed implementation guidance
- Code examples where applicable
- Specific acceptance criteria
- File paths to create/modify
- Proper labels and milestone assignment

## Next Steps

1. **Authenticate GitHub CLI**: Run `gh auth login`
2. **Create labels**: Run all label creation commands
3. **Create milestone**: Create Phase 1 milestone
4. **Create issues**: Run each issue creation command in sequence
5. **Verify**: Check GitHub repository issues page
6. **Start work**: Begin implementing Phase 1, Issue #1

Once Phase 1 is complete, create Phase 2 issues following the same pattern.
