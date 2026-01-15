# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 8501
CMD ["streamlit", "run", "gnce/ui/gn_app.py", "--server.port=8501", "--server.address=0.0.0.0"]