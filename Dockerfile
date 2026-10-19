FROM python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN python -m pip install --no-cache-dir pip==26.2.1 setuptools==84.0.0
RUN pip install --no-cache-dir torch==2.14.1+cpu --index-url https://download.pytorch.org/whl/cpu
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
RUN python -c "import torch; assert torch.version.cuda is None, 'CPU image must not load CUDA'"
COPY pyproject.toml ./
COPY atlas_rag ./atlas_rag
RUN pip install --no-cache-dir --no-deps .
RUN useradd --create-home --uid 10001 atlas && mkdir -p /home/atlas/state /home/atlas/.cache && chown -R atlas:atlas /home/atlas/state /home/atlas/.cache
COPY tests ./tests
COPY examples ./examples
COPY evaluation ./evaluation
COPY integrations ./integrations
USER atlas
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"
CMD ["uvicorn", "atlas_rag.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-concurrency", "16", "--no-access-log"]
