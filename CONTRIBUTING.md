# Contributing to ACBox

Thank you for your interest in contributing to ACBox! This document 
provides instructions for setting up your development environment and 
the workflow for making changes.

## Development Environment Setup

ACBox uses `uv` for dependency management, but you can also use 
standard `pip`.

### Prerequisites

- Python 3.10 or higher
- `uv` (recommended) or `pip`
- `make` (optional, for running convenience targets)

### Setup with `uv` (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/cav71/acbox.git
   cd acbox
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   uv sync --group dev
   ```

3. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

### Setup with `pip`

1. **Clone the repository:**
   ```bash
   git clone https://github.com/cav71/acbox.git
   cd acbox
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -e .
   # To install dev dependencies (using the dependency groups from pyproject.toml)
   # Note: pip support for [dependency-groups] is available in newer versions via `pip install --group`
   # or you can use:
   python -m pip install pre-commit ruff mypy pytest pytest-cov
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

## Development Workflow

### Code Quality and Linting

We use `ruff` for formatting and linting, and `mypy` for type checking.

Using `make`:
```bash
make fmt    # Format code
make check  # Run all checks (ruff + mypy)
make lint   # Run only mypy
```

Without `make`:
```bash
ruff format .
ruff check --fix .
mypy src tests
```

### Running Tests

We use `pytest` for testing.

Using `make`:
```bash
make tests     # Run all tests
make coverage  # Run tests with coverage report
```

Without `make`:
```bash
pytest tests
```

### Documentation

Documentation is built with `mkdocs` and `mkdocs-material`.

To serve documentation locally:
```bash
mkdocs serve
```
