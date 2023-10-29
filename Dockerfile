FROM python:3.9-slim-buster

ENV POETRY_HOME=/etc/poetry
ENV POETRY_VERSION=1.2.2

RUN apt-get update --assume-yes && apt-get install -y curl libpq-dev gcc netcat

RUN curl -sSL https://install.python-poetry.org | python3 - --version ${POETRY_VERSION}

ENV PATH="$POETRY_HOME/bin:$PATH"

RUN poetry config virtualenvs.create false

COPY ./pyproject.toml ./poetry.lock ./gunicorn.conf.py ./README.md /app/

WORKDIR /app

RUN mkdir logs

RUN poetry install --no-interaction --no-root

COPY ./benchmark benchmark

RUN poetry install --no-interaction

EXPOSE 8000

ENTRYPOINT ["opentelemetry-instrument"]

CMD ["gunicorn", \
    "-k", \
    "uvicorn.workers.UvicornWorker", \
    "benchmark.main:app", \
    "-b", \
    "0.0.0.0:8000"\
]
