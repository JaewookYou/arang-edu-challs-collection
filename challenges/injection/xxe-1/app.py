# -*- coding: utf-8 -*-
# XXE — 외부 엔티티 확장 허용. POST XML body 의 엔티티가 파일을 읽어 반영됨.
import os
from flask import Flask, request
from lxml import etree
app = Flask(__name__)
try:
    open("/flag.txt", "w").write(os.environ.get("FLAG_XXE_1", "flag{local}"))
except Exception:
    pass

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
        doc = etree.fromstring(data, parser)   # XXE sink
        name = doc.findtext("name")
        return "주문자: " + (name or "?")
    except Exception as e:
        return "parse error: " + str(e), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9208)
