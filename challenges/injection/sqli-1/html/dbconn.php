<?php
$host = getenv('DB_HOST') ?: 'db';
$db   = getenv('DB_NAME') ?: 'chall';
$user = getenv('DB_USER') ?: 'sqli';
$pass = getenv('DB_PASS') ?: 'sqlipw';
?>