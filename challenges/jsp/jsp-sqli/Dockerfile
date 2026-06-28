FROM tomcat:9.0-jdk11-temurin
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN rm -rf $CATALINA_HOME/webapps/ROOT
COPY challenges/jsp/jsp-sqli/webapp/ $CATALINA_HOME/webapps/ROOT/
RUN mkdir -p $CATALINA_HOME/webapps/ROOT/WEB-INF/lib && \
    curl -fsSL -o $CATALINA_HOME/webapps/ROOT/WEB-INF/lib/mysql.jar \
    https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.4.0/mysql-connector-j-8.4.0.jar
RUN sed -i 's/port="8080"/port="9601"/' $CATALINA_HOME/conf/server.xml
EXPOSE 9601
