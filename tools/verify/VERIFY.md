# 풀이 동작 검증 결과 (solvability check)

샌드박스(파이썬/Node)에서 **실제 익스플로잇을 실행**해 flag 추출까지 확인. (docker 없이 in-process/HTTP·jsdom 사용)

## 결과 요약

| 문제 | 검증 방식 | 결과 |
|---|---|---|
| idor-balance | 실서버 + `?acct=1000` | ✅ flag 추출 |
| 2fa-bypass | 실서버 + OTP 없이 `/secret` | ✅ flag 추출 |
| ssti-1 | 실서버 + SSTI RCE(`$FLAG` 출력) | ✅ flag 추출 |
| cmdi-1 (Blind) | 실서버 + 파일 사이드이펙트 OOB | ✅ flag 추출 |
| xxe-1 | 실서버 + 외부엔티티 파일읽기 | ✅ flag 추출 |
| ssrf-internal | 실서버 + 자기 자신 내부엔드포인트 호출 | ✅ flag 추출 |
| race-transfer | 실서버 + 60 동시요청 경합 | ✅ flag 추출 |
| csrf-1 | 마크다운→img→changepw→admin탈취→/board/0 | ✅ flag 추출 |
| csrf-2 | csrf_token 누출→changepw→admin탈취→/board/0 | ✅ flag 추출 |
| xss-1 | jsdom 봇 + 쿠키탈취 페이로드 | ✅ 쿠키 flag 유출 |
| xss-3 | jsdom 봇 + 필터우회(Set.constructor)→/board/0 읽기 | ✅ flag 유출 |
| domclobbering | jsdom + 클로버링(eval→fetch) | ✅ flag 유출 (※ id 클로버링은 실브라우저 표준동작) |
| prototype-pollution | jsdom + `__proto__` 오염→eval | ✅ flag 유출 |
| xss-2 | 필터 통과/차단 검증 | ✅ iframe+엔티티 우회 통과(실행은 실브라우저) |
| xsleak | 전제조건(필터통과 style + admin flag href) | ✅ 전제 성립 (CSS char-leak은 실브라우저 CSS엔진 필요) |

## docker 빌드에서 확인 필요 (샌드박스에 PHP/MySQL/Tomcat 없음)
- sqli-1/2/3, lfi-1/2, upload-webshell : 표준 PHP 포팅(원본 기믹 그대로). `docker compose --profile injection up` 후 `문답해설.txt` 페이로드로 1회 점검 권장.

## 재현 방법
```bash
# 서버사이드 7종 (실제 flag 추출)
python3 tools/verify/verify_server.py
# 클라이언트 (jsdom 봇 JS 실행)
cd /tmp && npm install jsdom
python3 tools/verify/render_client.py
python3 - <<'PY'
import json,subprocess
for t in json.load(open("/tmp/client_tests.json")):
    print(t["name"], subprocess.run(["node","tools/verify/exfil_check.js",t["file"],t["cookie"],t["flag"],t["url"]],capture_output=True,text=True).stdout)
PY
```
