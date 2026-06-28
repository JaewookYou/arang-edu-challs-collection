package com.corp;
import java.io.*;
import javax.servlet.*;
import javax.servlet.http.*;

public class DownloadServlet extends HttpServlet {
    protected void doGet(HttpServletRequest req, HttpServletResponse res) throws IOException {
        String f = req.getParameter("file");
        if (f == null) { res.getWriter().println("usage: /download?file=docs/readme.txt"); return; }
        String base = getServletContext().getRealPath("/");
        File t = new File(base, f);   // 취약점: 경로 정규화/검증 없음 → ../, WEB-INF 접근 가능
        try (FileInputStream in = new FileInputStream(t)) {
            res.setContentType("application/octet-stream");
            byte[] b = new byte[in.available()];
            in.read(b);
            res.getOutputStream().write(b);
        } catch (Exception e) {
            res.getWriter().println("error: " + e.getMessage());
        }
    }
}