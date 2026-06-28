# 멀티스테이지: javac 로 서블릿 컴파일 후 tomcat 으로 서빙
FROM eclipse-temurin:11-jdk AS build
WORKDIR /b
COPY --from=tomcat:9.0-jdk11-temurin /usr/local/tomcat/lib/servlet-api.jar /b/servlet-api.jar
COPY challenges/jsp/jsp-upload/src/UploadServlet.java /b/
RUN javac -encoding UTF-8 -cp servlet-api.jar -d /classes UploadServlet.java

FROM tomcat:9.0-jdk11-temurin
RUN rm -rf $CATALINA_HOME/webapps/ROOT
COPY challenges/jsp/jsp-upload/webapp/ $CATALINA_HOME/webapps/ROOT/
COPY --from=build /classes/ $CATALINA_HOME/webapps/ROOT/WEB-INF/classes/
RUN sed -i 's/port="8080"/port="9602"/' $CATALINA_HOME/conf/server.xml
EXPOSE 9602
CMD bash -c 'echo "$FLAG_JSP_UPLOAD" > /flag && catalina.sh run'
