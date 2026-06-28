FROM python:3.11-slim
WORKDIR /app
COPY challenges/injection/xxe-1/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY challenges/injection/xxe-1/app.py /app/app.py
EXPOSE 9208
CMD ["gunicorn","-b","0.0.0.0:9208","-w","1","--threads","8","app:app"]
