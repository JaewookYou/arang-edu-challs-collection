# build context = repo root
FROM php:8.1-apache
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev && rm -rf /var/lib/apt/lists/*
RUN sed -i 's/80/9205/g' /etc/apache2/sites-enabled/000-default.conf /etc/apache2/ports.conf
COPY challenges/injection/lfi-2/html/ /var/www/html/
EXPOSE 9205
# 원본처럼 flag 를 박은 /readflag 바이너리(실행전용 chmod 111) 생성 후 구동
CMD bash -c 'printf "#include <stdio.h>\\nint main(){puts(\"%s\");}" "$FLAG_LFI_2" > /tmp/r.c && gcc -o /readflag /tmp/r.c && chmod 111 /readflag && apache2-foreground'
