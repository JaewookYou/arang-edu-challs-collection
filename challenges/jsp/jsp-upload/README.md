# JSP — File Upload

| | |
|---|---|
| 버그클래스 | File Upload (RCE) |
| 언어 | JSP / Tomcat |
| 난이도 | ★★☆ |
| 포트 | 9602 |

## 학습 목표
`.jsp` 만 차단하는 허술한 검사. `.jspx`(JSP document) 로 우회 업로드 → Tomcat이 실행 → 웹쉘 RCE.

## 실행
```bash
./gen_flags.sh
make up-jsp   # 또는: docker compose up -d --build jsp-upload
# http://localhost:9602
```

## 진행
1. `.jspx` 웹쉘 업로드(아래 풀이).
2. `uploads/shell.jspx?c=cat /flag` 접근.
3. flag 획득.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
확장자 화이트리스트, 업로드 경로 실행권한 제거, 랜덤 파일명, 별도 스토리지.
