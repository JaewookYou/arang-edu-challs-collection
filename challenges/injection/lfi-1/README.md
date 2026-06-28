# LFI #1 — 기본

| | |
|---|---|
| 버그클래스 | Local File Inclusion |
| 난이도 | ★★☆ |
| 포트 | 9204 |

## 학습 목표
`include $_GET[p]` 가 임의 경로를 포함한다. php 파일은 그냥 include 하면 실행되어 소스가 안 보이므로 php://filter 로 소스를 base64 인코딩해 읽는다.

## 실행
```bash
./gen_flags.sh
make up-injection   # 또는: docker compose up -d --build lfi-1 db
# http://localhost:9204
```

## 진행
1. `?p=home.php` 정상 동작.
2. `?p=php://filter/convert.base64-encode/resource=config.php`.
3. base64 디코딩 → 주석 속 flag.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
include 대상은 화이트리스트/고정, 사용자 입력 경로 금지, allow_url_include off.
