# Custom Subagents for Blackedge OCR

This directory contains documentation for custom subagents that can be launched using the Task tool for specialized operations.

## How to Use Subagents

Subagents are launched on-demand using the Task tool:

```python
# In Claude Code, use the Task tool:
Task(
    subagent_type="general-purpose",  # or specific type
    prompt="Your detailed prompt here",
    description="Short description"
)
```

## Available Subagents

### 1. test-coverage-agent
**Purpose:** Analyze and improve test coverage
**When to use:** After completing a phase, before releases
**See:** [test-coverage-agent.md](./test-coverage-agent.md)

### 2. integration-tester-agent
**Purpose:** Run end-to-end integration tests
**When to use:** Before major releases, after adding new providers
**See:** [integration-tester-agent.md](./integration-tester-agent.md)

### 3. performance-optimizer-agent
**Purpose:** Profile and optimize performance
**When to use:** Performance issues, before production
**See:** [performance-optimizer-agent.md](./performance-optimizer-agent.md)

### 4. dependency-updater-agent
**Purpose:** Safely update project dependencies
**When to use:** Monthly updates, security alerts
**See:** [dependency-updater-agent.md](./dependency-updater-agent.md)

### 5. migration-assistant-agent
**Purpose:** Help with code migrations and refactoring
**When to use:** Major version upgrades, architecture changes
**See:** [migration-assistant-agent.md](./migration-assistant-agent.md)

### 6. api-doc-generator-agent
**Purpose:** Generate comprehensive API documentation
**When to use:** After API changes, before releases
**See:** [api-doc-generator-agent.md](./api-doc-generator-agent.md)

### 7. error-analyzer-agent
**Purpose:** Analyze error patterns and improve handling
**When to use:** Production errors, weekly analysis
**See:** [error-analyzer-agent.md](./error-analyzer-agent.md)

### 8. benchmark-runner-agent
**Purpose:** Run comprehensive benchmarks
**When to use:** Evaluating providers, quarterly reviews
**See:** [benchmark-runner-agent.md](./benchmark-runner-agent.md)

## Subagent vs Slash Command

**Use Slash Commands** (`/command`) for:
- Quick, interactive operations
- Testing and validation
- Status checks
- Configuration

**Use Subagents** (Task tool) for:
- Long-running operations
- Complex multi-step tasks
- Code generation
- Comprehensive analysis

## Example Usage

### Using a Slash Command
```bash
/test-phase 1 --coverage
# Quick test execution with immediate feedback
```

### Using a Subagent
```
User: "I need comprehensive test coverage analysis for Phase 1"