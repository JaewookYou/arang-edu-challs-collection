FROM python:3.11-slim
WORKDIR /app
COPY challenges/injection/xxe-1/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY challenges/injection/xxe-1/app.py /app/app.py
EXPOSE 9208
# gthread(-w 1 --threads 8) 였는데, 본문을 끝까지 안 보내는 요청이 스레드를 영구
# 점유해도 accept 루프는 살아 있어 gunicorn 이 heartbeat 를 계속 보낸다 → 아비터가
# 워커를 회수하지 못하고, 8개가 다 막히면 문제가 통째로 먹통이 된다(실제 26시간 정지).
# sync 워커는 요청 처리 중엔 heartbeat 를 못 보내므로 --timeout 을 넘기면 아비터가
# 죽이고 새로 띄운다 = 자동 복구. 프로세스 8개(≈240MB)로 동시 처리량도 유지.
CMD ["gunicorn","-b","0.0.0.0:9208","-w","8","--timeout","20","--graceful-timeout","5","--keep-alive","2","app:app"]
