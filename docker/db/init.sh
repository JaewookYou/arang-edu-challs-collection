#!/bin/bash
set -e
mysql -uroot -p"$MYSQL_ROOT_PASSWORD" <<SQL
CREATE DATABASE IF NOT EXISTS chall;
CREATE USER IF NOT EXISTS 'sqli'@'%' IDENTIFIED BY 'sqlipw';
GRANT ALL PRIVILEGES ON chall.* TO 'sqli'@'%';
FLUSH PRIVILEGES;
USE chall;
CREATE TABLE IF NOT EXISTS sqli1_table(userid VARCHAR(64), userpw VARCHAR(128));
INSERT INTO sqli1_table VALUES('admin','s3cr3t_admin_pw_one'),('guest','guest');
CREATE TABLE IF NOT EXISTS sqli2_table(userid VARCHAR(64), userpw VARCHAR(128));
INSERT INTO sqli2_table VALUES('admin','s3cr3t_admin_pw_two'),('guest','guest');
CREATE TABLE IF NOT EXISTS sqli3_table(userid VARCHAR(64), userpw VARCHAR(128));
INSERT INTO sqli3_table VALUES('admin','${FLAG_SQLI_3}'),('guest','guest');
CREATE TABLE IF NOT EXISTS jsp_users(userid VARCHAR(64), userpw VARCHAR(128));
INSERT INTO jsp_users VALUES('admin','s3cr3t_jsp_admin'),('guest','guest');
SQL
echo "[db] init done"
