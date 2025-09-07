# Diun Dashboard

A web-based dashboard to visualize and manage Docker image update notifications from [Diun](https://crazymax.dev/diun/).

## Features

*   Displays Diun notifications in a user-friendly interface.
*   Uses SQLite for persistent storage.
*   Easy setup with Docker Compose.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/)

### Installation

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

### Accessing the Dashboard

Once the services are up and running, you can access the Diun Dashboard in your web browser at:

```
http://localhost:8554
```

## Project Structure

*   `main.py`: The main FastAPI application.
*   `database.py`: Handles database connection and operations.
*   `templates/index.html`: The main HTML template for the dashboard.
*   `alembic/`: Database migrations.

## TODOs
1. Right now the dashboards shows only one entry per image, but it should be per image per server.
2. Tests:
    - Add a few entries from different servers and different images.
3. Make it runable without docker and convert to uv