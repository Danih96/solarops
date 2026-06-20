FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN mkdir app && touch app/__init__.py && \
    pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
RUN useradd -m appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
