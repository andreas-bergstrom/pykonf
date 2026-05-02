FROM python:3.9-slim-buster AS builder

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .


FROM gcr.io/distroless/python3-debian10

COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

EXPOSE 8000

CMD ["python", "-m", "pykonf"]
