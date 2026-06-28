FROM python:3.11-slim
WORKDIR /app
COPY challenges/auth/idor-balance/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY challenges/auth/idor-balance/app.py /app/app.py
EXPOSE 9301
CMD ["gunicorn","-b","0.0.0.0:9301","-w","1","--threads","8","app:app"]
