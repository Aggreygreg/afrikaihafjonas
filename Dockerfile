# Base image
FROM python:3.12-slim

# Set environment variables to prevent temporary file buffering
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app