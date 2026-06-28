<?php
if(isset($_POST['url'])){
  $ch=curl_init(getenv('BOT_URL')?:'http://bot:9099/visit');
  curl_setopt($ch,CURLOPT_POST,true);
  curl_setopt($ch,CURLOPT_POSTFIELDS,http_build_query(['chal'=>'domclobbering','url'=>$_POST['url']]));
  curl_setopt($ch,CURLOPT_RETURNTRANSFER,true);
  curl_exec($ch); curl_close($ch);
  echo "reported";
} ?>