<?php include 'dbconn.php';
function waf($s){ $t=strtolower($s);
  if(preg_match("/or|union|admin|\\||\\&|\\d|-|\\\\|\\x09|\\x0b|\\x0c|\\x0d|\\x20|\\//",$t)) die('no hack..');
  return $s; }
if (isset($_GET['userid']) && isset($_GET['userpw'])) {
    $m = new mysqli($host, $user, $pass, $db);
    if ($m->connect_error) die('db error');
    $uid = waf($_GET['userid']); $upw = waf($_GET['userpw']);
    $q = "SELECT userid FROM sqli3_table WHERE userid='$uid' AND userpw='$upw'";
    $r = $m->query($q); $u = '';
    if ($r && $r->num_rows > 0) { while ($row = $r->fetch_assoc()) { $u = $row['userid']; break; } }
    $m->close();
    if ($u === 'admin') { echo 'Hello admin'; } else if ($u) { echo 'Hello '.htmlspecialchars($u); } else { echo 'login fail'; }
}
?><hr><p>admin 의 비밀번호가 곧 flag 입니다. (Blind)</p>
<form>userid <input name=userid> userpw <input name=userpw> <button>login</button></form>
<?php highlight_file(__FILE__); ?>