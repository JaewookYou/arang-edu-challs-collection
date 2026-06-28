# XSS #3 — flag 게시글 읽기

| | |
|---|---|
| 버그클래스 | XSS (strong filter) |
| 난이도 | ★★★ |
| 봇 | 필요 |
| 포트 | 9103 |

## 학습 목표
괄호·따옴표·주요 키워드가 막힌 상태에서 무괄호/백틱 기법으로 스크립트를 실행, admin 권한으로 `/board/0`(flag)을 읽어 외부 전송.

## 실행
```bash
./gen_flags.sh
make up-client   # 또는: docker compose up -d --build xss-3 bot platform
# http://localhost:9103
```

## 진행
1. 0번 글은 admin 소유 → 일반 유저는 view 불가.
2. 필터를 우회하는 XSS 작성(괄호·따옴표 없이).
3. admin 봇이 글 열람 시 `/board/0` fetch → 외부 전송.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
출력 escape, CSP, 민감정보의 클라이언트 노출 최소화.
