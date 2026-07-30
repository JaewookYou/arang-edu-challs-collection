# -*- coding: utf-8 -*-
# XXE — 외부 엔티티 확장 허용. POST XML body 의 엔티티가 파일을 읽어 반영됨.
import os, stat
from flask import Flask, request
from lxml import etree
app = Flask(__name__)

# 주문 XML 은 원래 작다. 상한을 두면 'Content-Length 는 큰데 본문을 끝까지 안 보내는'
# 요청을 워커가 본문 다 읽기 전에 413 으로 끊는다(그런 요청이 스레드를 영구 점유해
# 문제 전체가 26시간 먹통이 된 적이 있다).
MAX_BODY = 256 * 1024
MAX_ENTITY = 64 * 1024
app.config["MAX_CONTENT_LENGTH"] = MAX_BODY

try:
    open("/flag.txt", "w").write(os.environ.get("FLAG_XXE_1", "flag{local}"))
except Exception:
    pass


class SafeFileResolver(etree.Resolver):
    """XXE 실습은 그대로 둔다(파일은 읽힌다). 다만 '영영 안 끝나는 대상' 만 막는다.
    디렉터리·장치·FIFO 를 엔티티로 열면 파서가 그 스레드를 붙잡고 안 돌아온다."""

    def resolve(self, url, pubid, context):
        path = url[7:] if url.startswith("file://") else (url if url.startswith("/") else None)
        if path is None:
            return None                       # 네트워크 등은 파서 기본 처리(no_network 로 차단)
        try:
            st = os.stat(path)
        except OSError:
            return None                       # 없는 경로는 평소대로 에러
        if not stat.S_ISREG(st.st_mode):
            return self.resolve_string(b"", context)      # 정규 파일이 아니면 빈 값
        try:
            with open(path, "rb") as f:
                return self.resolve_string(f.read(MAX_ENTITY), context)
        except OSError:
            return self.resolve_string(b"", context)

FORM = ('<h3>XML 주문 파서</h3>'
        '<p>아래에 XML 을 입력하고 보내면 서버가 파싱해 &lt;name&gt; 값을 되돌려줍니다.</p>'
        '<textarea id="xml" rows="8" style="width:80%;font-family:monospace">'
        '&lt;?xml version="1.0"?&gt;\n&lt;order&gt;&lt;name&gt;홍길동&lt;/name&gt;&lt;/order&gt;'
        '</textarea><br>'
        '<button onclick="send()">전송</button>'
        '<h4>응답</h4><pre id="out" style="background:#f4f4f4;padding:8px;min-height:1em"></pre>'
        '<script>'
        'async function send(){'
        ' const r=await fetch("/order",{method:"POST",'
        '  headers:{"Content-Type":"application/xml"},'
        '  body:document.getElementById("xml").value});'
        ' document.getElementById("out").textContent=await r.text();'
        '}'
        '</script>'
        '<p style="color:#888">또는 CLI: '
        '<code>curl -XPOST --data-binary @order.xml http://localhost:9208/order</code></p>')

@app.route("/")
def index():
    return FORM

@app.route("/order", methods=["POST"])
def order():
    data = request.get_data()
    try:
        parser = etree.XMLParser(resolve_entities=True, load_dtd=True, no_network=True)
        parser.resolvers.add(SafeFileResolver())
        doc = etree.fromstring(data, parser)   # XXE sink
        name = doc.findtext("name")
        return "주문자: " + (name or "?")
    except Exception as e:
        return "parse error: " + str(e), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9208)
