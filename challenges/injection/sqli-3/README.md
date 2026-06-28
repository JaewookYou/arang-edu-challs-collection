# SQLi #3 — Blind

| | |
|---|---|
| 버그클래스 | Blind SQL Injection |
| 난이도 | ★★★ |
| 포트 | 9203 |

## 학습 목표
로그인 성공/실패만 구분된다(Blind). 참/거짓 조건으로 admin 비밀번호(=flag)를 한 글자씩 추출.

## 실행
```bash
./gen_flags.sh
make up-injection   # 또는: docker compose up -d --build sqli-3 db
# http://localhost:9203
```

## 진행
1. `userid=admin'and(substr(userpw,1,1)='f')#` 식 참/거짓 관찰(WAF 우회 필요).
2. 길이만큼 반복 → 비밀번호 복원.
3. 복원한 값이 flag.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
Prepared Statement, 일정한 응답(타이밍/메시지 차이 제거).
