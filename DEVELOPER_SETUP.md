# Developer Setup Guide

This guide helps developers get started with the Brownie Metadata Database project.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Git

### 1. Clone Repository

```bash
git clone https://github.com/longyi-brownie/brownie-metadata-database.git
cd brownie-metadata-database
```

### 2. Install Package in Development Mode

```bash
# Install the package in editable mode
python3 -m pip install -e .

# Or install from local wheel
python3 -m pip install dist/brownie_metadata_db-0.1.0-py3-none-any.whl
```

### 3. Verify Installation

```bash
# Test import
python3 -c "import brownie_metadata_db as bmd; print(f'Version: {bmd.__version__}')"

# Test CLI
brownie-backup --help
```

## 🛠️ Development Workflow

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Type checking
mypy brownie_metadata_db/

# Run all quality checks
python3 scripts/package-manager.py build
```

### Testing

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run with coverage
python3 -m pytest tests/ --cov=brownie_metadata_db --cov-report=html

# Run specific test file
python3 -m pytest tests/test_models.py -v
```

### Package Management

```bash
# Build package
python3 scripts/package-manager.py build

# Test package locally
python3 scripts/package-manager.py test

# Update version
python3 scripts/package-manager.py version 0.1.1
```

## 🐳 Docker Development

### Start Full Stack

```bash
# Generate SSL certificates
./scripts/setup-dev-certs.sh

# Start all services
docker compose up -d

# Check services
docker compose ps
```

### Database Operations

```bash
# Connect to database
docker compose exec postgres psql -U brownie-fastapi-server -d brownie_metadata

# Run migrations
docker compose exec app alembic upgrade head

# Create new migration
docker compose exec app alembic revision --autogenerate -m "Add new table"
```

## 📦 Package Development

### Project Structure

```
brownie_metadata_db/          # Main package
├── __init__.py              # Package exports
├── backup/                  # Backup system
├── certificates/            # SSL management
├── database/               # Database layer
└── logging/                # Logging utilities
```

### Adding New Features

1. **Create new module** in appropriate subpackage
2. **Add exports** to `__init__.py`
3. **Write tests** in `tests/`
4. **Update documentation** in docstrings
5. **Run quality checks** before committing

### Example: Adding New Model

```python
# brownie_metadata_db/database/models/new_model.py
from sqlalchemy import Column, String
from ..base import BaseModel

class NewModel(BaseModel):
    __tablename__ = "new_models"
    
    name = Column(String(255), nullable=False)
```

```python
# brownie_metadata_db/database/models/__init__.py
from .new_model import NewModel

__all__ = [
    # ... existing exports
    "NewModel",
]
```

```python
# brownie_metadata_db/__init__.py
from .database.models import NewModel

__all__ = [
    # ... existing exports
    "NewModel",
]
```

## 🔧 IDE Setup

### VS Code

Install recommended extensions:
- Python
- Pylance
- Black Formatter
- isort

### PyCharm

Configure code style:
- Set formatter to Black
- Enable isort on save
- Configure mypy for type checking

## 🧪 Testing Strategy

### Test Categories

1. **Unit Tests** - Individual functions/classes
2. **Integration Tests** - Database operations
3. **Docker Tests** - Full stack testing

### Writing Tests

```python
# tests/test_new_feature.py
import pytest
from brownie_metadata_db import NewModel

def test_new_model_creation():
    model = NewModel(name="test")
    assert model.name == "test"
```

### Test Database

Tests use a separate test database:
- Automatically created/cleaned
- Isolated from development data
- Fast setup/teardown

## 📚 Documentation

### Docstrings

Follow Google style:

```python
def example_function(param1: str, param2: int) -> bool:
    """Example function with proper docstring.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param1 is invalid
    """
    pass
```

### README Updates

When adding features:
1. Update library usage examples
2. Add new classes to exports list
3. Update project structure if needed

## 🚀 Publishing

### Release Process

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md**
3. **Run tests**: `python3 scripts/package-manager.py test`
4. **Commit changes**
5. **Create git tag**: `git tag v0.1.1`
6. **Push tag**: `git push origin v0.1.1`
7. **GitHub Actions** will automatically publish to PyPI

### Manual Publishing

```bash
# Build and test
python3 scripts/package-manager.py build
python3 scripts/package-manager.py test

# Publish to PyPI
python3 scripts/package-manager.py publish
```

## 🐛 Debugging

### Common Issues

**Import Errors:**
```bash
# Check if package is installed
python3 -c "import brownie_metadata_db; print(brownie_metadata_db.__file__)"

# Reinstall if needed
python3 -m pip install -e .
```

**Database Connection:**
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Check logs
docker compose logs postgres
```

**Test Failures:**
```bash
# Run with verbose output
python3 -m pytest tests/ -v -s

# Run specific test
python3 -m pytest tests/test_models.py::test_organization_creation -v
```

## 📞 Getting Help

- **Documentation**: README.md and inline docstrings
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Code Review**: All changes require PR review

## 🔄 Contributing

1. **Fork repository**
2. **Create feature branch**: `git checkout -b feature/new-feature`
3. **Make changes** with tests
4. **Run quality checks**: `python3 scripts/package-manager.py build`
5. **Commit changes**: `git commit -m "Add new feature"`
6. **Push branch**: `git push origin feature/new-feature`
7. **Create Pull Request**

---

Happy coding! 🎉
