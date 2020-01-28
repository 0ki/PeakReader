# PeakReader

This software allows reading routes.txt / stops.txt from software used by many municipalities and companies in the Baltic, Nording and Eastern European region.

This includes:
 * https://saraksti.rigassatiksme.lv
 * https://www.marsruti.lv
 * https://www.stops.lt
 * https://transport.tallinn.ee/
 * and many others
 

Usage example, also see sample.py.
```
from PeakWeb import PeakWebFileReader
pw = PeakWebFileReader("routes.txt","stops.txt")
print (pw.stops)
```


Copyright [Kirils Solovjovs](https://twitter.com/KirilsSolovjovs/), https://kirils.org/
