# Prototype Pollution

| | |
|---|---|
| 버그클래스 | Prototype Pollution |
| 난이도 | ★★★ |
| 포트 | 9503 |

## 학습 목표
사용자 JSON 이 재귀 merge 되어 `__proto__` 오염이 가능하다. 미초기화된 `isAdmin`/`code` 를 프로토타입으로 위조해 eval 발동.

## 실행
```bash
./gen_flags.sh
make up-injection   # 또는: docker compose up -d --build prototype-pollution db
# http://localhost:9503
```

## 진행
1. `c={"__proto__":{"isAdmin":true,"code":"..."}}`.
2. code 에 flag(div#flag) 외부 전송 JS.
3. report 로 봇 방문 → 유출.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
merge 시 __proto__/constructor 키 차단, Object.create(null), 스키마 검증.
