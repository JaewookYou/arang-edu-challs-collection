FROM python:3.11-slim
WORKDIR /app
COPY challenges/logic/race-transfer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY challenges/logic/race-transfer/app.py /app/app.py
EXPOSE 9401
# --threads 는 '동시에 검증을 통과할 수 있는 요청 수' = 경합 창의 폭.
# 8 이면 최대 800 까지만 적립되어 목표(1000) 도달 불가 → 경합이 성립하려면 10 이상 필요.
# 잔액이 수강생별로 분리된 뒤로는 이 값이 '동시에 시도할 수 있는 인원' 도 결정한다.
# 한 명이 10요청 이상을 겹쳐 보내야 하므로 24 면 두 명이 겹치는 순간 서로의 요청이
# 직렬화돼 둘 다 실패한다 → 64 로 키워 여러 명이 동시에 풀 수 있게 한다.
CMD ["gunicorn","-b","0.0.0.0:9401","-w","1","--threads","64","app:app"]
