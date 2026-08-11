FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY evalkit ./evalkit
COPY datasets ./datasets

# Default: run the eval suite against the offline mock as a release gate.
ENTRYPOINT ["python", "-m", "evalkit.run"]
CMD ["--dataset", "datasets/support_agent.yaml", "--target", "mock", "--report", "out/report.md"]
