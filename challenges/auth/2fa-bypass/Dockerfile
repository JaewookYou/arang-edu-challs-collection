FROM python:3.11-slim
WORKDIR /app
COPY challenges/auth/2fa-bypass/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY challenges/auth/2fa-bypass/app.py /app/app.py
EXPOSE 9302
CMD ["gunicorn","-b","0.0.0.0:9302","-w","1","--threads","8","app:app"]
