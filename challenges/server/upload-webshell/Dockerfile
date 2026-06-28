FROM php:8.1-apache
RUN sed -i 's/80/9501/g' /etc/apache2/sites-enabled/000-default.conf /etc/apache2/ports.conf
# .phtml/.php5 를 PHP 로 실행하도록 전역 매핑 + 업로드 디렉터리 준비.
#  - 기존 방식(uploads/.htaccess 에 AddType)은 두 가지 이유로 동작 안 함:
#    (1) uploads/ 가 첫 요청 전엔 없어 컨테이너 기동 시 .htaccess 생성이 실패(생성 타이밍),
#    (2) Debian Apache 기본 AllowOverride None 이라 .htaccess 자체가 무시됨.
#  - 서버 설정(conf-enabled)의 SetHandler 로 대체하면 위 둘과 무관하게 .phtml 이 실행됨.
RUN printf '<FilesMatch "\\.(phtml|php5)$">\n  SetHandler application/x-httpd-php\n</FilesMatch>\n' \
        > /etc/apache2/conf-enabled/phtml-exec.conf \
 && mkdir -p /var/www/html/uploads && chown -R www-data:www-data /var/www/html/uploads
COPY challenges/server/upload-webshell/html/ /var/www/html/
EXPOSE 9501
CMD bash -c "echo \"$FLAG_UPLOAD\" > /flag_upload.txt && apache2-foreground"
