# SSRF — 내부망

| | |
|---|---|
| 버그클래스 | Server-Side Request Forgery |
| 난이도 | ★★★ |
| 포트 | 9502 |

## 학습 목표
`/fetch?url=` 가 스킴/호스트 검증 없이 서버측 요청을 만든다. `/internal/flag` 는 localhost 요청만 허용 → SSRF 로만 도달 가능.

## 실행
```bash
./gen_flags.sh
docker compose up -d --build ssrf-internal
# http://localhost:9502
```

## 진행
1. `/internal/flag` 직접 접근 → 403.
2. `/fetch?url=http://example.com` 정상 동작 확인.
3. `/fetch?url=http://127.0.0.1:9502/internal/flag` → 서버가 localhost 로 요청 → flag.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
URL 스킴/호스트 allow-list, 내부망/localhost 차단, 메타데이터 IP 차단, 리다이렉트 검증.
