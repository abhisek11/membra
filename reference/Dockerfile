# Sentra — pure standard-library, so the image is tiny and dependency-free.
FROM python:3.12-slim

WORKDIR /app
COPY sentra/ ./sentra/
COPY demo/mock_upstream.py ./demo/mock_upstream.py

# Train the injection model at build time so the image ships ready-to-serve.
RUN python3 -m sentra.detectors.ml_injection

ENV SENTRA_PORT=8100
# Point at your real provider in production, e.g. https://api.openai.com
ENV SENTRA_UPSTREAM=https://api.openai.com
EXPOSE 8100

CMD ["python3", "-m", "sentra.app"]
