#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

# Retrieve whole htrm document
base_path = "/home/jors/sources/proyectos/naufrago/samples"
post_id = "1"
full_path = base_path + "/" + post_id
url = "http://www.abc.es/20110328/local-castilla-leon/abci-tere-201103280754.html"
os.system("wget -q -p -k -nc -nd -P " + full_path + " " + url)

# Get the (only?) html file
if os.path.exists(full_path):
 for f in os.listdir(full_path):
  if f.lower().endswith('htm') or f.lower().endswith('html'):
   print f
