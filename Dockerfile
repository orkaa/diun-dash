# Use a slim Python image as a base
FROM python:3.13-slim

RUN pip install uvicorn fastapi sqlalchemy alembic jinja2

# Copy the application code
WORKDIR /app

# Copy alembic configuration and scripts
COPY alembic.ini .
COPY alembic/ ./alembic/

# Copy the application code
COPY main.py .
COPY database.py .
COPY templates/ ./templates/

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info", "--access-log"]
