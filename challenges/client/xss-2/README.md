# XSS #2 — 필터 우회

| | |
|---|---|
| 버그클래스 | XSS (filter bypass) |
| 난이도 | ★★☆ |
| 봇 | 필요 |
| 포트 | 9102 |

## 학습 목표
`onerror=`, `<script` 등 '정확히 일치'만 막는 블랙리스트의 허점(공백/탭/대소문자/엔티티)을 우회한다.

## 실행
```bash
./gen_flags.sh
make up-client   # 또는: docker compose up -d --build xss-2 bot platform
# http://localhost:9102
```

## 진행
1. 글쓰기에 페이로드를 넣어 필터에 막히는 패턴을 파악.
2. `onerror=` 사이에 탭/개행을 넣거나 HTML 엔티티로 우회.
3. 신고로 admin 봇 방문 → `document.cookie` 외부 전송.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
블랙리스트가 아닌 출력 escape(화이트리스트), HttpOnly 쿠키, CSP.
