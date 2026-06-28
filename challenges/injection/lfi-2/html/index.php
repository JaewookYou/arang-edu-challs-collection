<?php
    session_start();
    # /readflag 를 실행(RCE)해야 flag 가 나옵니다.
    if (!isset($_GET["p"])) { include 'home.php'; }
    else { $_SESSION["p"] = $_GET["p"]; include $_GET["p"]; }   // LFI + 입력을 세션에 저장
?><hr><?php highlight_file(__FILE__); ?>