FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY mock_sinks.py .
EXPOSE 9000
CMD ["uvicorn", "mock_sinks:app", "--host", "0.0.0.0", "--port", "9000"]
