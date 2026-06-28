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
        '<p>POST 로 XML 을 보내면 &lt;name&gt; 값을 되돌려줍니다.</p>'
        '<pre>curl -XPOST --data-binary @order.xml http://localhost:9208/order</pre>')

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
