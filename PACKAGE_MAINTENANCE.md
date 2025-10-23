# Package Maintenance Guide

This guide covers how to maintain and publish the `brownie-metadata-db` Python package.

## 📦 Package Information

- **Package Name**: `brownie-metadata-db`
- **PyPI URL**: https://pypi.org/project/brownie-metadata-db/
- **Current Version**: 0.1.0
- **Python Support**: 3.9+
- **Package Type**: Library + CLI tool

## 🚀 Publishing New Versions

### 1. Update Version

Update the version in `pyproject.toml`:

```toml
[project]
name = "brownie-metadata-db"
version = "0.1.1"  # Increment version
```

### 2. Update Changelog

Add entry to `CHANGELOG.md`:

```markdown
## [0.1.1] - 2024-01-15

### Added
- New feature X
- Enhanced Y functionality

### Changed
- Improved Z performance

### Fixed
- Bug fix A
- Bug fix B
```

### 3. Run Tests and Formatting

```bash
# Format code
black .
isort .

# Run linting
flake8 .

# Run tests
python3 -m pytest tests/ -v

# Verify formatting
black --check --diff .
isort --check-only --diff .
```

### 4. Build Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build wheel and source distribution
python3 -m build

# Verify package contents
unzip -l dist/brownie_metadata_db-0.1.1-py3-none-any.whl | head -20
```

### 5. Test Package Locally

```bash
# Install locally for testing
python3 -m pip install dist/brownie_metadata_db-0.1.1-py3-none-any.whl --force-reinstall

# Test import
python3 -c "import brownie_metadata_db as bmd; print(f'Version: {bmd.__version__}')"

# Test CLI
brownie-backup --help
```

### 6. Upload to PyPI

**Test PyPI (recommended first):**
```bash
# Install twine if not already installed
python3 -m pip install twine

# Upload to test PyPI
python3 -m twine upload --repository testpypi dist/*

# Test installation from test PyPI
python3 -m pip install --index-url https://test.pypi.org/simple/ brownie-metadata-db==0.1.1
```

**Production PyPI:**
```bash
# Upload to production PyPI
python3 -m twine upload dist/*
```

### 7. Verify Upload

```bash
# Check package on PyPI
open https://pypi.org/project/brownie-metadata-db/

# Test installation from PyPI
python3 -m pip install brownie-metadata-db==0.1.1
```

## 🔧 Development Workflow

### Local Development

```bash
# Install in development mode
python3 -m pip install -e .

# Or install from local wheel
python3 -m pip install dist/brownie_metadata_db-0.1.0-py3-none-any.whl
```

### Testing Changes

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test categories
python3 -m pytest tests/test_models.py -v
python3 -m pytest tests/test_backup.py -v

# Run with coverage
python3 -m pytest tests/ --cov=brownie_metadata_db --cov-report=html
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Type checking
mypy brownie_metadata_db/

# Verify all checks pass
black --check --diff .
isort --check-only --diff .
flake8 .
mypy brownie_metadata_db/
```

## 📋 Package Structure

```
brownie_metadata_db/
├── __init__.py              # Main package exports
├── backup/                  # Backup system
│   ├── __init__.py
│   ├── cli.py              # CLI commands
│   ├── manager.py          # BackupManager
│   ├── providers.py        # Storage providers
│   └── scheduler.py        # Backup scheduling
├── certificates/            # SSL certificate management
│   ├── __init__.py
│   ├── config.py
│   └── validation.py
├── database/               # Database layer
│   ├── __init__.py
│   ├── base.py            # Base models
│   ├── config.py          # Database config
│   ├── connection.py      # Connection management
│   └── models/            # SQLAlchemy models
│       ├── __init__.py
│       ├── organization.py
│       ├── user.py
│       └── ...
└── logging/               # Logging utilities
    ├── __init__.py
    ├── audit.py
    ├── config.py
    └── performance.py
```

## 🔍 Package Exports

The package exports 26+ classes and functions:

### Database Models
- `Organization`, `Team`, `User`, `UserRole`
- `Incident`, `IncidentStatus`, `IncidentPriority`
- `AgentConfig`, `AgentType`
- `Stats`, `Config`, `ConfigType`, `ConfigStatus`

### Database Management
- `get_database_manager()`, `get_session()`
- `DatabaseManager`, `DatabaseSettings`

### Backup System
- `BackupManager`, `BackupProvider`
- `S3Provider`, `LocalProvider`

### Certificate Management
- `CertificateValidator`, `CertificateConfig`, `cert_config`

### Logging
- `AuditLogger`, `PerformanceLogger`
- `LoggingConfig`, `configure_logging()`

### CLI Tool
- `brownie-backup` command with subcommands:
  - `backup` - Create backups
  - `list` - List available backups
  - `restore` - Restore from backup
  - `cleanup` - Clean old backups
  - `status` - Show backup status

## 🐛 Troubleshooting

### Common Issues

**Import Errors:**
```bash
# If you get import errors, check the package is installed
python3 -c "import brownie_metadata_db; print(brownie_metadata_db.__file__)"

# Reinstall if needed
python3 -m pip install --force-reinstall brownie-metadata-db
```

**CLI Not Found:**
```bash
# Check if CLI is installed
which brownie-backup

# Reinstall package
python3 -m pip install --force-reinstall brownie-metadata-db
```

**Build Errors:**
```bash
# Clean everything and rebuild
rm -rf dist/ build/ *.egg-info/
python3 -m build
```

### Version Conflicts

If you have version conflicts:

```bash
# Check installed versions
python3 -m pip list | grep brownie

# Uninstall and reinstall
python3 -m pip uninstall brownie-metadata-db
python3 -m pip install brownie-metadata-db==0.1.0
```

## 📚 Documentation

### API Documentation

The package includes comprehensive docstrings. Generate docs:

```bash
# Install sphinx
python3 -m pip install sphinx sphinx-autodoc-typehints

# Generate documentation (if sphinx is configured)
sphinx-build -b html docs/ docs/_build/html
```

### Type Hints

All functions and classes include type hints for better IDE support:

```python
from brownie_metadata_db import Organization, User, UserRole

def create_user(name: str, email: str, role: UserRole) -> User:
    return User(username=name, email=email, role=role)
```

## 🔄 CI/CD Integration

### GitHub Actions

The repository includes GitHub Actions for:

- **Lint and Format**: Runs `black`, `isort`, `flake8`, `mypy`
- **Integration Tests**: Runs full Docker stack tests
- **Package Publishing**: Automatically publishes to PyPI on version tags

### Pre-commit Hooks

Set up pre-commit hooks for code quality:

```bash
# Install pre-commit
python3 -m pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## 📈 Monitoring Package Usage

### PyPI Statistics

Monitor package downloads:
- https://pypi.org/project/brownie-metadata-db/#statistics
- https://pepy.tech/project/brownie-metadata-db

### GitHub Insights

Check repository activity:
- Repository insights
- Download statistics
- Issue and PR activity

## 🆘 Support

### For Package Users

- **Documentation**: README.md and inline docstrings
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions

### For Package Maintainers

- **Release Process**: Follow this guide
- **Version Management**: Use semantic versioning
- **Breaking Changes**: Update major version
- **Deprecations**: Use deprecation warnings

## 📝 Release Checklist

Before each release:

- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md`
- [ ] Run all tests: `pytest tests/ -v`
- [ ] Format code: `black . && isort .`
- [ ] Lint code: `flake8 .`
- [ ] Type check: `mypy brownie_metadata_db/`
- [ ] Build package: `python3 -m build`
- [ ] Test package locally
- [ ] Update README.md if needed
- [ ] Create GitHub release
- [ ] Upload to PyPI
- [ ] Verify installation from PyPI

---

**Package Maintainer**: Update this guide as the package evolves!
