# Diun Dashboard

A web-based dashboard to visualize and manage Docker image update notifications from [Diun](https://crazymax.dev/diun/).

## Features

*   Displays Diun notifications in a user-friendly interface
*   Uses SQLite for persistent storage
*   Easy setup with Docker Compose
*   Modern Python development with uv package manager
*   Convenient development scripts for common tasks
*   FastAPI backend with Alembic database migrations

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

#### For Docker deployment:
*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/)

#### For local development:
*   Python 3.13+
*   [uv](https://docs.astral.sh/uv/) package manager

### Installation

#### Option 1: Docker Deployment (Recommended)

1.  Clone this repository:

    ```bash
    git clone https://github.com/your-repo/diun-dash.git
    cd diun-dash
    ```

2.  Copy the example environment file and configure it if necessary:

    ```bash
    cp .env.example .env
    ```

3.  Start the application using Docker Compose:

    ```bash
    docker-compose up -d
    ```

#### Option 2: Local Development Setup

1.  Clone this repository:

    ```bash
    git clone https://github.com/your-repo/diun-dash.git
    cd diun-dash
    ```

2.  Install dependencies with uv:

    ```bash
    uv sync
    ```

3.  Run database migrations:

    ```bash
    ./scripts/migrate.sh
    ```

4.  Start the development server:

    ```bash
    ./scripts/dev.sh
    ```

### Accessing the Dashboard

Once the services are up and running, you can access the Diun Dashboard in your web browser at:

```
http://localhost:8554
```

## Development Scripts

The project includes convenient scripts for common development tasks:

*   `./scripts/dev.sh` - Start the development server with auto-reload
*   `./scripts/test.sh` - Run the test suite with pytest
*   `./scripts/migrate.sh` - Run database migrations

## Project Structure

```
diun-dash/
├── src/                    # Source code directory
│   ├── main.py            # Main FastAPI application
│   ├── database.py        # Database connection and operations
│   └── templates/         # Jinja2 templates
│       └── index.html     # Main dashboard template
├── alembic/               # Database migrations
├── scripts/               # Development convenience scripts
│   ├── dev.sh            # Development server
│   ├── test.sh           # Test runner
│   └── migrate.sh        # Database migrations
├── pyproject.toml         # Python project configuration
├── uv.lock               # Locked dependencies
└── Dockerfile            # Container build configuration
```

## Development

### Running Tests

```bash
./scripts/test.sh
```

### Database Migrations

To create a new migration:

```bash
uv run alembic revision --autogenerate -m "Description of changes"
```

To apply migrations:

```bash
./scripts/migrate.sh
```

### Technology Stack

*   **Backend**: FastAPI with Python 3.13+
*   **Database**: SQLite with SQLAlchemy ORM
*   **Migrations**: Alembic
*   **Package Management**: uv
*   **Templates**: Jinja2
*   **Testing**: pytest
*   **Containerization**: Docker & Docker Compose

## TODOs
- Right now the dashboards shows only one entry per image, but it should be per image per server.
- Tests:
    - Add a few entries from different servers and different images.
- Pin the version on uv we pull into docker image
- "Fix all" button to remove all current entries