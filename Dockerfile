# Use a slim Python image as a base
FROM python:3.13-slim

RUN pip install uvicorn fastapi sqlalchemy alembic jinja2

# Copy the application code
WORKDIR /app

# Copy source code
COPY src/ ./src/
COPY templates/ ./templates/

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info", "--access-log"]
