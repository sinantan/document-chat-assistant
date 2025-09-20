#!/bin/sh

# Alembic entrypoint script for production
# This script runs database migrations and starts the application

set -e

echo "Starting Document Chat Assistant..."

# Wait for database services to be ready
echo "Waiting for PostgreSQL..."
./docker/wait-for.sh ${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432} -t 30

echo "Waiting for MongoDB..."
./docker/wait-for.sh ${MONGO_HOST:-mongodb}:${MONGO_PORT:-27017} -t 30

echo "Waiting for Redis..."
./docker/wait-for.sh ${REDIS_HOST:-redis}:${REDIS_PORT:-6379} -t 30

echo "All services are ready!"

# Run database migrations
echo "Running database migrations..."
poetry run alembic upgrade head

echo "Starting the application..."
exec poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
