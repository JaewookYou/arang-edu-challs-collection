# SQLi #2 — 필터 우회

| | |
|---|---|
| 버그클래스 | SQL Injection (WAF bypass) |
| 난이도 | ★★☆ |
| 포트 | 9202 |

## 학습 목표
or/union/admin/숫자/공백/슬래시 등이 차단된다. 주석개행(%0a)·괄호·`concat`·`like` 등으로 우회.

## 실행
```bash
./gen_flags.sh
make up-injection   # 또는: docker compose up -d --build sqli-2 db
# http://localhost:9202
```

## 진행
1. WAF 가 막는 키워드 파악.
2. 공백 대신 `%0a`, admin 은 `concat('ad','min')` 등으로 구성.
3. 예: `userid=a'='a'%23%0aand%23%0auserid=concat('ad','min')%23`.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
블랙리스트 WAF 대신 Prepared Statement.
