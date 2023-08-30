#!/bin/bash
git clone https://github.com/data-for-change/anyway-newsflash-infographics.git
sed -i 's#https://www.anyway.co.il/#http://localhost:8080/#g' ./anyway-newsflash-infographics/.env
sed -i 's#https://dev.anyway.co.il/#http://localhost:8080/#g' ./anyway-newsflash-infographics/.env
