# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# psycopg2-binary usually works fine, but sometimes needs libpq-dev
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('vader_lexicon')"

# Copy the current directory contents into the container at /app
COPY . .

# Expose the port that Streamlit runs on
EXPOSE 8501

# Define environment variable for Streamlit
ENV PORT=8501

# Run streamlit when the container launches
# This can be overridden by the command in docker-compose or render.yaml
CMD ["streamlit", "run", "src/dashboards/streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
