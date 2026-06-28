# build context = repo root (docker-compose 에서 지정)
FROM python:3.11-slim
WORKDIR /app
COPY challenges/client/xss-1/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY _base/flask_board /app/flask_board
COPY challenges/client/xss-1/app.py /app/app.py
EXPOSE 9101
# 인메모리 상태(게시글/유저) 공유를 위해 단일 워커 + 멀티스레드
CMD ["gunicorn", "-b", "0.0.0.0:9101", "-w", "1", "--threads", "8", "app:app"]
