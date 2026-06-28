# [강사용] SSRF 풀이
`/fetch?url=http://127.0.0.1:9502/internal/flag` → 서버가 자기 자신(localhost)으로 요청하여 내부 전용 flag 반환. (gopher/파일 스킴 확장도 강의에서 다룸)
