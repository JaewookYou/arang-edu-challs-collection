FROM python:3.11-slim
WORKDIR /app
COPY challenges/injection/ssti-1/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY challenges/injection/ssti-1/app.py /app/app.py
EXPOSE 9207
CMD ["gunicorn","-b","0.0.0.0:9207","-w","1","--threads","8","app:app"]
