FROM python:3.12.7-slim

# Working directory
WORKDIR /app

# Environment variables
ENV DIR_MOVIES=/data/movies
ENV DIR_TV=/data/tv
ENV DIR_SRC=/data/src
ENV DIR_OUTPUT=/data/output
ENV DIR_TMP=/data/tmp

# Create directories within the container
RUN mkdir -p $DIR_MOVIES $DIR_TV $DIR_SRC $DIR_OUTPUT $DIR_TMP

# Install system dependencies
RUN apt-get update && apt-get install -y \
    mkvtoolnix \
    ffmpeg \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5656

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=5656"]