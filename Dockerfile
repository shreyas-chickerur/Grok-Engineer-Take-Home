FROM python:3.11-slim

# Prevents Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1         
ENV PIP_DISABLE_PIP_VERSION_CHECK=on         
ENV PIP_NO_CACHE_DIR=on         
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

COPY . .
EXPOSE 8501

# Default environment, can be overridden by docker-compose or env file
ENV DB_PATH=/app/data/app.db         
ENV GROK_API_URL=https://api.x.ai/v1         
ENV GROK_MODEL=grok-4         
ENV STREAMLIT_SERVER_PORT=8501

# Create data dir for SQLite
RUN mkdir -p /app/data

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--theme.base=light"]
