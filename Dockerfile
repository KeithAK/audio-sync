# Start from a Python 3.12 slim image
FROM python:3.12.7-slim

# Set up the working directory
WORKDIR /app

# Define environment variables for linked directories
ENV DIR_MOVIES=/data/movies
ENV DIR_TV=/data/tv
ENV DIR_SRC=/data/src
ENV DIR_OUTPUT=/data/output
ENV DIR_TMP=/data/tmp

# Create the directories within the container
RUN mkdir -p $DIR_MOVIES $DIR_TV $DIR_SRC $DIR_OUTPUT $DIR_TMP

# Install system dependencies like mkvtoolnix
RUN apt-get update && apt-get install -y \
    mkvtoolnix \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port for Streamlit
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501"]