#!/bin/bash
set -e
wget https://saraksti.rigassatiksme.lv/riga/routes.txt -O routes.txt
wget https://saraksti.rigassatiksme.lv/riga/stops.txt -O stops.txt

wget https://www.marsruti.lv/rigasmikroautobusi/bbus/readfile.php?name=stops.txt -O stops-rms.txt
wget https://www.marsruti.lv/rigasmikroautobusi/bbus/readfile.php?name=routes.txt -O routes-rms.txt

./sample.py



