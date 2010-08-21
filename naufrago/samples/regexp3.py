#!/usr/bin/env python
# -*- coding: utf-8 -*-

#<img\s+                         # start of the tag
#[^>]*?                          # any attributes that precede the src
#src=                            # start of the src attribute
#(?P<quote>["'])?                # optional opening quote
#(?P<image>[^"'>]+)              # image filename
#(?(quote)(?P=quote))            # closing quote (matches opening quote if given)
#[^>]*?                          # any attributes that follow the src
#>                               # end of the tag

import re

#rgxp = '''<img\s+[^>]*?src=(?P<quote>["'])?(?P<image>[^"'>]+)(?(quote)(?P=quote))[^>]*?>'''
rgxp = '''<img\s+[^>]*?src=["']?([^"'>]+)[^>]*?>'''
text = "This is an <IMG alt=\"Imagen de nada\" src=\"fotoprix.jpg\" width=\"100\" /> tag, and this is another <img src=\"http://img.dominio.net/slurp/77777.0/j5.gif\" />!"

#m = re.search(rgxp, text)
#if m is not None:
# print m.group(1)

m = re.findall(rgxp, text, re.I)
#print m
for img in m:
 print img

