FROM python:3.15-alpine

WORKDIR /app

COPY scripts/ scripts/

# Install requests + requests-ratelimiter for Docker mode
RUN pip install --no-cache-dir -r scripts/requirements.txt

# Enable Docker mode: use requests + requests-ratelimiter instead of stdlib urllib
ENV AVE_USE_DOCKER=true

ENTRYPOINT ["python", "scripts/ave_client.py"]
