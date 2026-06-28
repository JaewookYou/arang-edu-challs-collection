import java.io.*;
import javax.servlet.*;
import javax.servlet.http.*;
import javax.servlet.annotation.*;

@WebServlet("/upload")
@MultipartConfig
public class UploadServlet extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse res) throws IOException, ServletException {
        res.setContentType("text/html; charset=UTF-8");   // 한글 응답 깨짐 방지
        Part p = req.getPart("f");
        String name = p.getSubmittedFileName();
        // 허술한 검사: .jsp 만 차단 (.jspx 는 통과 → Tomcat이 실행)
        if (name.toLowerCase().endsWith(".jsp")) {
            res.getWriter().println("jsp 금지!");
            return;
        }
        String dir = getServletContext().getRealPath("/uploads");
        new File(dir).mkdirs();
        p.write(dir + File.separator + name);
        res.getWriter().println("업로드됨: <a href='uploads/" + name + "'>uploads/" + name + "</a>");
    }
}