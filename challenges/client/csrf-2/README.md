# CSRF #2 — 토큰 누출 체이닝

| | |
|---|---|
| 버그클래스 | CSRF + XSS |
| 난이도 | ★★★ |
| 봇 | 필요 |
| 포트 | 9105 |

## 학습 목표
`/changepw` 가 CSRF 토큰을 요구한다. XSS로 admin 권한에서 토큰을 읽어 changepw를 호출하는 2단 체이닝.

## 실행
```bash
./gen_flags.sh
make up-client   # 또는: docker compose up -d --build csrf-2 bot platform
# http://localhost:9105
```

## 진행
1. `/changepw` 페이지에 csrf_token 이 박혀있음.
2. XSS(백틱 기법)로 admin 권한에서 `/changepw` 를 읽어 토큰 파싱.
3. 같은 스크립트로 `/changepw?...&csrf_token=` 호출 → admin 탈취 → `/board/0`.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
토큰 + SameSite + XSS 차단(출력 escape, CSP).
