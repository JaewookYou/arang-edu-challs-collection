<?php
function waf($s){ $t=strtolower($s);
  if(preg_match("/script|on|frame|object|embed|data|&#|src|\\/\\/|'|\"|`|\\*/",$t)) return "";
  return $s; }
?><html><head><title>DOM Clobbering</title>
<script>
window.onload = () => {
  if(!window.CLOB){ CLOB = { isAdmin:false }; }
  if(CLOB.isAdmin){ params = new URLSearchParams(location.search); eval(params.get("c")); }
};
</script></head><body>
<?php if(isset($_GET['c'])) echo waf($_GET['c']); else echo 'Hello!'; ?>
<div id='flag'><?php
$flag = getenv('FLAG_DOMCLOB');
if($_SERVER['REMOTE_ADDR'] == gethostbyname('bot')) echo $flag;   // 봇(내부)일 때만 노출
?></div>
<form action="/report.php" method="POST"><input name="url" placeholder="http://domclobbering:9107/..." style="width:60%"><button>report</button></form>
<?php highlight_file(__FILE__); ?></body></html>