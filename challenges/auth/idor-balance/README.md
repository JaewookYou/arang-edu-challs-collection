# IDOR — 계좌 잔액 조회

| | |
|---|---|
| 버그클래스 | IDOR / BOLA |
| 난이도 | ★☆☆ |
| 포트 | 9301 |

## 학습 목표
잔액 조회가 `acct` 파라미터만 신뢰하고 소유자 검증을 하지 않는다. 금융권에서 가장 흔하고 치명적인 인가 결함.

## 실행
```bash
./gen_flags.sh
docker compose up -d --build idor-balance
# http://localhost:9301
```

## 진행
1. guest/guest 로그인 → 내 계좌 1001 조회.
2. `acct` 를 1000(admin) 으로 변경.
3. admin 계좌 메모에서 flag 획득.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
조회 대상 리소스의 소유자를 세션 사용자와 대조(서버측 인가), 추측 가능한 식별자 회피.
