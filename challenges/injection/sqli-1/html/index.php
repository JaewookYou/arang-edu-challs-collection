<?php include 'dbconn.php';
if (isset($_GET['userid']) && isset($_GET['userpw'])) {
    $m = new mysqli($host, $user, $pass, $db);
    if ($m->connect_error) die('db error');
    $q = "SELECT userid FROM sqli1_table WHERE userid='$_GET[userid]' AND userpw='$_GET[userpw]'";
    $r = $m->query($q); $uid = '';
    if ($r && $r->num_rows > 0) { while ($row = $r->fetch_assoc()) { $uid = $row['userid']; } }
    $m->close();
    if ($uid === 'admin') { echo getenv('FLAG_SQLI_1'); }
    else { echo htmlspecialchars($uid); }
}
?><hr><form>userid <input name=userid> userpw <input name=userpw> <button>login</button></form>
<?php highlight_file(__FILE__); ?>