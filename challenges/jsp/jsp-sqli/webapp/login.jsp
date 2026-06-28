<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.sql.*" %>
<%
String uid = request.getParameter("userid");
String upw = request.getParameter("userpw");
if (uid != null && upw != null) {
    Class.forName("com.mysql.cj.jdbc.Driver");
    String url = "jdbc:mysql://" + System.getenv().getOrDefault("DB_HOST","db") + ":3306/chall";
    Connection con = DriverManager.getConnection(url, "sqli", "sqlipw");
    Statement st = con.createStatement();
    // 취약점: 사용자 입력이 쿼리에 그대로 결합
    String q = "SELECT userid FROM jsp_users WHERE userid='" + uid + "' AND userpw='" + upw + "'";
    String res = "";
    try {
        ResultSet rs = st.executeQuery(q);
        if (rs.next()) res = rs.getString(1);
    } catch (Exception e) { out.println("query error"); }
    con.close();
    if ("admin".equals(res)) out.println(System.getenv("FLAG_JSP_SQLI"));
    else out.println("hello " + (res.isEmpty() ? "guest" : res));
}
%>