# Workflow Testing & Debug Skill

You are a workflow debugging specialist for the Blackedge OCR project. Test, debug, and optimize the workflow system.

## Capabilities

### 1. Workflow Routing Test
Test which workflow is selected for a given query.

### 2. Workflow Execution
Execute specific workflows with sample PDFs.

### 3. Workflow Comparison
Run the same PDF through all workflows and compare results.

### 4. Performance Benchmarking
Measure time, accuracy, and cost for each workflow.

### 5. Debug Mode
Step-by-step execution with detailed logging.

## Commands

```bash
/workflow test "<query>"               # Test workflow routing
/workflow list                         # List all available workflows
/workflow execute <workflow> <pdf>    # Run specific workflow
/workflow compare <pdf>               # Run all workflows on PDF
/workflow benchmark <pdf>             # Performance comparison
/workflow debug "<query>" <pdf>       # Debug workflow execution
```

## Available Workflows

### 1. TEXT_EXTRACTION
**Keywords**: "text extraction", "pdfplumber", "no ai", "simple extract"
**Use Case**: Fast text-only extraction without AI
**Method**: pdfplumber library
**Cost**: Free
**Speed**: Very fast (<5s for 10-page PDF)

### 2. MISTRAL (Default)
**Keywords**: "mistral", "default"
**Use Case**: General-purpose extraction
**Method**: Mistral AI via Azure
**Cost**: $0.001 per page
**Speed**: Fast (10-30s for 10-page PDF)

### 3. AZURE_DOCUMENT_INTELLIGENCE
**Keywords**: "azure di", "document intelligence", "smart tables", "form recognition"
**Use Case**: Complex tables and forms
**Method**: Azure Document Intelligence
**Cost**: $0.01 per page
**Speed**: Medium (30-60s for 10-page PDF)

### 4. OCR_WITH_IMAGES
**Keywords**: "ocr", "images", "charts", "diagrams", "vision", "scanned"
**Use Case**: Scanned documents, charts, diagrams
**Method**: Mistral + OpenAI Vision
**Cost**: $0.003 per page
**Speed**: Slow (60-120s for 10-page PDF)

### 5. GEMINI
**Keywords**: "gemini", "google"
**Use Case**: High-quality extraction with Gemini
**Method**: Google Gemini
**Cost**: $0.002 per page
**Speed**: Medium (20-45s for 10-page PDF)

## Workflow Routing Process

The `WorkflowRouter` analyzes the query to determine the best workflow:

1. **Extract keywords** from query (case-insensitive)
2. **Match against patterns** (priority order)
3. **Return workflow type**
4. **Default to MISTRAL** if no match

Priority Order:
1. TEXT_EXTRACTION (highest priority - no AI cost)
2. AZURE_DOCUMENT_INTELLIGENCE (specialized for tables)
3. OCR_WITH_IMAGES (for scanned docs)
4. GEMINI (specific provider)
5. MISTRAL (default fallback)

## Output Format

### Workflow Routing Test
```
🔀 Workflow Routing Test
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Query: "extract tables from financial report"

✅ Selected Workflow: AZURE_DOCUMENT_INTELLIGENCE

📊 Match Analysis:
  AZURE_DI:    ████████░░  80% (keywords: "tables")
  MISTRAL:     ████░░░░░░  40% (default)
  OCR_IMAGES:  ██░░░░░░░░  20% (no match)
  GEMINI:      ░░░░░░░░░░   0% (no match)
  TEXT_ONLY:   ░░░░░░░░░░   0% (no match)

💡 Why this workflow?
  - Query contains "tables" keyword
  - Azure DI optimized for table extraction
  - High accuracy for financial data

⚙️  Workflow Details:
  - Provider: Azure Document Intelligence
  - Est. Time: 30-60s for 10 pages
  - Est. Cost: $0.10 for 10 pages
  - Features: Smart table detection, form recognition

🔄 Alternative Workflows:
  1. MISTRAL: Faster but less accurate for tables
  2. OCR_IMAGES: Better if document is scanned
```

### Workflow Comparison
```
📊 Workflow Comparison: financial_report.pdf
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Document: financial_report.pdf (15 pages, 3.2 MB)

┌─────────────────┬──────────┬───────────┬─────────┬─────────────┐
│ Workflow        │ Time     │ Accuracy  │ Cost    │ Tables      │
├─────────────────┼──────────┼───────────┼─────────┼─────────────┤
│ TEXT_EXTRACTION │ 3s       │ 60%       │ Free    │ ❌ Broken   │
│ MISTRAL         │ 22s      │ 85%       │ $0.015  │ ⚠️  Partial │
│ AZURE_DI        │ 45s      │ 98%       │ $0.150  │ ✅ Perfect  │
│ OCR_IMAGES      │ 95s      │ 82%       │ $0.045  │ ⚠️  Partial │
│ GEMINI          │ 38s      │ 90%       │ $0.030  │ ✅ Good     │
└─────────────────┴──────────┴───────────┴─────────┴─────────────┘

🏆 Best for Accuracy: AZURE_DI (98%)
⚡ Best for Speed: TEXT_EXTRACTION (3s)
💰 Best for Cost: TEXT_EXTRACTION (Free)
🎯 Recommended: AZURE_DI (best quality/cost balance for tables)

📈 Detailed Metrics:
  - Tables extracted: 12 total
    • AZURE_DI: 12/12 (100%)
    • GEMINI: 11/12 (92%)
    • MISTRAL: 8/12 (67%)
    • OCR_IMAGES: 9/12 (75%)
    • TEXT_EXTRACTION: 3/12 (25%)

  - Numbers accuracy:
    • AZURE_DI: 99.8% correct
    • GEMINI: 98.5% correct
    • MISTRAL: 94.2% correct
```

### Debug Mode
```
🐛 Workflow Debug: financial_report.pdf
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Query: "extract financial tables"
Workflow: AZURE_DOCUMENT_INTELLIGENCE

[Step 1] Routing
  ✓ Query analyzed
  ✓ Keywords matched: ["financial", "tables"]
  ✓ Workflow selected: AZURE_DI

[Step 2] Input Processing
  ✓ PDF validated: 15 pages, 3.2 MB
  ✓ File size OK (< 50 MB)
  ✓ Extension valid: .pdf

[Step 3] Client Initialization
  ✓ Azure DI client created
  ✓ API key validated
  ✓ Endpoint accessible

[Step 4] Document Processing
  ⏳ Uploading document... (2s)
  ⏳ Starting analysis... (5s)
  ⏳ Processing pages 1-5... (15s)
  ⏳ Processing pages 6-10... (12s)
  ⏳ Processing pages 11-15... (11s)
  ✓ Analysis complete

[Step 5] Result Extraction
  ✓ Tables detected: 12
  ✓ Text blocks: 45
  ✓ Content formatted

[Step 6] Validation (if enabled)
  ⊗ Validation skipped (not enabled)

[Step 7] Response Building
  ✓ Metadata collected
  ✓ Sections organized
  ✓ Response formatted

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Workflow completed successfully
⏱️  Total time: 45.3s
💰 Estimated cost: $0.15
```

## Testing Scenarios

### Scenario 1: Financial Reports
```bash
/workflow test "extract financial data and tables"
# Expected: AZURE_DI (tables keyword)
```

### Scenario 2: Scanned Documents
```bash
/workflow test "OCR this scanned document with charts"
# Expected: OCR_WITH_IMAGES (ocr + charts keywords)
```

### Scenario 3: Simple Text
```bash
/workflow test "just extract the text, no AI needed"
# Expected: TEXT_EXTRACTION (no ai keyword)
```

### Scenario 4: Default Case
```bash
/workflow test "process this document"
# Expected: MISTRAL (default, no specific keywords)
```

## Performance Benchmarking

Run comprehensive benchmarks:

```bash
/workflow benchmark sample.pdf
```

This will:
1. Run same PDF through all 5 workflows
2. Measure time, accuracy, cost
3. Compare extraction quality
4. Generate recommendation

Benchmark includes:
- **Speed**: Processing time
- **Accuracy**: Manual validation against ground truth
- **Cost**: Estimated API costs
- **Quality**: Table extraction, number accuracy, format preservation

## Debugging Tips

### Common Issues

**Issue 1: Wrong workflow selected**
```
Problem: Query "extract tables" → MISTRAL (expected AZURE_DI)
Fix: Use "smart tables" or "document intelligence" keywords
```

**Issue 2: Workflow fails**
```
Problem: AZURE_DI workflow timeout
Debug: /workflow debug "azure di" sample.pdf
Check: API key, endpoint, rate limits
```

**Issue 3: Poor extraction quality**
```
Problem: Tables not extracted correctly
Solution: /workflow compare sample.pdf
       Then choose best workflow for document type
```

## Integration with Code

### Using in Python
```python
from src.services.workflow_router import get_workflow_type
from src.services.workflow_orchestrator import get_workflow_orchestrator

# Test routing
query = "extract financial tables"
workflow_type = get_workflow_type(query)
print(f"Selected: {workflow_type}")

# Execute workflow
orchestrator = get_workflow_orchestrator()
result = await orchestrator.execute_workflow(
    pdf_path="document.pdf",
    query=query
)
```

### Custom Workflow Keywords
To add custom routing logic, edit:
- `src/core/constants.py` → Update `WORKFLOW_KEYWORDS`
- `src/services/workflow_router.py` → Update routing logic

## Examples

### Example 1: Test routing
```
User: /workflow test "extract tables from financial report"
```

### Example 2: List workflows
```
User: /workflow list
```

### Example 3: Compare all workflows
```
User: /workflow compare report.pdf
```

### Example 4: Debug execution
```
User: /workflow debug "azure di tables" report.pdf
```
