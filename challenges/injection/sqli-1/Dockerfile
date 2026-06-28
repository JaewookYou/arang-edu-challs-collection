FROM php:8.1-apache
RUN docker-php-ext-install mysqli
RUN sed -i 's/80/9201/g' /etc/apache2/sites-enabled/000-default.conf /etc/apache2/ports.conf
COPY challenges/injection/sqli-1/html/ /var/www/html/
EXPOSE 9201
