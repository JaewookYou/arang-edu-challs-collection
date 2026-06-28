# 멀티스테이지: javac 로 서블릿 컴파일 → tomcat 으로 서빙 (WEB-INF/classes 에 .class 배치)
FROM eclipse-temurin:11-jdk AS build
WORKDIR /b
COPY --from=tomcat:9.0-jdk11-temurin /usr/local/tomcat/lib/servlet-api.jar /b/servlet-api.jar
COPY challenges/capstone/jsp-chain/src/ /b/src/
RUN mkdir /classes && javac -encoding UTF-8 -cp servlet-api.jar -d /classes $(find /b/src -name '*.java')

FROM tomcat:9.0-jdk11-temurin
RUN rm -rf $CATALINA_HOME/webapps/ROOT
COPY challenges/capstone/jsp-chain/webapp/ $CATALINA_HOME/webapps/ROOT/
COPY --from=build /classes/ $CATALINA_HOME/webapps/ROOT/WEB-INF/classes/
RUN sed -i 's/port="8080"/port="9711"/' $CATALINA_HOME/conf/server.xml
EXPOSE 9711
# flag 는 런타임 env 에서 /flag 로 (RCE 로만 읽힘)
CMD bash -c 'echo "$FLAG_JSP_CHAIN" > /flag && catalina.sh run'
