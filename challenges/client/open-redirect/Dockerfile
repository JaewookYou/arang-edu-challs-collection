FROM python:3.11-slim
WORKDIR /app
COPY challenges/client/open-redirect/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY _base/flask_board /app/flask_board
COPY challenges/client/open-redirect/app.py /app/app.py
EXPOSE 9108
CMD ["gunicorn","-b","0.0.0.0:9108","-w","1","--threads","8","app:app"]
