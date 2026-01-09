# Blackedge OCR - Michman PDF Extractor

A production-grade, multi-strategy PDF extraction system leveraging multiple AI providers (Mistral, OpenAI, Gemini, Azure Document Intelligence) for intelligent document processing.

## Features

- **Multi-Strategy Extraction**: Choose from 5 different extraction workflows based on your needs
- **AI-Powered**: Leverages Mistral, OpenAI GPT-4o, Google Gemini, and Azure Document Intelligence
- **Quality Validation**: Optional cross-validation system to ensure extraction accuracy
- **Flexible Output**: Get results as JSON or organized ZIP archives
- **Production-Ready**: Built with FastAPI, async processing, and comprehensive error handling
- **Extensible Architecture**: Easy to add new AI providers or extraction strategies

## Architecture Highlights

- **Clean Architecture**: Separation of concerns across API, Business Logic, and Service layers
- **Strategy Pattern**: Workflows are pluggable and interchangeable
- **Factory Pattern**: Centralized client management with lazy initialization
- **Async/Await**: Non-blocking I/O for optimal performance
- **Quality-First**: Built-in validation and error handling

## Quick Start

### Prerequisites

- Python 3.9+
- API keys for AI providers (Mistral/Azure OpenAI, Google Gemini, etc.)

### Installation

```bash
# Clone repository
git clone https://github.com/avichay-be/Blackedge-OCR.git
cd Blackedge-OCR

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: `http://localhost:8000`
Interactive docs at: `http://localhost:8000/docs`

## API Endpoints

### Extract as JSON

```bash
curl -X POST "http://localhost:8000/api/v1/extract-json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@document.pdf" \
  -F "query=extract all tables and text"
```

### Extract as ZIP

```bash
curl -X POST "http://localhost:8000/api/v1/extract" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@document.pdf" \
  -F "query=extract with azure di" \
  -o result.zip
```

## Extraction Workflows

1. **Default (Mistral)**: General-purpose extraction using Mistral AI
2. **Text Extraction**: Fast, no-AI extraction using pdfplumber
3. **Azure Document Intelligence**: Optimized for complex tables and forms
4. **OCR with Images**: Best for scanned documents and charts
5. **Gemini**: High-quality extraction using Google Gemini

Workflows are automatically selected based on query keywords, or you can specify explicitly.

## Project Structure

```
blackedge-ocr/
├── src/
│   ├── api/
│   │   └── routes/          # FastAPI route definitions
│   ├── core/                # Configuration, constants, utilities
│   ├── models/              # Pydantic data models
│   └── services/
│       ├── clients/         # AI provider clients
│       ├── workflows/       # Extraction strategy handlers
│       └── validation/      # Quality validation system
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/               # End-to-end tests
├── docs/                   # Documentation
├── main.py                # Application entry point
└── requirements.txt       # Python dependencies
```

## Configuration

Key environment variables (see `.env.example`):

```env
# API Keys
AZURE_API_KEY=your_azure_key
MISTRAL_API_URL=your_mistral_url
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key

# Validation
ENABLE_CROSS_VALIDATION=false
VALIDATION_SIMILARITY_THRESHOLD=0.95

# Security
API_KEY=your_api_key
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suite
pytest tests/unit
pytest tests/integration
pytest tests/e2e
```

### Code Quality

```bash
# Format code
black src tests

# Lint
flake8 src tests

# Type checking
mypy src
```

## Documentation

- [Architecture Guide](docs/ARCHITECTURE.md) - Detailed system design and patterns
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md) - Step-by-step build guide
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when server is running)

## Extending the System

### Adding a New AI Provider

1. Create client class extending `BaseDocumentClient`
2. Add property to `ClientFactory`
3. Use in workflow handlers

### Adding a New Workflow

1. Create handler class extending `BaseWorkflowHandler`
2. Register in `WorkflowOrchestrator`
3. Add routing logic in `WorkflowRouter`

See [Architecture Guide](docs/ARCHITECTURE.md) for detailed instructions.

## Performance

- Async processing for concurrent API calls
- Connection pooling for HTTP efficiency
- Streaming responses for large outputs
- Stateless design for horizontal scaling

## Security

- API key authentication
- No secrets in code (environment variables only)
- Input validation with Pydantic
- Temporary file cleanup
- Rate limiting (configurable)

## Monitoring

Health check endpoints:
- `GET /api/v1/health` - Basic health status
- `GET /api/v1/health/detailed` - Component-level health

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## Support

- Issues: https://github.com/avichay-be/Blackedge-OCR/issues
- Documentation: https://github.com/avichay-be/Blackedge-OCR/docs

## Roadmap

- [ ] Phase 1: Core infrastructure (In Progress)
- [ ] Phase 2: HTTP client layer
- [ ] Phase 3: Document clients
- [ ] Phase 4: Workflow system
- [ ] Phase 5: Validation system
- [ ] Phase 6: API layer
- [ ] Phase 7: Security & error handling
- [ ] Phase 8: Monitoring & observability
- [ ] Phase 9: Comprehensive testing
- [ ] Phase 10: Deployment & documentation

---

Built with FastAPI, powered by multiple AI providers, designed for production.
