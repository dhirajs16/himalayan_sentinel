FROM python:3.12-slim AS runtime
WORKDIR /workspace/backend
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./
RUN useradd --create-home sentinel && mkdir -p var data/processed && chown -R sentinel:sentinel /workspace
USER sentinel
EXPOSE 8000
CMD ["python", "-m", "app.bootstrap"]

FROM runtime AS test
USER root
RUN pip install --no-cache-dir "pytest>=9.1.1"
USER sentinel
CMD ["python", "-m", "pytest", "-q"]
