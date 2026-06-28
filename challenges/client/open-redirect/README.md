# Open Redirect

| | |
|---|---|
| 버그클래스 | Open Redirection |
| 난이도 | ★☆☆ |
| 봇 | 불필요 |
| 포트 | 9108 |

## 학습 목표
`next` 파라미터의 same-site 검사가 'localhost 포함' 또는 '/ 시작'만 본다. `//`·`/\\`·`localhost.evil.com` 등으로 우회.

## 실행
```bash
./gen_flags.sh
make up-client   # 또는: docker compose up -d --build open-redirect bot platform
# http://localhost:9108
```

## 진행
1. `/go?next=/welcome` 정상 동작 확인.
2. 검사 로직(`localhost` 포함/`/`시작)의 허점 파악.
3. `next=//evil.com` 또는 `next=https://localhost.evil.com/` 으로 외부 이동 성공 → flag.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
리다이렉트 대상은 허용목록(allow-list)으로 검증, 상대경로만 허용.
