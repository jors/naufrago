#!/usr/bin/env python
# -*- coding: utf-8 -*-

url = 'http://enchufado.com/test/lastfile.php'
split = url.split("/")
favicon_url = split[0]+'//'+split[1]+split[2]+'/favicon.ico'
print favicon_url
