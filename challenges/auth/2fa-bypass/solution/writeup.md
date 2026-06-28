# [강사용] 2FA 우회 풀이
guest/guest 로그인 직후(stage='otp') OTP 입력 없이 `/secret` 직접 접근 → flag. /secret 가 'done' 이 아닌 'otp' 도 허용하는 게 버그.
