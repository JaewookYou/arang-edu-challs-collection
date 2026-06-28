# XXE

| | |
|---|---|
| 버그클래스 | XML External Entity |
| 난이도 | ★★☆ |
| 포트 | 9208 |

## 학습 목표
XML 파서가 외부 엔티티를 확장한다. SYSTEM 엔티티로 로컬 파일을 읽어 응답에 반영.

## 실행
```bash
./gen_flags.sh
docker compose up -d --build xxe-1
# http://localhost:9208
```

## 진행
1. 정상 XML `<order><name>홍길동</name></order>` 전송.
2. DOCTYPE 으로 SYSTEM 엔티티 정의.
3. `&xxe;` 를 name 에 넣어 /flag.txt 유출.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
외부 엔티티/DTD 비활성화(`resolve_entities=False`, `no_network=True`, DTD 금지).
