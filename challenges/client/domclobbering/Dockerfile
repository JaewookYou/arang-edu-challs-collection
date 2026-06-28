FROM php:8.1-apache
RUN sed -i 's/80/9107/g' /etc/apache2/sites-enabled/000-default.conf /etc/apache2/ports.conf
COPY challenges/client/domclobbering/html/ /var/www/html/
EXPOSE 9107
