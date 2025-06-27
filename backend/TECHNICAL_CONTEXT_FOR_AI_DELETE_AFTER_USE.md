# IMPORTANT: TECHNICAL CONTEXT FOR AI - DELETE AFTER USE

This file provides technical context about your project for AI co-editors.
If your AI co-editor uses file-based memory, instruct it to read the content of this file to populate its memory.
You can safely delete this file after your AI has gained sufficient context and populated its memory, or keep it if you plan to continue using AI assistance.

---

## Project Overview

This project is a FastAPI application generated from a cookiecutter template. It is designed with a modern Python stack, emphasizing best practices for development, testing, and deployment. It includes structured logging, configuration management, and a comprehensive set of development tools managed via `Justfile` and `nix`.

## Technologies Used

- **Framework**: FastAPI
- **Language**: Python 3.12+
- **Dependency Management**: `uv`
- **Package Management & Build**: `hatchling` (configured in `pyproject.toml`)
- **Task Runner**: `Justfile`
- **Environment Management**: `nix` for reproducible development environments.
- **Containerization**: Docker image building is managed through `nix`.

## Development Workflow & Tooling

The `Justfile` in the project root provides commands for all common development tasks.

- **Run the development server**: `just backend-server`
- **Run tests**: `just test` (uses `pytest`)
- **Run code quality checks**: `just check` (runs `ruff` for linting, `mypy` for type checking, and `bandit` for security scanning).
- **Fix code automatically**: `just fix` (runs `ruff --fix` and `black` for formatting).

## Project Structure

- `src/sia/`: Contains the main application source code.
  - `main.py`: The FastAPI application entry point. It initializes the app, sets up middleware (logging, security headers), and includes the API routers.
  - `config.py`: Manages application settings using `pydantic-settings`.
  - `routers/`: Contains API route modules. Example: `cash.py`.
  - `telemetry/`: Configures structured logging using `structlog`.
- `tests/`: Contains the test suite using `pytest`.
- `pyproject.toml`: Defines project dependencies, build system (`hatchling`), and tool configurations (`ruff`, `black`, `mypy`, `bandit`).
- `flake.nix` / `flake.lock`: Defines the Nix development environment for full reproducibility.
- `Justfile`: Provides a command-line interface for development tasks.

## Key Features

- **Structured Logging**: Uses `structlog` for JSON-formatted, context-rich logs.
- **Configuration Management**: Settings are managed via environment variables and Pydantic models in `config.py`.
- **Middleware**: Includes middleware for logging HTTP requests and adding security headers to responses.
- **Global Exception Handling**: A global exception handler is in place to catch unhandled errors and return a generic 500 response.
- **Health Check**: A `/healthz` endpoint is provided for monitoring application health.
- **Dockerization**: Builds multi-platform Docker images using `nix` for consistent and reproducible builds.
