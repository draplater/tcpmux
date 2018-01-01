# tcpmux
```
usage: tcpmux.py [-h] --listen LISTEN [--ssh SSH] [--http HTTP] [--tls TLS] 
                 --other OTHER [--timeout TIMEOUT] [--buffer-size BUFFER_SIZE]

Use only one port to handle HTTP, TLS, SSH and unrecognized traffic.        

optional arguments:                   
  -h, --help            show this help message and exit                     
  --listen LISTEN       listen address                                      
  --ssh SSH             address to which SSH traffic will be forward        
  --http HTTP           address to which HTTP traffic will be forward       
  --tls TLS             address to which TLS traffic will be forward        
  --other OTHER         address to which unrecognized traffic will be forward
  --timeout TIMEOUT                   
  --buffer-size BUFFER_SIZE           
```

Python 3.6+ is required to run this program. [uvloop](https://pypi.python.org/pypi/uvloop) is recommend to get better performance.
