# CSRF #1 — admin 비밀번호 변경

| | |
|---|---|
| 버그클래스 | CSRF |
| 난이도 | ★★☆ |
| 봇 | 필요 |
| 포트 | 9104 |

## 학습 목표
비밀번호 변경이 GET + 검증 없이 처리된다. 게시글에 `<img>` 태그를 심어 admin 봇이 열람할 때 변경을 유발한다.

## 실행
```bash
./gen_flags.sh
make up-client   # 또는: docker compose up -d --build csrf-1 bot platform
# http://localhost:9104
```

## 진행
1. `/changepw` 가 GET 으로 동작함을 확인.
2. 따옴표/script 는 필터됨 → `<img src=/changepw?userid=admin&userpw=pwned>` 작성.
3. 신고 → admin 봇 방문 시 변경 발동 → admin/pwned 로 로그인 → `/board/0` flag.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
CSRF 토큰, SameSite 쿠키, 상태변경은 POST + Referer 검증.
