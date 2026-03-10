# Contributing to Multi-Agent Orchestrator

Thank you for your interest in contributing to the Multi-Agent Orchestrator! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git
- OpenAI API Key (optional, for testing with real LLM)

### Development Setup

1. **Fork and clone the repository**
```bash
git clone https://github.com/your-username/multi-agent-orchestrator.git
cd multi-agent-orchestrator
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run tests to verify setup**
```bash
pytest
```

## 🏗️ Development Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Critical production fixes

### Making Changes

1. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**
   - Write clean, documented code
   - Follow existing code style
   - Add tests for new functionality

3. **Run quality checks**
```bash
# Format code
black src tests

# Lint code
flake8 src tests

# Type checking
mypy src

# Run tests
pytest --cov=src
```

4. **Commit your changes**
```bash
git add .
git commit -m "feat: add new feature description"
```

5. **Push and create PR**
```bash
git push origin feature/your-feature-name
```

## 📝 Code Style Guidelines

### Python Style

- Follow PEP 8 guidelines
- Use Black for code formatting
- Maximum line length: 88 characters
- Use type hints for all functions
- Write docstrings for all public functions and classes

### Example Code Style

```python
"""
Module docstring describing the purpose.
"""
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ExampleClass:
    """
    Class docstring describing the class purpose.
    
    Args:
        param1: Description of parameter
        param2: Description of parameter
    """
    
    def __init__(self, param1: str, param2: Optional[int] = None):
        self.param1 = param1
        self.param2 = param2
    
    async def example_method(self, data: Dict[str, str]) -> List[str]:
        """
        Method docstring describing what it does.
        
        Args:
            data: Input data dictionary
            
        Returns:
            List of processed strings
            
        Raises:
            ValueError: If data is invalid
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        logger.info(f"Processing {len(data)} items")
        return list(data.values())
```

### Commit Message Format

Use conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(agents): add new researcher agent capabilities
fix(api): resolve websocket connection timeout issue
docs(readme): update installation instructions
```

## 🧪 Testing Guidelines

### Test Structure

- Unit tests: `tests/test_*.py`
- Integration tests: `tests/integration/`
- Test fixtures: `tests/conftest.py`

### Writing Tests

```python
import pytest
from src.agents import ResearcherAgent


class TestResearcherAgent:
    """Test cases for ResearcherAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return ResearcherAgent()
    
    @pytest.mark.asyncio
    async def test_research_success(self, agent):
        """Test successful research execution."""
        # Test implementation
        pass
    
    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        assert agent.name == "Researcher"
```

### Test Coverage

- Maintain minimum 80% test coverage
- Test both success and failure scenarios
- Include edge cases and error conditions
- Mock external dependencies

## 📚 Documentation

### Code Documentation

- Write clear docstrings for all public APIs
- Include type hints
- Document complex algorithms and business logic
- Update README.md for significant changes

### API Documentation

- FastAPI automatically generates OpenAPI docs
- Ensure all endpoints have proper descriptions
- Include example requests/responses
- Document error codes and responses

## 🔍 Code Review Process

### Before Submitting PR

- [ ] All tests pass
- [ ] Code is formatted with Black
- [ ] No linting errors
- [ ] Type checking passes
- [ ] Documentation is updated
- [ ] Commit messages follow convention

### PR Requirements

- Clear description of changes
- Link to related issues
- Screenshots for UI changes
- Performance impact assessment
- Breaking changes documented

### Review Criteria

- Code quality and maintainability
- Test coverage and quality
- Documentation completeness
- Performance considerations
- Security implications

## 🐛 Bug Reports

### Before Reporting

1. Check existing issues
2. Verify with latest version
3. Test with minimal reproduction case

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Environment:**
- OS: [e.g. Ubuntu 20.04]
- Python version: [e.g. 3.11.0]
- Package version: [e.g. 1.0.0]

**Additional context**
Any other context about the problem.
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Any other context or screenshots about the feature request.
```

## 🏷️ Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Release Checklist

- [ ] Update version numbers
- [ ] Update CHANGELOG.md
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Create release notes
- [ ] Tag release
- [ ] Deploy to production

## 📞 Getting Help

- **Issues**: GitHub Issues for bugs and features
- **Discussions**: GitHub Discussions for questions
- **Email**: [your-email@example.com]

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Multi-Agent Orchestrator! 🎉