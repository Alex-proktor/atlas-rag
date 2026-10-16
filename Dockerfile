FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml ./
COPY atlas_rag ./atlas_rag
RUN pip install --no-cache-dir .
RUN useradd --create-home --uid 10001 atlas
USER atlas
EXPOSE 8000
CMD ["uvicorn", "atlas_rag.main:app", "--host", "0.0.0.0", "--port", "8000"]
