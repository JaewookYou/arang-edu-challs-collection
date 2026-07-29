FROM python:3.11-slim
WORKDIR /app
COPY challenges/injection/cmdi-1/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY challenges/injection/cmdi-1/app.py /app/app.py
# 이 문제는 '/' 가 자기 소스를 그대로 뿌린다. blind 인젝션이라 원격 수강생에게는
# `cat flag >> app.py` 로 결과를 소스에 섞어 회수하는 게 사실상 유일한 in-band 통로다.
# 그런데 그 상태로 gunicorn 이 모듈을 다시 import 하면 SyntaxError 로 컨테이너가 죽어
# 한 명 때문에 나머지 전원이 문제를 못 푼다(실제 발생: 재부팅 후 crash loop).
# → (1) 기동할 때마다 읽기전용 원본에서 복원, (2) --preload 로 워커가 재기동돼도
#    파일을 다시 읽지 않게 한다. 풀이 경로(append 후 '/' 조회)는 그대로 살아 있다.
RUN cp /app/app.py /opt/app.py.orig
EXPOSE 9206
CMD ["sh","-c","cp -f /opt/app.py.orig /app/app.py 2>/dev/null; exec gunicorn -b 0.0.0.0:9206 -w 1 --threads 8 --preload app:app"]
