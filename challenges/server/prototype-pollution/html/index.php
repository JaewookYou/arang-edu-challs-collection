<?php ?><html><head><title>Prototype Pollution</title>
<script>
function isObject(o){ return o!==null && typeof o==='object'; }
function merge(a,b){ for(let k in b){ if(isObject(a[k])&&isObject(b[k])) merge(a[k],b[k]); else a[k]=b[k]; } return a; }
CLOB = { name:'arang' };
window.onload = () => {
  params = new URLSearchParams(location.search);
  try { c = JSON.parse(params.get("c")); merge(CLOB, c); } catch(e){}
  document.getElementById('name').innerText = `Hello ${CLOB.name}`;
  if(CLOB.isAdmin){ eval(CLOB.code); }
};
</script></head><body>
<div id='name'></div>
<div id='flag'><?php $flag=getenv('FLAG_PROTO'); if($_SERVER['REMOTE_ADDR']==gethostbyname('bot')) echo $flag; ?></div>
<form action="/report.php" method="POST"><input name="url" placeholder="http://prototype-pollution:9503/..." style="width:60%"><button>report</button></form>
<?php highlight_file(__FILE__); ?></body></html>