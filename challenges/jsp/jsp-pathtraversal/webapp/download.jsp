<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.io.*" %>
<%
String f = request.getParameter("file");
if (f == null) { out.println("usage: ?file=report1.txt"); }
else {
    String base = application.getRealPath("/files/");
    File target = new File(base, f);   // 취약점: 경로 검증 없음 → ../ 로 상위 접근
    try (FileInputStream in = new FileInputStream(target)) {
        response.setContentType("text/plain");
        byte[] b = new byte[in.available()];
        in.read(b);
        out.print(new String(b));
    } catch (Exception e) { out.println("error: " + e.getMessage()); }
}
%>