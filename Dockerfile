FROM python:3.12

ENV PYTHONPATH src/

WORKDIR /app
RUN pip install --upgrade pip setuptools wheel
RUN pip install poetry~="1.8.0" --upgrade

COPY pyproject.toml poetry.lock alembic.ini ./
COPY src src
COPY migrations migrations

RUN poetry install -vvv  --only main

CMD ["poetry", "run", "python", "src/main.py"]
