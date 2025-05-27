FROM python:3.10-slim

WORKDIR /app

COPY . .

COPY local_packages /app/local_packages

RUN pip install --no-cache-dir --no-index --find-links=/app/local_packages -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "cloud_frontend.py", "--server.port=8501", "--server.address=0.0.0.0"]
