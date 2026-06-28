<?php
# flag 는 lfiflag.php 안에 있습니다 (그냥 include 하면 실행되어 안 보임 → 소스를 읽으세요)
if (!isset($_GET["p"])) { include 'home.php'; }
else { include $_GET["p"]; }   // LFI
?><hr><?php highlight_file(__FILE__); ?>