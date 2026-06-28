<?php
$dir = __DIR__.'/uploads';
@mkdir($dir, 0777, true);
if (!empty($_FILES['f']['name'])) {
    $name = basename($_FILES['f']['name']);
    // 허술한 확장자 검사: .php 만 차단 (.phtml/.php5/대소문자 우회 가능)
    if (preg_match('/\.php$/i', $name)) { echo "php 금지!"; }
    else {
        move_uploaded_file($_FILES['f']['tmp_name'], "$dir/$name");
        echo "업로드됨: <a href='uploads/$name'>uploads/$name</a>";
    }
}
?><hr><h3>이미지 업로드</h3>
<form method=post enctype=multipart/form-data><input type=file name=f><button>upload</button></form>
<p>flag 는 /flag_upload.txt 에 있습니다. (웹쉘로 읽으세요)</p>
<?php highlight_file(__FILE__); ?>