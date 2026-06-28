FROM python:3.11-slim
WORKDIR /app
COPY challenges/logic/race-transfer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY challenges/logic/race-transfer/app.py /app/app.py
EXPOSE 9401
# --threads 는 '동시에 검증을 통과할 수 있는 요청 수' = 경합 창의 폭.
# 8 이면 최대 800 까지만 적립되어 목표(1000) 도달 불가 → 24 로 키워 경합이 성립하게 함.
CMD ["gunicorn","-b","0.0.0.0:9401","-w","1","--threads","24","app:app"]
