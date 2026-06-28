# XSS #1 — 기본 (Stored XSS)

| | |
|---|---|
| 카테고리 | client |
| 버그클래스 | Cross-Site Scripting (Stored) |
| 난이도 | ★☆☆ |
| 봇 | 필요 (admin 방문) |
| 포트 | 9101 |

## 학습 목표
게시판 본문이 **escape 없이 출력(`|safe`)** 되는 Stored XSS를 이용해, 내부망에서 글을 열람하는 **admin 봇의 `flag` 쿠키**를 외부로 탈취한다. "사용자 입력 → 신뢰 → DOM 실행"의 기본기를 익힌다.

## 구성
이 폴더에는 **취약 설정(app.py) 한 파일**만 있다. 게시판 골격(가입/로그인/목록/작성/신고)은 `_base/flask_board` 가 제공한다. 취약점은 `render_safe=True`(본문 비escape 출력) + `content_filter=None`(필터 없음) 두 줄이 전부다.

## 실행
```bash
# 저장소 루트에서
./gen_flags.sh
docker compose up -d xss-1 bot platform   # 또는: make up-client
# 학습자 접속: http://localhost:9101  (스코어보드: http://localhost:9000)
```

## 진행
1. 회원가입 후 로그인.
2. 글쓰기에서 본문에 스크립트를 넣어 본다 → 보기 화면에서 그대로 실행되는지 확인.
3. 신고(report)에 **내부 URL**(`http://xss-1:9101/board/<번호>`)을 제출하면 admin 봇이 로그인 상태로 방문.
4. admin 의 `flag` 쿠키를 외부 수집기로 전송 → 플래그 획득 → 스코어보드(:9000)에 제출.

<details><summary>힌트</summary>

- 본문은 필터가 전혀 없다.
- admin 으로 로그인하면 `flag` 쿠키가 세팅된다(HttpOnly 아님 → `document.cookie` 로 접근 가능).
- 봇은 컨테이너 내부에서 도므로 URL의 host는 `localhost`가 아니라 서비스명 `xss-1` 을 써야 한다.
- 수집기는 봇 컨테이너에서 도달 가능해야 한다(호스트의 리스너 → `host.docker.internal` 또는 호스트 IP).
</details>

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md) (강사용)

## 대응방안
출력 시 컨텍스트에 맞는 escape(HTML 엔티티 인코딩), 프레임워크 자동 escape 유지(`|safe` 금지), 민감 쿠키는 `HttpOnly`, CSP 적용.
