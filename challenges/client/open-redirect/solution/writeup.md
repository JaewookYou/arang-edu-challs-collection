# [강사용] Open Redirect 풀이

검사: `url.startswith('/') or 'localhost' in url`.
- `next=//evil.com` → `/` 로 시작하므로 통과, 브라우저는 `//evil.com` 을 프로토콜-상대 외부 URL 로 해석.
- 또는 `next=https://localhost.evil.com/` → 'localhost' 포함으로 통과하지만 실제 호스트는 evil.com.

`/go?next=//evil.com` 호출 시 응답 본문에 flag 노출.
