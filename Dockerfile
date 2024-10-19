FROM python:3.10

WORKDIR /app/

# # Install cmake (required by ecos)
RUN apt-get update && apt-get install -y cmake

# Install system-level dependencies required by cvxpy and its solvers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    libblas-dev \
    liblapack-dev \
    libgfortran5 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in requirements.txt
COPY ./requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt


ENV PYTHONPATH=/app

COPY ./scripts/ /app/

COPY ./app /app/app

# Comment this line for deployment
# ENV PORT 8080

EXPOSE 8080

# Uncomment this line for deployment
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
