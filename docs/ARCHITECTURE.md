# Building Michman PDF Extractor from Scratch

A comprehensive guide to understanding and recreating the PDF extraction system's architecture.

---

## Table of Contents

1. [Architecture Philosophy](#architecture-philosophy)
2. [System Overview](#system-overview)
3. [Building Blocks - Implementation Order](#building-blocks---implementation-order)
4. [Core Architecture Patterns](#core-architecture-patterns)
5. [Layer-by-Layer Construction](#layer-by-layer-construction)
6. [Integration Points](#integration-points)
7. [Scaling Considerations](#scaling-considerations)

---

## Architecture Philosophy

### Core Principles

**1. Clean Architecture**
- Separation of concerns: API → Business Logic → External Services
- Inner layers don't depend on outer layers
- Business logic is independent of frameworks and external APIs

**2. Open/Closed Principle**
- Open for extension (add new workflows without modifying existing code)
- Closed for modification (existing workflows remain untouched)

**3. Dependency Inversion**
- High-level modules depend on abstractions, not concrete implementations
- Strategy Pattern for workflows, Factory Pattern for clients

**4. Single Responsibility**
- Each module has one reason to change
- PDFInputHandler: file operations only
- WorkflowRouter: routing logic only
- ResponseBuilder: response formatting only

### Why This Architecture?

**Problem**: Multiple AI providers (Mistral, OpenAI, Gemini, Azure) with different extraction strategies

**Solution**:
- Abstract the concept of a "workflow" (Strategy Pattern)
- Abstract the concept of a "document client" (Factory Pattern)
- Make both independently extensible

**Benefits**:
- Add new AI providers without touching existing code
- Add new extraction strategies without modifying API layer
- Test components in isolation
- Scale different parts independently

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│  (FastAPI routes, request/response handling)                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                   Input Processing Layer                     │
│  (PDFInputHandler: file upload, decode, cleanup)             │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                  Orchestration Layer                         │
│  ┌──────────────┐  ┌────────────────────┐                   │
│  │WorkflowRouter│─▶│WorkflowOrchestrator│                   │
│  └──────────────┘  └─────────┬──────────┘                   │
│                              │                               │
│  ┌───────────────────────────▼────────────────────────┐     │
│  │           Workflow Handlers (Strategy)             │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐          │     │
│  │  │Default   │ │AzureDI   │ │Gemini    │ ...      │     │
│  │  │Handler   │ │Handler   │ │Handler   │          │     │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘          │     │
│  └───────┼────────────┼────────────┼─────────────────┘     │
└──────────┼────────────┼────────────┼───────────────────────┘
           │            │            │
┌──────────▼────────────▼────────────▼───────────────────────┐
│                  Service Layer                               │
│  ┌─────────────────────────────────────────────────┐        │
│  │        Client Factory (Lazy Singleton)          │        │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │        │
│  │  │Mistral   │ │OpenAI    │ │Gemini    │ ...    │        │
│  │  │Client    │ │Client    │ │Client    │        │        │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘        │        │
│  └───────┼────────────┼────────────┼──────────────┘        │
│          │            │            │                        │
│  ┌───────▼────────────▼────────────▼──────────────┐        │
│  │         Validation Service (Optional)          │        │
│  │  ┌──────────────┐ ┌───────────────────┐       │        │
│  │  │ProblemDetector│ │SimilarityCalculator│       │        │
│  │  └──────────────┘ └───────────────────┘       │        │
│  └─────────────────────────────────────────────────┘        │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                  Output Processing Layer                      │
│  (ResponseBuilder: ZIP, JSON, single file formatting)         │
└───────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. HTTP Request → FastAPI Route
2. File Upload → PDFInputHandler (save to temp file)
3. Query Analysis → WorkflowRouter (determine strategy)
4. Workflow Execution → WorkflowOrchestrator (delegate to handler)
5. AI Processing → Document Client (API call)
6. Quality Check → ValidationService (optional)
7. Response Format → ResponseBuilder (ZIP/JSON)
8. Cleanup → PDFInputHandler (delete temp files)
9. HTTP Response → Client
```

---

## Building Blocks - Implementation Order

### Phase 1: Foundation (Core Infrastructure)

**Order matters**: Build from the inside out

#### 1.1 Configuration System
**File**: `src/core/config.py`

**Why First?**: Every other component depends on configuration

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    AZURE_API_KEY: str
    MISTRAL_API_URL: str

    # Validation
    ENABLE_CROSS_VALIDATION: bool = False
    VALIDATION_SIMILARITY_THRESHOLD: float = 0.95

    class Config:
        env_file = ".env"

settings = Settings()
```

**Key Decisions**:
- Use Pydantic for type safety and validation
- Load from .env for security (never commit secrets)
- Provide sensible defaults

#### 1.2 Data Models
**Files**: `src/models/*.py`

**Why Second?**: Defines contracts between layers

```python
# src/models/workflow_models.py
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
```

**Key Decisions**:
- Pydantic models for validation and serialization
- Immutable data structures (easier to reason about)
- Optional fields for flexibility

#### 1.3 Constants and Utilities
**Files**: `src/core/constants.py`, `src/core/utils.py`

**Why Third?**: Shared by multiple layers

```python
# src/core/constants.py
CONTENT_SEPARATOR = "\n---PAGE-BREAK---\n"
DEFAULT_CHUNK_SIZE = 50  # pages

# src/core/utils.py
def encode_pdf_to_base64(pdf_path: str) -> str:
    """Convert PDF file to base64 string"""
    with open(pdf_path, "rb") as f:
        return base64.b64encode(f.read()).decode()
```

#### 1.4 Error Handling
**File**: `src/core/error_handling.py`

**Why Fourth?**: Centralized error handling for consistency

```python
class ExtractionError(Exception):
    """Base exception for extraction errors"""
    pass

class APIClientError(ExtractionError):
    """External API errors"""
    pass

def handle_extraction_errors(context: str):
    """Decorator for consistent error responses"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ExtractionError as e:
                logger.error(f"{context}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        return wrapper
    return decorator
```

**Key Decisions**:
- Custom exception hierarchy for granular error handling
- Decorator pattern for DRY (Don't Repeat Yourself)
- Structured logging

#### 1.5 HTTP Client
**File**: `src/core/http_client.py`

**Why Fifth?**: Shared by all API clients

```python
import httpx
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_managed_client(timeout: float = 60.0):
    """Context manager for HTTP client lifecycle"""
    limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        yield client
```

**Key Decisions**:
- Async HTTP client (httpx) for concurrency
- Connection pooling for performance
- Context manager for automatic cleanup

---

### Phase 2: Client Abstraction

#### 2.1 Base Client Interface
**File**: `src/services/clients/base_client.py`

**Why First in Phase 2?**: Defines contract for all AI clients

```python
from abc import ABC, abstractmethod

class BaseDocumentClient(ABC):
    """Abstract base class for document processing clients"""

    def __init__(self, timeout: float = 60.0):
        self.timeout = timeout
        self._validate_credentials()

    @abstractmethod
    def _validate_credentials(self):
        """Validate API keys/credentials"""
        pass

    @abstractmethod
    async def extract_page_content(self, pdf_bytes: bytes, page_number: int) -> str:
        """Extract content from single PDF page"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if API is accessible"""
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @abstractmethod
    async def close(self):
        """Cleanup resources"""
        pass
```

**Key Decisions**:
- Abstract base class enforces interface
- Async context manager for resource management
- Health check for monitoring
- Template method pattern (common structure, specific implementation)

#### 2.2 Concrete Clients
**Files**: `src/services/mistral_client.py`, `src/services/openai_client.py`, etc.

**Implementation Order**: Start with simplest (Mistral), then add complexity

```python
# src/services/mistral_client.py
class MistralDocumentClient(BaseDocumentClient):
    def __init__(self, api_key: str = None, api_url: str = None):
        self.api_key = api_key or settings.AZURE_API_KEY
        self.api_url = api_url or settings.MISTRAL_API_URL
        super().__init__(timeout=120.0)
        self._client = None

    async def __aenter__(self):
        self._client = get_async_client(timeout=self.timeout)
        return self

    async def close(self):
        if self._client:
            await self._client.aclose()

    def _validate_credentials(self):
        if not self.api_key or not self.api_url:
            raise ValueError("Mistral credentials missing")

    async def extract_page_content(self, pdf_bytes: bytes, page_number: int) -> str:
        # Implementation specific to Mistral API
        pass

    async def health_check(self) -> bool:
        try:
            # Ping Mistral API
            return True
        except Exception:
            return False
```

#### 2.3 Client Factory
**File**: `src/services/client_factory.py`

**Why After Clients?**: Manages lifecycle of all clients

```python
class ClientFactory:
    """Singleton factory for lazy client initialization"""

    def __init__(self):
        self._mistral_client = None
        self._openai_client = None
        self._gemini_client = None
        self._azure_di_client = None

    @property
    def mistral_client(self):
        """Lazy initialization - only created when first accessed"""
        if self._mistral_client is None:
            self._mistral_client = MistralDocumentClient()
        return self._mistral_client

    @property
    def openai_client(self):
        if self._openai_client is None:
            self._openai_client = OpenAIDocumentClient()
        return self._openai_client

    # ... other clients

_client_factory_instance = None

def get_client_factory() -> ClientFactory:
    """Singleton pattern"""
    global _client_factory_instance
    if _client_factory_instance is None:
        _client_factory_instance = ClientFactory()
    return _client_factory_instance
```

**Key Decisions**:
- Singleton pattern (one factory instance)
- Lazy initialization (clients created on-demand)
- Property pattern for clean access

---

### Phase 3: Workflow System

#### 3.1 Workflow Types
**File**: `src/workflows/workflow_types.py`

**Why First?**: Defines available strategies

```python
from enum import Enum

class WorkflowType(Enum):
    """Available extraction workflows"""
    MISTRAL = "mistral"
    TEXT_EXTRACTION = "text_extraction"
    AZURE_DOCUMENT_INTELLIGENCE = "azure_di"
    OCR_WITH_IMAGES = "ocr_images"
    GEMINI_WF = "gemini"
```

#### 3.2 Base Handler Interface
**File**: `src/services/workflows/base_handler.py`

**Why Second?**: Defines contract for all handlers

```python
from abc import ABC, abstractmethod
from src.models.workflow_models import WorkflowResult

class BaseWorkflowHandler(ABC):
    """Abstract base class for workflow handlers"""

    @abstractmethod
    async def execute(
        self,
        pdf_path: str,
        query: str,
        enable_validation: bool = None
    ) -> WorkflowResult:
        """
        Execute the workflow

        Args:
            pdf_path: Path to PDF file
            query: User query for context
            enable_validation: Override global validation setting

        Returns:
            WorkflowResult with extracted content
        """
        pass
```

**Key Decisions**:
- Strategy pattern (interchangeable algorithms)
- Common interface for all workflows
- Consistent return type

#### 3.3 Concrete Handlers
**Files**: `src/services/workflows/*_handler.py`

**Implementation Order**: Simplest to most complex

1. **TextExtractionHandler**: No AI, just pdfplumber
2. **DefaultHandler**: Single client (Mistral)
3. **AzureDIHandler**: Single client with post-processing
4. **OcrImagesHandler**: Multiple clients (Mistral + OpenAI)
5. **GeminiHandler**: Parallel page processing

```python
# src/services/workflows/default_handler.py
class DefaultHandler(BaseWorkflowHandler):
    async def execute(self, pdf_path: str, query: str, enable_validation=None) -> WorkflowResult:
        # 1. Get client from factory
        client_factory = get_client_factory()
        mistral_client = client_factory.mistral_client

        # 2. Process document
        content, metadata = await mistral_client.process_document(pdf_path)

        # 3. Optional validation
        if enable_validation:
            validation_service = ValidationService(
                openai_client=client_factory.openai_client
            )
            validated = await validation_service.validate(content, pdf_path)
            content = validated.content
            validation_report = validated.report

        # 4. Return result
        return WorkflowResult(
            content=content,
            metadata={"workflow": "mistral", **metadata},
            validation_report=validation_report if enable_validation else None
        )
```

#### 3.4 Workflow Router
**File**: `src/services/workflow_router.py`

**Why After Handlers?**: Maps queries to handlers

```python
def get_workflow_type(query: str) -> WorkflowType:
    """
    Determine workflow based on query keywords

    Priority order:
    1. TEXT_EXTRACTION (no AI)
    2. AZURE_DOCUMENT_INTELLIGENCE (smart tables)
    3. OCR_WITH_IMAGES (charts/diagrams)
    4. GEMINI_WF (Gemini specific)
    5. MISTRAL (default)
    """
    query_lower = query.lower()

    if any(kw in query_lower for kw in ["text extraction", "pdfplumber", "no ai"]):
        return WorkflowType.TEXT_EXTRACTION

    if any(kw in query_lower for kw in ["azure di", "document intelligence", "smart tables"]):
        return WorkflowType.AZURE_DOCUMENT_INTELLIGENCE

    if any(kw in query_lower for kw in ["ocr", "images", "charts", "diagrams"]):
        return WorkflowType.OCR_WITH_IMAGES

    if any(kw in query_lower for kw in ["gemini", "google"]):
        return WorkflowType.GEMINI_WF

    return WorkflowType.MISTRAL  # default
```

**Key Decisions**:
- Keyword-based routing (simple, transparent)
- Priority order (most specific to least specific)
- Default fallback

#### 3.5 Workflow Orchestrator
**File**: `src/services/workflow_orchestrator.py`

**Why Last?**: Coordinates router and handlers

```python
class WorkflowOrchestrator:
    """Coordinates workflow execution"""

    def __init__(self):
        self.workflow_handlers = {
            WorkflowType.MISTRAL: DefaultHandler(),
            WorkflowType.TEXT_EXTRACTION: TextExtractionHandler(),
            WorkflowType.AZURE_DOCUMENT_INTELLIGENCE: AzureDIHandler(),
            WorkflowType.OCR_WITH_IMAGES: OcrImagesHandler(),
            WorkflowType.GEMINI_WF: GeminiHandler(),
        }

    async def execute_workflow(
        self,
        pdf_path: str,
        query: str = "",
        enable_validation: bool = None,
        workflow_type: WorkflowType = None
    ) -> WorkflowResult:
        """Execute appropriate workflow"""

        # 1. Determine workflow
        if workflow_type is None:
            workflow_type = get_workflow_type(query)

        # 2. Get handler
        handler = self.workflow_handlers.get(workflow_type)
        if not handler:
            raise ValueError(f"Unknown workflow: {workflow_type}")

        # 3. Execute
        logger.info(f"Executing workflow: {workflow_type}")
        result = await handler.execute(pdf_path, query, enable_validation)

        return result

_orchestrator_instance = None

def get_workflow_orchestrator() -> WorkflowOrchestrator:
    """Singleton pattern"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = WorkflowOrchestrator()
    return _orchestrator_instance
```

**Key Decisions**:
- Singleton pattern (one orchestrator instance)
- Handler registry (extensible without modification)
- Centralized logging

---

### Phase 4: Validation System (Optional)

#### 4.1 Content Normalizer
**File**: `src/services/validation/content_normalizer.py`

**Why First?**: Preprocessing for comparison

```python
class ContentNormalizer:
    """Normalize text for comparison"""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Basic normalization"""
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)  # collapse whitespace
        return text.strip()

    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """Extract all numbers from text"""
        pattern = r'-?\d+(?:,\d{3})*(?:\.\d+)?'
        numbers = re.findall(pattern, text)
        return [float(n.replace(',', '')) for n in numbers]
```

#### 4.2 Problem Detector
**File**: `src/services/validation/problem_detector.py`

**Why Second?**: Identifies quality issues

```python
class ProblemDetector:
    """Detect extraction quality problems"""

    async def detect_problems_batch(
        self,
        sections: List[ExtractedSection]
    ) -> Dict[int, List[str]]:
        """Detect problems in parallel for all sections"""
        tasks = [
            self._detect_problems_for_section(section)
            for section in sections
        ]
        results = await asyncio.gather(*tasks)

        return {
            section.page_number: problems
            for section, problems in zip(sections, results)
            if problems
        }

    async def _detect_problems_for_section(
        self,
        section: ExtractedSection
    ) -> List[str]:
        """Detect problems for single section"""
        problems = []
        content = section.content

        # Check 1: Empty or too short
        if len(content.strip()) < 100:
            problems.append("low_content_density")

        # Check 2: Missing numbers in tables
        if "| " in content and not re.search(r'\d', content):
            problems.append("missing_numbers")

        # Check 3: Repeated characters
        if re.search(r'(.)\1{10,}', content):
            problems.append("repeated_characters")

        # ... 10 more checks

        return problems
```

#### 4.3 Similarity Calculator
**File**: `src/services/validation/similarity_calculator.py`

**Why Third?**: Compares two extractions

```python
class SimilarityCalculator:
    """Calculate similarity between two texts"""

    def calculate_similarity(
        self,
        text1: str,
        text2: str,
        method: str = "number_frequency"
    ) -> float:
        """Calculate similarity score (0.0 to 1.0)"""

        if method == "number_frequency":
            return self._number_frequency_similarity(text1, text2)
        elif method == "levenshtein":
            return self._levenshtein_similarity(text1, text2)
        else:
            raise ValueError(f"Unknown method: {method}")

    def _number_frequency_similarity(self, text1: str, text2: str) -> float:
        """Compare based on number frequencies"""
        normalizer = ContentNormalizer()

        numbers1 = normalizer.extract_numbers(text1)
        numbers2 = normalizer.extract_numbers(text2)

        if not numbers1 and not numbers2:
            return 1.0  # both empty

        if not numbers1 or not numbers2:
            return 0.0  # one empty

        # Calculate frequency distributions
        freq1 = Counter(numbers1)
        freq2 = Counter(numbers2)

        # Cosine similarity
        all_numbers = set(freq1.keys()) | set(freq2.keys())
        vec1 = [freq1.get(n, 0) for n in all_numbers]
        vec2 = [freq2.get(n, 0) for n in all_numbers]

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        return dot_product / (magnitude1 * magnitude2) if magnitude1 * magnitude2 > 0 else 0.0
```

#### 4.4 Validation Orchestrator
**File**: `src/services/validation/validation_orchestrator.py`

**Why Last?**: Coordinates validation pipeline

```python
class ValidationService:
    """Orchestrate validation process"""

    def __init__(self, openai_client, gemini_client=None):
        self.openai_client = openai_client
        self.gemini_client = gemini_client
        self.problem_detector = ProblemDetector()
        self.similarity_calculator = SimilarityCalculator()
        self.normalizer = ContentNormalizer()

    async def validate(
        self,
        primary_content: str,
        pdf_path: str,
        sections: List[ExtractedSection] = None
    ) -> ValidationResult:
        """
        Validate extraction quality

        Process:
        1. Detect problems in primary extraction
        2. If problems → use secondary extraction
        3. Else → compare similarity
        4. If similarity low → use secondary extraction
        """

        # Step 1: Detect problems
        if sections:
            problems = await self.problem_detector.detect_problems_batch(sections)
            problem_pages = list(problems.keys())
        else:
            problems = {}
            problem_pages = []

        # Step 2: If problems, use secondary extraction
        if problem_pages:
            logger.info(f"Problems detected on {len(problem_pages)} pages")
            secondary_content = await self._extract_with_openai(pdf_path)

            return ValidationResult(
                content=secondary_content,
                used_secondary=True,
                report={
                    "problems": problems,
                    "reason": "quality_issues"
                }
            )

        # Step 3: Calculate similarity
        secondary_content = await self._extract_with_openai(pdf_path)
        similarity = self.similarity_calculator.calculate_similarity(
            primary_content,
            secondary_content,
            method=settings.VALIDATION_SIMILARITY_METHOD
        )

        logger.info(f"Similarity score: {similarity:.2f}")

        # Step 4: Use secondary if similarity low
        if similarity < settings.VALIDATION_SIMILARITY_THRESHOLD:
            return ValidationResult(
                content=secondary_content,
                used_secondary=True,
                report={
                    "similarity": similarity,
                    "reason": "low_similarity"
                }
            )

        return ValidationResult(
            content=primary_content,
            used_secondary=False,
            report={"similarity": similarity}
        )
```

**Key Decisions**:
- Dependency injection (clients passed in constructor)
- Two-stage validation (problems → similarity)
- Configurable similarity method and threshold
- Detailed reporting for debugging

---

### Phase 5: API Layer

#### 5.1 Input Handler
**File**: `src/services/pdf_input_handler.py`

**Why First?**: Handles file uploads

```python
class PDFInputHandler:
    """Handle PDF file inputs"""

    def __init__(self):
        self.temp_files = []

    async def save_uploaded_file(self, file: UploadFile) -> str:
        """Save uploaded file to temp location"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        self.temp_files.append(temp_file.name)

        content = await file.read()
        temp_file.write(content)
        temp_file.close()

        return temp_file.name

    def decode_base64_pdf(self, base64_string: str) -> str:
        """Decode base64 PDF and save to temp file"""
        pdf_bytes = base64.b64decode(base64_string)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        self.temp_files.append(temp_file.name)

        temp_file.write(pdf_bytes)
        temp_file.close()

        return temp_file.name

    async def cleanup(self):
        """Delete all temp files"""
        for temp_file in self.temp_files:
            try:
                os.remove(temp_file)
            except Exception as e:
                logger.warning(f"Failed to delete {temp_file}: {e}")
```

**Key Decisions**:
- Track temp files for cleanup
- Support both file upload and base64
- Graceful cleanup (don't fail on cleanup errors)

#### 5.2 Response Builder
**File**: `src/services/response_builder.py`

**Why Second?**: Formats responses

```python
class ResponseBuilder:
    """Build API responses"""

    def build_json_response(self, result: WorkflowResult) -> Dict:
        """Build JSON response"""
        return {
            "status": "success",
            "content": result.content,
            "metadata": result.metadata,
            "validation_report": result.validation_report
        }

    def build_zip_response(self, result: WorkflowResult) -> StreamingResponse:
        """Build ZIP response with markdown files"""
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add full content
            zip_file.writestr("full_content.md", result.content)

            # Add individual sections
            if result.sections:
                for section in result.sections:
                    filename = f"page_{section.page_number}.md"
                    zip_file.writestr(filename, section.content)

            # Add metadata
            metadata_json = json.dumps(result.metadata, indent=2)
            zip_file.writestr("metadata.json", metadata_json)

        zip_buffer.seek(0)

        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=extraction.zip"}
        )
```

#### 5.3 Security
**File**: `src/core/security.py`

**Why Third?**: API authentication

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Security, HTTPException

security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key from Authorization header"""
    api_key = credentials.credentials
    expected_key = settings.API_KEY

    if not expected_key:
        # No API key configured, allow access
        return True

    if api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return True
```

#### 5.4 API Routes
**File**: `src/api/routes/extraction.py`

**Why Last?**: Ties everything together

```python
from fastapi import APIRouter, UploadFile, Depends
from src.core.error_handling import handle_extraction_errors
from src.services.pdf_input_handler import PDFInputHandler
from src.services.workflow_orchestrator import get_workflow_orchestrator
from src.services.response_builder import ResponseBuilder
from src.core.security import verify_api_key

router = APIRouter()

@router.post("/extract-json")
@handle_extraction_errors("JSON extraction failed")
async def extract_json(
    file: UploadFile,
    query: str = "",
    enable_validation: bool = None,
    _: bool = Depends(verify_api_key)
):
    """Extract PDF content as JSON"""

    # 1. Initialize components
    pdf_handler = PDFInputHandler()
    orchestrator = get_workflow_orchestrator()
    response_builder = ResponseBuilder()

    try:
        # 2. Save input
        pdf_path = await pdf_handler.save_uploaded_file(file)

        # 3. Execute workflow
        result = await orchestrator.execute_workflow(
            pdf_path=pdf_path,
            query=query,
            enable_validation=enable_validation
        )

        # 4. Build response
        return response_builder.build_json_response(result)

    finally:
        # 5. Cleanup
        await pdf_handler.cleanup()

@router.post("/extract")
@handle_extraction_errors("ZIP extraction failed")
async def extract_zip(
    file: UploadFile,
    query: str = "",
    enable_validation: bool = None,
    _: bool = Depends(verify_api_key)
):
    """Extract PDF content as ZIP"""

    pdf_handler = PDFInputHandler()
    orchestrator = get_workflow_orchestrator()
    response_builder = ResponseBuilder()

    try:
        pdf_path = await pdf_handler.save_uploaded_file(file)

        result = await orchestrator.execute_workflow(
            pdf_path=pdf_path,
            query=query,
            enable_validation=enable_validation
        )

        return response_builder.build_zip_response(result)

    finally:
        await pdf_handler.cleanup()
```

**Key Decisions**:
- Dependency injection for authentication
- Try-finally for guaranteed cleanup
- Reusable components (orchestrator, response builder)
- Decorator for error handling

#### 5.5 Main Application
**File**: `main.py`

**Why Last?**: Entry point

```python
from fastapi import FastAPI
from src.api.routes import extraction, health
from src.core.middleware import add_middleware
from src.core.logging import setup_logging

# Setup logging
setup_logging()

# Create app
app = FastAPI(
    title="Michman PDF Extractor",
    description="Multi-strategy PDF extraction with AI",
    version="1.0.0"
)

# Add middleware
add_middleware(app)

# Register routes
app.include_router(extraction.router, prefix="/api/v1", tags=["extraction"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Core Architecture Patterns

### 1. Strategy Pattern (Workflows)

**Problem**: Multiple extraction algorithms with different trade-offs

**Solution**: Define family of algorithms, encapsulate each, make them interchangeable

```
BaseWorkflowHandler (interface)
       ↑
       │ implements
       │
       ├── DefaultHandler (Mistral)
       ├── AzureDIHandler (Azure DI)
       ├── GeminiHandler (Gemini)
       └── OcrImagesHandler (Mistral + OpenAI)
```

**Benefits**:
- Add new workflows without modifying existing code
- Test each strategy in isolation
- Switch strategies at runtime based on query

### 2. Factory Pattern (Clients)

**Problem**: Multiple API clients with different initialization requirements

**Solution**: Encapsulate object creation, provide lazy initialization

```
ClientFactory (singleton)
    ├── mistral_client (lazy property)
    ├── openai_client (lazy property)
    ├── gemini_client (lazy property)
    └── azure_di_client (lazy property)
```

**Benefits**:
- Centralized client management
- Lazy initialization (only create when needed)
- Easy to mock for testing

### 3. Template Method Pattern (Base Classes)

**Problem**: Common structure with specific variations

**Solution**: Define skeleton in base class, let subclasses override steps

```python
class BaseDocumentClient:
    def __init__(self):
        self._validate_credentials()  # specific to each client
        # common setup

    @abstractmethod
    def _validate_credentials(self):
        pass  # each client implements differently
```

**Benefits**:
- Reuse common code
- Enforce structure
- Clear extension points

### 4. Decorator Pattern (Error Handling)

**Problem**: Consistent error handling across endpoints

**Solution**: Wrap functions with reusable error handling logic

```python
@handle_extraction_errors("Extraction failed")
async def extract_json(...):
    # business logic
```

**Benefits**:
- DRY (Don't Repeat Yourself)
- Consistent error responses
- Easy to modify error handling globally

### 5. Dependency Injection (Validation)

**Problem**: Tight coupling between validation and specific clients

**Solution**: Pass dependencies through constructor

```python
class ValidationService:
    def __init__(self, openai_client, gemini_client=None):
        self.openai_client = openai_client
        self.gemini_client = gemini_client
```

**Benefits**:
- Easy to test (inject mocks)
- Loose coupling
- Flexible client choice

### 6. Async Context Manager (Resource Lifecycle)

**Problem**: HTTP clients need proper cleanup

**Solution**: Use async context manager protocol

```python
async with get_managed_client() as client:
    response = await client.post(url, json=data)
# client automatically closed
```

**Benefits**:
- Automatic resource cleanup
- Exception safety
- Clear resource boundaries

---

## Layer-by-Layer Construction

### Layer 1: Core Infrastructure (No External Dependencies)

**Components**:
- Configuration (Pydantic Settings)
- Data Models (Pydantic BaseModel)
- Constants
- Utilities
- Error Handling

**Test Strategy**: Unit tests with mocked env vars

### Layer 2: HTTP Client (Depends on Layer 1)

**Components**:
- HTTP Client with connection pooling
- Rate limiter
- Retry logic

**Test Strategy**: Integration tests with mock HTTP server

### Layer 3: Document Clients (Depends on Layers 1-2)

**Components**:
- Base client interface
- Mistral client
- OpenAI client
- Gemini client
- Azure DI client
- Client factory

**Test Strategy**: Integration tests with real APIs (use test accounts)

### Layer 4: Validation (Depends on Layers 1-3)

**Components**:
- Content normalizer
- Problem detector
- Similarity calculator
- Validation orchestrator

**Test Strategy**: Unit tests with fixture data

### Layer 5: Workflows (Depends on Layers 1-4)

**Components**:
- Workflow types
- Base handler
- Concrete handlers
- Workflow router
- Workflow orchestrator

**Test Strategy**: Integration tests with sample PDFs

### Layer 6: API (Depends on All Layers)

**Components**:
- Input handler
- Response builder
- Security
- API routes
- Middleware
- Main application

**Test Strategy**: E2E tests with FastAPI TestClient

---

## Integration Points

### External APIs

**Mistral Document AI**:
- Endpoint: Azure OpenAI-hosted Mistral
- Authentication: API key
- Input: Base64-encoded PDF
- Output: Markdown text
- Rate limit: Configured in Azure
- Retry: 3 attempts with exponential backoff

**OpenAI Vision**:
- Endpoint: Azure OpenAI-hosted GPT-4o
- Authentication: API key
- Input: Base64-encoded images (PDF pages)
- Output: JSON/Markdown
- Rate limit: Configured in Azure
- Retry: 3 attempts with exponential backoff

**Google Gemini**:
- Endpoint: Google AI Studio
- Authentication: API key
- Input: PDF bytes + custom prompts
- Output: Markdown text
- Rate limit: 60 requests/minute
- Retry: 3 attempts with exponential backoff

**Azure Document Intelligence**:
- Endpoint: Azure Cognitive Services
- Authentication: API key
- Input: PDF URL or bytes
- Output: JSON (structured tables)
- Rate limit: Configured in Azure
- Retry: Long-running operation (polling)

### Internal Communication

**Synchronous**:
- API → Input Handler
- API → Response Builder
- Orchestrator → Handler
- Handler → Client

**Asynchronous**:
- Client → External API (async HTTP)
- Validation → Problem Detection (parallel)
- Validation → Secondary Extraction (conditional)
- Gemini → Page Processing (parallel)

---

## Scaling Considerations

### Horizontal Scaling

**Stateless Design**:
- No in-memory state (except singletons)
- Temp files use unique names
- Each request is independent

**Load Balancing**:
- API servers can run in parallel
- No shared state between instances
- Health check endpoint for monitoring

### Vertical Scaling

**Memory**:
- PDF files in temp storage (not in memory)
- Streaming responses for large outputs
- Configurable chunk sizes

**CPU**:
- Async I/O for concurrent API calls
- Parallel page processing (Gemini)
- Parallel problem detection (Validation)

### Performance Optimization

**HTTP Client**:
- Connection pooling (10 max connections)
- Keep-alive connections
- Configurable timeouts

**Caching**:
- Client factory (singleton)
- Orchestrator (singleton)
- HTTP client reuse

**Async Processing**:
- All API calls are async
- Parallel page processing where possible
- Non-blocking I/O

### Monitoring

**Health Checks**:
- `/api/v1/health` - Basic health
- `/api/v1/health/detailed` - Component health

**Logging**:
- Structured logging (JSON)
- Request/response logging
- Error tracking with stack traces
- Performance metrics (duration)

**Metrics** (to implement):
- Request count per workflow
- Average processing time
- Error rate
- API success rate

---

## Key Takeaways

### Architectural Principles Applied

1. **Separation of Concerns**: Each layer has clear responsibilities
2. **Open/Closed**: Extend without modifying (workflows, clients)
3. **Dependency Inversion**: Depend on abstractions (base classes)
4. **Single Responsibility**: Each module does one thing
5. **DRY**: Reusable components (factory, orchestrator)

### Design Patterns Used

1. **Strategy**: Workflow handlers
2. **Factory**: Client creation
3. **Template Method**: Base client
4. **Decorator**: Error handling
5. **Singleton**: Orchestrator, factory
6. **Dependency Injection**: Validation service

### Extension Points

**Add New Workflow**:
1. Create handler class (extends BaseWorkflowHandler)
2. Register in orchestrator
3. Add routing logic

**Add New Client**:
1. Create client class (extends BaseDocumentClient)
2. Add property in factory
3. Use in handler

**Add New Validation Check**:
1. Add method in ProblemDetector
2. Call in detect_problems_batch

**Add New Endpoint**:
1. Create route in extraction.py
2. Use existing components (orchestrator, response builder)

### Testing Strategy

**Unit Tests**: Core logic (normalizer, problem detector)
**Integration Tests**: API clients, workflows
**E2E Tests**: Full API flow
**Coverage Target**: 80%+

---

## Next Steps

### Recommended Implementation Order

1. **Phase 1**: Core infrastructure (config, models, utils)
2. **Phase 2**: HTTP client + one document client (Mistral)
3. **Phase 3**: Simple workflow (Default handler)
4. **Phase 4**: API layer with one endpoint
5. **Phase 5**: Add more clients (OpenAI, Gemini)
6. **Phase 6**: Add more workflows
7. **Phase 7**: Add validation system
8. **Phase 8**: Production hardening (logging, monitoring)

### Critical Decisions to Make Early

1. **Which AI provider to start with?** (Recommend: Mistral - simplest)
2. **Authentication method?** (Current: API key in header)
3. **Response format?** (Current: JSON and ZIP)
4. **Validation strategy?** (Current: Optional cross-validation)
5. **Deployment target?** (Cloud, on-premise, Docker)

### Common Pitfalls to Avoid

1. **Don't couple workflows to specific clients** - Use abstraction
2. **Don't skip error handling** - APIs fail, handle gracefully
3. **Don't hold PDFs in memory** - Use temp files
4. **Don't forget cleanup** - Use try-finally
5. **Don't hardcode configuration** - Use environment variables
6. **Don't skip logging** - Essential for debugging
7. **Don't skip tests** - Catch regressions early

---

## Conclusion

This architecture provides:
- **Flexibility**: Easy to add new workflows and clients
- **Testability**: Components are loosely coupled
- **Maintainability**: Clear structure, separation of concerns
- **Scalability**: Stateless design, async processing
- **Reliability**: Error handling, validation, monitoring

The key insight: **Abstraction at the right levels**. Workflows and clients are abstracted, but we don't over-engineer with unnecessary layers. Each component has a clear purpose and can be tested independently.
