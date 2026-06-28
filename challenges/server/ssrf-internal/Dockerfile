FROM python:3.11-slim
WORKDIR /app
COPY challenges/server/ssrf-internal/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY challenges/server/ssrf-internal/app.py /app/app.py
EXPOSE 9502
CMD ["gunicorn","-b","0.0.0.0:9502","-w","1","--threads","8","app:app"]
