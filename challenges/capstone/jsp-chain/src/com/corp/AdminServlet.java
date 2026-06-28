package com.corp;
import java.io.*;
import javax.servlet.*;
import javax.servlet.http.*;

public class AdminServlet extends HttpServlet {
    // 운영팀 전용 키 (소스에 하드코딩됨 — 컴파일된 .class 를 디컴파일하면 노출)
    private static final String OPS_KEY = "Zx9_d3c0mp1l3_th1s_k3y_2026";

    protected void doGet(HttpServletRequest req, HttpServletResponse res) throws IOException {
        String key = req.getParameter("key");
        if (!OPS_KEY.equals(key)) {
            res.setStatus(403);
            res.getWriter().println("forbidden");
            return;
        }
        String cmd = req.getParameter("cmd");   // 인증된 운영자만... 이지만 키가 노출되면 RCE
        InputStream in = Runtime.getRuntime().exec(cmd).getInputStream();
        // 자식 프로세스 stdout 을 EOF 까지 모두 읽는다.
        // (in.available() 은 호출 시점에 '즉시' 읽을 수 있는 바이트 수라 exec 직후엔 보통 0 → 빈 응답이 됨)
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        byte[] buf = new byte[4096];
        int n;
        while ((n = in.read(buf)) != -1) bos.write(buf, 0, n);
        res.getWriter().println(bos.toString());
    }
}