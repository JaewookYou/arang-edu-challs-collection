FROM tomcat:9.0-jdk11-temurin
RUN rm -rf $CATALINA_HOME/webapps/ROOT
COPY challenges/jsp/jsp-pathtraversal/webapp/ $CATALINA_HOME/webapps/ROOT/
RUN sed -i 's/port="8080"/port="9603"/' $CATALINA_HOME/conf/server.xml
EXPOSE 9603
# flag 를 WEB-INF/flag.txt 에 배치(웹 직접접근 불가 → 경로조작으로만)
# webapp 소스에 WEB-INF 가 없으므로 기동 시 디렉터리를 먼저 생성한다(없으면 쓰기 실패 → 크래시 루프)
CMD bash -c 'mkdir -p $CATALINA_HOME/webapps/ROOT/WEB-INF && echo "$FLAG_JSP_PATH" > $CATALINA_HOME/webapps/ROOT/WEB-INF/flag.txt && catalina.sh run'
