# DOM Clobbering

| | |
|---|---|
| 버그클래스 | DOM Clobbering |
| 난이도 | ★★☆ |
| 포트 | 9107 |

## 학습 목표
`window.CLOB.isAdmin` 검증을 HTML 요소(id/name)로 덮어써(clobbering) 참으로 만든다. WAF 가 script/따옴표 등을 막아 무괄호 기법 필요.

## 실행
```bash
./gen_flags.sh
make up-injection   # 또는: docker compose up -d --build domclobbering db
# http://localhost:9107
```

## 진행
1. `<form id=CLOB><input id=isAdmin>` 주입으로 CLOB.isAdmin truthy.
2. `c` 파라미터에 무따옴표/무괄호 JS 로 flag(div#flag) 외부 전송.
3. report 로 봇 방문 → 봇 화면에서만 flag 가 보임.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
DOMPurify 로 id/name 제거, 사용 전 변수 초기화, eval 제거.
