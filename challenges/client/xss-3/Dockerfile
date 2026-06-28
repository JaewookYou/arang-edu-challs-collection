FROM python:3.11-slim
WORKDIR /app
COPY challenges/client/xss-3/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY _base/flask_board /app/flask_board
COPY challenges/client/xss-3/app.py /app/app.py
EXPOSE 9103
CMD ["gunicorn","-b","0.0.0.0:9103","-w","1","--threads","8","app:app"]
