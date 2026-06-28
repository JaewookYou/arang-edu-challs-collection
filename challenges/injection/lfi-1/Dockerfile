# build context = repo root
FROM php:8.1-apache
RUN sed -i 's/80/9204/g' /etc/apache2/sites-enabled/000-default.conf /etc/apache2/ports.conf
COPY challenges/injection/lfi-1/html/ /var/www/html/
EXPOSE 9204
# 원본처럼 lfiflag.php 에 flag 를 박아 넣고(소스로만 읽힘) 구동
CMD bash -c 'printf "<?php\\n\$flag = \"%s\";\\n" "$FLAG_LFI_1" > /var/www/html/lfiflag.php && apache2-foreground'
