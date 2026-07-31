FROM python:3.11-slim
WORKDIR /app
COPY platform/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY platform/ /app/
ENV USERS_PATH=/data/users.json
EXPOSE 9000
# sync 워커 2개(=동시 2연결)로 200명을 받다가 스코어보드가 상시 먹통이 됐다.
# 브라우저는 한 명당 소켓을 2~4개 미리 열어 두는데, sync 워커는 그런 '아직 요청을
# 안 보낸 연결' 하나가 워커 하나를 --timeout(기본 30초) 동안 통째로 점유한다.
# 학생 25명만 접속해도 빈 소켓이 50개 → 2칸짜리 워커풀은 영구 포화(WORKER TIMEOUT
# 시간당 50~135회, 가용률 0%). 제출 페이지가 안 떠서 '플래그 인증이 안 된다' 로 보였다.
# gevent 는 연결마다 그린렛이라 놀고 있는 소켓은 워커를 잡지 않는다 = 근본 해결.
# 계정 파일 갱신은 app.py 의 파일 락으로 보호하므로 워커를 늘려도 안전하다.
CMD ["gunicorn", "-b", "0.0.0.0:9000", \
     "-k", "gevent", "-w", "4", "--worker-connections", "1000", \
     "--timeout", "60", "--graceful-timeout", "10", "--keep-alive", "5", \
     "--access-logfile", "-", "app:app"]
