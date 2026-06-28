FROM python:3.11-slim
WORKDIR /app
COPY challenges/client/csrf-1/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY _base/flask_board /app/flask_board
COPY challenges/client/csrf-1/app.py /app/app.py
EXPOSE 9104
CMD ["gunicorn","-b","0.0.0.0:9104","-w","1","--threads","8","app:app"]
