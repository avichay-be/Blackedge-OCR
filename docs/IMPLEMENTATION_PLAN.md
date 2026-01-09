# Implementation Plan - Michman PDF Extractor

A detailed, phase-by-phase guide to building the PDF extraction system from scratch.

---

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)

**Goal**: Set up the foundational layer that all other components depend on.

#### Tasks:

1. **Project Setup**
   - [x] Initialize Git repository
   - [x] Create directory structure
   - [x] Set up virtual environment
   - [ ] Install dependencies from requirements.txt
   - [ ] Create .env file from .env.example

2. **Configuration System** (`src/core/config.py`)
   - [ ] Create Settings class with Pydantic
   - [ ] Load environment variables
   - [ ] Add validation for required fields
   - [ ] Test configuration loading

3. **Data Models** (`src/models/`)
   - [ ] Create `workflow_models.py`
     - ExtractedSection model
     - WorkflowResult model
     - ValidationResult model
   - [ ] Create `api_models.py`
     - Request models
     - Response models
   - [ ] Write unit tests for models

4. **Constants** (`src/core/constants.py`)
   - [ ] Define content separators
   - [ ] Define chunk sizes
   - [ ] Define timeout values
   - [ ] Define workflow keywords

5. **Utilities** (`src/core/utils.py`)
   - [ ] PDF to base64 encoder
   - [ ] Base64 to PDF decoder
   - [ ] File size checker
   - [ ] Page counter
   - [ ] Write unit tests

6. **Error Handling** (`src/core/error_handling.py`)
   - [ ] Define exception hierarchy
   - [ ] Create error handler decorator
   - [ ] Add logging integration
   - [ ] Write tests for error handling

**Success Criteria**:
- All core modules importable
- Configuration loads from .env
- Models validate correctly
- Utilities work with sample PDFs
- Error handlers catch and log exceptions

---

### Phase 2: HTTP Client Layer (Week 1-2)

**Goal**: Create reusable HTTP client infrastructure for all API calls.

#### Tasks:

1. **HTTP Client** (`src/core/http_client.py`)
   - [ ] Implement async client with httpx
   - [ ] Add connection pooling
   - [ ] Configure timeouts
   - [ ] Create context manager
   - [ ] Add request logging

2. **Rate Limiter** (`src/core/rate_limiter.py`)
   - [ ] Implement token bucket algorithm
   - [ ] Make configurable per provider
   - [ ] Add async support
   - [ ] Write tests

3. **Retry Logic** (`src/core/retry.py`)
   - [ ] Implement exponential backoff
   - [ ] Make retry count configurable
   - [ ] Handle specific HTTP errors
   - [ ] Add logging
   - [ ] Write tests

**Success Criteria**:
- HTTP client handles concurrent requests
- Rate limiting prevents API overload
- Retry logic handles transient failures
- All components tested with mock server

---

### Phase 3: Document Clients (Week 2-3)

**Goal**: Implement AI provider clients with unified interface.

#### Tasks:

1. **Base Client** (`src/services/clients/base_client.py`)
   - [ ] Define abstract base class
   - [ ] Add abstract methods:
     - `_validate_credentials()`
     - `extract_page_content()`
     - `process_document()`
     - `health_check()`
   - [ ] Implement context manager protocol
   - [ ] Add logging

2. **Mistral Client** (`src/services/clients/mistral_client.py`)
   - [ ] Implement BaseDocumentClient
   - [ ] Add credential validation
   - [ ] Implement document processing
   - [ ] Add error handling
   - [ ] Write integration tests
   - [ ] Test with real API

3. **OpenAI Client** (`src/services/clients/openai_client.py`)
   - [ ] Implement BaseDocumentClient
   - [ ] Add vision API support
   - [ ] Implement image extraction
   - [ ] Add error handling
   - [ ] Write integration tests

4. **Gemini Client** (`src/services/clients/gemini_client.py`)
   - [ ] Implement BaseDocumentClient
   - [ ] Add parallel page processing
   - [ ] Implement rate limiting
   - [ ] Add error handling
   - [ ] Write integration tests

5. **Azure DI Client** (`src/services/clients/azure_di_client.py`)
   - [ ] Implement BaseDocumentClient
   - [ ] Add long-running operation support
   - [ ] Implement polling mechanism
   - [ ] Add table extraction
   - [ ] Write integration tests

6. **Client Factory** (`src/services/client_factory.py`)
   - [ ] Implement singleton pattern
   - [ ] Add lazy initialization for each client
   - [ ] Implement getter methods
   - [ ] Add cleanup method
   - [ ] Write unit tests

**Success Criteria**:
- All clients implement common interface
- Each client works with its respective API
- Factory provides lazy initialization
- Health checks work for all clients
- Integration tests pass

---

### Phase 4: Workflow System (Week 3-4)

**Goal**: Build the strategy pattern-based workflow system.

#### Tasks:

1. **Workflow Types** (`src/services/workflows/workflow_types.py`)
   - [ ] Define WorkflowType enum
   - [ ] Add workflow descriptions
   - [ ] Document use cases

2. **Base Handler** (`src/services/workflows/base_handler.py`)
   - [ ] Define abstract base class
   - [ ] Add abstract execute method
   - [ ] Define common interface

3. **Text Extraction Handler** (`src/services/workflows/text_extraction_handler.py`)
   - [ ] Implement with pdfplumber
   - [ ] No AI, pure text extraction
   - [ ] Fast processing
   - [ ] Write unit tests

4. **Default Handler** (`src/services/workflows/default_handler.py`)
   - [ ] Use Mistral client
   - [ ] Add validation support
   - [ ] Implement metadata collection
   - [ ] Write integration tests

5. **Azure DI Handler** (`src/services/workflows/azure_di_handler.py`)
   - [ ] Use Azure DI client
   - [ ] Optimize for tables
   - [ ] Add post-processing
   - [ ] Write integration tests

6. **OCR Images Handler** (`src/services/workflows/ocr_images_handler.py`)
   - [ ] Use Mistral + OpenAI
   - [ ] Extract images from PDF
   - [ ] Process with vision API
   - [ ] Combine results
   - [ ] Write integration tests

7. **Gemini Handler** (`src/services/workflows/gemini_handler.py`)
   - [ ] Use Gemini client
   - [ ] Add parallel processing
   - [ ] Implement rate limiting
   - [ ] Write integration tests

8. **Workflow Router** (`src/services/workflow_router.py`)
   - [ ] Implement keyword-based routing
   - [ ] Add priority order
   - [ ] Default to Mistral
   - [ ] Write unit tests

9. **Workflow Orchestrator** (`src/services/workflow_orchestrator.py`)
   - [ ] Implement singleton pattern
   - [ ] Register all handlers
   - [ ] Add workflow selection logic
   - [ ] Implement execute method
   - [ ] Add logging
   - [ ] Write integration tests

**Success Criteria**:
- All handlers implement common interface
- Router correctly maps queries to workflows
- Orchestrator executes workflows
- Can switch workflows at runtime
- Integration tests with sample PDFs pass

---

### Phase 5: Validation System (Week 4-5)

**Goal**: Build optional quality validation system.

#### Tasks:

1. **Content Normalizer** (`src/services/validation/content_normalizer.py`)
   - [ ] Implement text normalization
   - [ ] Add number extraction
   - [ ] Add whitespace handling
   - [ ] Write unit tests

2. **Problem Detector** (`src/services/validation/problem_detector.py`)
   - [ ] Implement quality checks:
     - Low content density
     - Missing numbers
     - Repeated characters
     - Malformed tables
     - Unicode errors
     - Truncated content
   - [ ] Add parallel detection
   - [ ] Write unit tests

3. **Similarity Calculator** (`src/services/validation/similarity_calculator.py`)
   - [ ] Implement number frequency method
   - [ ] Implement Levenshtein method
   - [ ] Add cosine similarity
   - [ ] Make method configurable
   - [ ] Write unit tests

4. **Validation Service** (`src/services/validation/validation_service.py`)
   - [ ] Implement two-stage validation
   - [ ] Add problem detection
   - [ ] Add similarity comparison
   - [ ] Implement secondary extraction
   - [ ] Add detailed reporting
   - [ ] Write integration tests

**Success Criteria**:
- Problem detector identifies quality issues
- Similarity calculator works accurately
- Validation service improves extraction quality
- Detailed reports available
- Integration tests with problematic PDFs pass

---

### Phase 6: API Layer (Week 5-6)

**Goal**: Build FastAPI REST API with endpoints.

#### Tasks:

1. **PDF Input Handler** (`src/services/pdf_input_handler.py`)
   - [ ] Handle file uploads
   - [ ] Handle base64 input
   - [ ] Implement temp file management
   - [ ] Add cleanup logic
   - [ ] Write unit tests

2. **Response Builder** (`src/services/response_builder.py`)
   - [ ] Implement JSON response builder
   - [ ] Implement ZIP response builder
   - [ ] Add markdown formatting
   - [ ] Add metadata inclusion
   - [ ] Write unit tests

3. **Health Routes** (`src/api/routes/health.py`)
   - [ ] Implement basic health check
   - [ ] Implement detailed health check
   - [ ] Check all client connections
   - [ ] Add system info endpoint
   - [ ] Write tests

4. **Extraction Routes** (`src/api/routes/extraction.py`)
   - [ ] Implement /extract-json endpoint
   - [ ] Implement /extract (ZIP) endpoint
   - [ ] Add request validation
   - [ ] Add authentication
   - [ ] Add error handling
   - [ ] Write E2E tests

5. **Main Application** (`main.py`)
   - [ ] Create FastAPI app
   - [ ] Register routes
   - [ ] Add middleware
   - [ ] Configure CORS
   - [ ] Add startup/shutdown events
   - [ ] Write tests

**Success Criteria**:
- API accepts PDF uploads
- Both endpoints return correct formats
- Health checks work
- Authentication enforced
- E2E tests pass

---

### Phase 7: Security & Error Handling (Week 6)

**Goal**: Add production-grade security and error handling.

#### Tasks:

1. **Security** (`src/core/security.py`)
   - [ ] Implement API key authentication
   - [ ] Add rate limiting per key
   - [ ] Validate file types
   - [ ] Validate file sizes
   - [ ] Add CORS configuration
   - [ ] Write tests

2. **Middleware** (`src/core/middleware.py`)
   - [ ] Add request logging
   - [ ] Add response logging
   - [ ] Add timing middleware
   - [ ] Add error catching middleware
   - [ ] Write tests

3. **Comprehensive Error Handling**
   - [ ] Add specific error types
   - [ ] Create error response models
   - [ ] Add error logging
   - [ ] Add error monitoring
   - [ ] Write tests

**Success Criteria**:
- API key authentication works
- Unauthorized requests rejected
- All errors logged properly
- Middleware tracks all requests
- Security tests pass

---

### Phase 8: Logging & Monitoring (Week 7)

**Goal**: Add observability and monitoring capabilities.

#### Tasks:

1. **Logging Setup** (`src/core/logging.py`)
   - [ ] Configure structlog
   - [ ] Add JSON formatting
   - [ ] Configure log levels
   - [ ] Add request ID tracking
   - [ ] Add performance logging
   - [ ] Write tests

2. **Monitoring**
   - [ ] Add request counters
   - [ ] Add timing metrics
   - [ ] Add error counters
   - [ ] Add workflow metrics
   - [ ] Create metrics endpoint

3. **Health Checks**
   - [ ] Add component health checks
   - [ ] Add dependency health checks
   - [ ] Add system resource checks
   - [ ] Create health dashboard
   - [ ] Write tests

**Success Criteria**:
- All operations logged
- Metrics collected
- Health checks comprehensive
- Performance trackable
- Monitoring tests pass

---

### Phase 9: Testing (Week 7-8)

**Goal**: Achieve comprehensive test coverage.

#### Tasks:

1. **Unit Tests** (`tests/unit/`)
   - [ ] Test all core utilities
   - [ ] Test all models
   - [ ] Test normalization
   - [ ] Test problem detection
   - [ ] Test similarity calculation
   - [ ] Test workflow router
   - [ ] Achieve 90%+ coverage

2. **Integration Tests** (`tests/integration/`)
   - [ ] Test each client with API
   - [ ] Test each workflow handler
   - [ ] Test validation service
   - [ ] Test orchestrator
   - [ ] Use real test accounts

3. **E2E Tests** (`tests/e2e/`)
   - [ ] Test full extraction flow
   - [ ] Test all endpoints
   - [ ] Test error scenarios
   - [ ] Test authentication
   - [ ] Test with various PDF types

4. **Test Infrastructure**
   - [ ] Create test fixtures
   - [ ] Create mock clients
   - [ ] Add sample PDFs
   - [ ] Configure pytest
   - [ ] Set up CI/CD tests

**Success Criteria**:
- 80%+ code coverage
- All critical paths tested
- Integration tests with real APIs
- E2E tests cover main flows
- Tests run in CI/CD

---

### Phase 10: Deployment & Documentation (Week 8)

**Goal**: Make the system production-ready and well-documented.

#### Tasks:

1. **Docker Setup**
   - [ ] Create Dockerfile
   - [ ] Create docker-compose.yml
   - [ ] Add health checks
   - [ ] Optimize image size
   - [ ] Test container

2. **Deployment Documentation** (`docs/DEPLOYMENT.md`)
   - [ ] Document environment setup
   - [ ] Document configuration
   - [ ] Add deployment guide
   - [ ] Add scaling guide
   - [ ] Add troubleshooting guide

3. **API Documentation**
   - [ ] Enhance OpenAPI schema
   - [ ] Add request examples
   - [ ] Add response examples
   - [ ] Add authentication guide
   - [ ] Test interactive docs

4. **Developer Documentation**
   - [ ] Update README
   - [ ] Add contributing guide
   - [ ] Add code style guide
   - [ ] Add extension guide
   - [ ] Add FAQ

5. **Production Hardening**
   - [ ] Add request validation
   - [ ] Add input sanitization
   - [ ] Add resource limits
   - [ ] Add graceful shutdown
   - [ ] Add monitoring alerts

**Success Criteria**:
- Docker container runs successfully
- Documentation complete
- API docs comprehensive
- Production checklist complete
- Ready for deployment

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| 1 | Week 1 | Core infrastructure |
| 2 | Week 1-2 | HTTP client layer |
| 3 | Week 2-3 | All AI clients |
| 4 | Week 3-4 | Workflow system |
| 5 | Week 4-5 | Validation system |
| 6 | Week 5-6 | API endpoints |
| 7 | Week 6 | Security layer |
| 8 | Week 7 | Monitoring |
| 9 | Week 7-8 | Comprehensive tests |
| 10 | Week 8 | Deployment ready |

**Total Duration**: 8 weeks

---

## Daily Development Workflow

### Morning (2-3 hours)
1. Review yesterday's work
2. Write/update tests for today's tasks
3. Implement new features (TDD approach)

### Afternoon (2-3 hours)
4. Integration testing
5. Code review and refactoring
6. Documentation updates

### Evening (1 hour)
7. Git commit and push
8. Update progress tracker
9. Plan next day's tasks

---

## Best Practices

### Code Quality
- Write tests before implementation (TDD)
- Keep functions small and focused
- Use type hints everywhere
- Follow PEP 8 style guide
- Run black, flake8, mypy before commit

### Git Workflow
- Commit frequently with clear messages
- Use feature branches
- Write descriptive commit messages
- Tag releases

### Documentation
- Document as you code
- Update docstrings
- Keep README current
- Add examples

---

## Risk Management

### Technical Risks

1. **API Rate Limits**
   - Risk: Hitting provider rate limits
   - Mitigation: Implement rate limiting, use multiple providers

2. **API Reliability**
   - Risk: External APIs down
   - Mitigation: Retry logic, fallback workflows, health checks

3. **Large PDF Processing**
   - Risk: Memory issues, timeouts
   - Mitigation: Chunking, streaming, resource limits

4. **Validation Accuracy**
   - Risk: False positives in problem detection
   - Mitigation: Tunable thresholds, multiple validation methods

### Schedule Risks

1. **API Access Delays**
   - Risk: Waiting for API keys
   - Mitigation: Request early, use mocks for development

2. **Integration Issues**
   - Risk: Unexpected API behavior
   - Mitigation: Thorough testing, good error handling

---

## Success Metrics

### Code Quality
- [ ] 80%+ test coverage
- [ ] All type hints pass mypy
- [ ] Zero flake8 warnings
- [ ] All tests pass

### Performance
- [ ] < 30s for 10-page PDF
- [ ] < 2 min for 100-page PDF
- [ ] Handles 10 concurrent requests

### Reliability
- [ ] 99%+ uptime
- [ ] < 1% error rate
- [ ] All errors logged and monitored

### Documentation
- [ ] All public APIs documented
- [ ] Architecture documented
- [ ] Deployment guide complete
- [ ] Contributing guide available

---

## Next Steps

After Phase 10, consider:

1. **Performance Optimization**
   - Implement caching
   - Add CDN for static assets
   - Optimize database queries (if added)

2. **Advanced Features**
   - Batch processing API
   - Webhook support
   - Real-time progress tracking
   - PDF comparison API

3. **Scaling**
   - Kubernetes deployment
   - Multi-region support
   - Load balancer configuration
   - Auto-scaling rules

4. **Monitoring & Analytics**
   - Grafana dashboards
   - Error tracking (Sentry)
   - Usage analytics
   - Cost tracking

---

This implementation plan provides a clear roadmap from empty repository to production-ready system. Follow it sequentially, test thoroughly, and iterate based on feedback.
