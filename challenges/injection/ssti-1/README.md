# SSTI → RCE

| | |
|---|---|
| 버그클래스 | Server-Side Template Injection |
| 난이도 | ★★☆ |
| 포트 | 9207 |

## 학습 목표
`name` 이 템플릿 문자열에 직접 결합된다. `{{7*7}}` 로 평가 확인 후 RCE 가젯으로 파일 읽기.

## 실행
```bash
./gen_flags.sh
docker compose up -d --build ssti-1
# http://localhost:9207
```

## 진행
1. `name={{7*7}}` → 49 확인.
2. 가젯으로 os 접근.
3. `cat /flag.txt` 실행 → 플래그.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
사용자 입력은 템플릿 변수로만 전달(`render_template`+context), 문자열 결합 금지.
