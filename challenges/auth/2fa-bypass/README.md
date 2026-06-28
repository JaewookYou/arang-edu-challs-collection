# 2차인증 검증 우회

| | |
|---|---|
| 버그클래스 | Improper Verification (2FA) |
| 난이도 | ★★☆ |
| 포트 | 9302 |

## 학습 목표
비밀번호 통과 후 OTP 단계가 있으나, 보호 자원(/secret)이 OTP 완료가 아닌 '비번 통과' 상태만 확인한다.

## 실행
```bash
./gen_flags.sh
docker compose up -d --build 2fa-bypass
# http://localhost:9302
```

## 진행
1. guest/guest 로그인 → OTP 단계로 이동(코드 모름).
2. OTP 를 풀지 않고 `/secret` 로 직접 접근.
3. 서버가 OTP 완료를 검증하지 않아 flag 노출.

> 참조 풀이: [`solution/writeup.md`](solution/writeup.md)

## 대응방안
최종 자원 접근 시 모든 인증 단계 완료 상태를 서버 세션으로 엄격 검증.
