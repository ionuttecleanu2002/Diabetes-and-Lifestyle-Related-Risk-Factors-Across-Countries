# Task 1.3 — Development Environment

## Operating System

- **Operating System:** Linux Mint 22.3

## Installed Development Tools

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.12.3 | Main programming language for the project |
| Git | 2.43.0 | Version control and source code management |
| VSCodium | 1.108.20787 | Code editor and development environment |
| PostgreSQL | 16.15 | Relational database management system |
| FastAPI | 0.162.0 | Backend API framework |
| Uvicorn | 0.54.0 | ASGI server for running the FastAPI application |
| SQLAlchemy | 2.1.8 | Python SQL toolkit and ORM |
| Docker Engine | 29.9.3 | Containerization platform |
| Docker Compose | 5.7.0 | Management of multi-container applications |

## Python Environment

A Python virtual environment named `venv` is configured in the project directory. It isolates the project's Python dependencies from system-wide packages.

The following Python packages are installed:

- FastAPI
- Uvicorn
- SQLAlchemy

## Database Environment

PostgreSQL 16.15 is installed and its command-line tools are available. This version satisfies the assignment's stated minimum requirement of PostgreSQL 16.

## Containerization Environment

Docker Engine and Docker Compose are installed. The Docker installation was tested successfully using the `hello-world` image, confirming that the Docker client can communicate with the Docker daemon and run containers.

## Development Setup Summary

The development environment provides the main tools required to build the Global Health Data Platform:

- Python for data extraction, processing, analysis, and machine learning.
- PostgreSQL for persistent storage of global health indicators.
- FastAPI and Uvicorn for the backend API.
- SQLAlchemy for database interaction through Python.
- VSCodium for code editing and project management.
- Git for version control.
- Docker and Docker Compose for containerization and service orchestration.