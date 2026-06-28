# Race Condition — 이체

| | |
|---|---|
| 버그클래스 | Race Condition (TOCTOU) |
| 난이도 | ★★☆ |
| 포트 | 9401 |

## 학습 목표
잔액 검증 후 차감까지 시간차가 있고 락이 없다. 동시에 다수 요청을 보내면 같은 잔액으로 여러 번 이체된다.

## 실행
```bash
./gen_flags.sh
docker compose up -d --build race-transfer
# http://localhost:9401
```

## 진행
1. me=100. `/transfer?amt=100` 1회는 정상.
2. `/transfer?amt=100` 을 동시에 수십 번 전송(race).
3. 검증을 동시에 통과 → vault 가 1000+ 누적 → `/flag`.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
공유자원 갱신을 원자적으로(트랜잭션/락/SELECT FOR UPDATE), 잔액 차감과 검증을 한 단위로.
