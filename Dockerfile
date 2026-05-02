# First stage: build the Python application
FROM python:3.9-slim-buster AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Second stage: create the final image with gcr.io/distroless as the base
FROM gcr.io/distroless/python3-debian10

COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /app /app

EXPOSE 8000

CMD ["python", "/api.py"]
