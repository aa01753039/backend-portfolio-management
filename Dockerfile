FROM python:3.10

WORKDIR /app/

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./pyproject.toml ./poetry.lock* /app/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi"

ENV PYTHONPATH=/app

COPY ./scripts/ /app/

COPY ./app /app/app

#comment this line for deployment
# COPY ./secrets /app/secrets

# Ensure that the app listens on port 8080 for Cloud Run compatibility
# ENV PORT 8080
EXPOSE 8080

#uncomment this line for deployment
# Command to start Uvicorn (make sure it listens on all interfaces and the correct port)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
