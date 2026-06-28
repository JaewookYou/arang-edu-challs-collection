# JSP — Path Traversal

| | |
|---|---|
| 버그클래스 | Path Traversal |
| 언어 | JSP / Tomcat |
| 난이도 | ★★☆ |
| 포트 | 9603 |

## 학습 목표
`download.jsp?file=` 가 경로를 검증하지 않는다. WEB-INF 는 웹 직접접근이 금지되지만 경로조작으로 읽을 수 있다.

## 실행
```bash
./gen_flags.sh
make up-jsp   # 또는: docker compose up -d --build jsp-pathtraversal
# http://localhost:9603
```

## 진행
1. `?file=report1.txt` 정상.
2. `?file=../WEB-INF/flag.txt` → flag.
3. `?file=../WEB-INF/web.xml` 등 내부 파일도 노출(캡스톤 빌드업).

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
정규화 후 화이트리스트 경로 검사, WEB-INF 접근 차단, 사용자 입력 경로 금지.
