#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from urllib2 import urlopen
import re

def get_filename(url):
 i = -1
 filename = url.split("/")[i]
 while filename == '':
  i -= 1
  filename = url.split("/")[i]
 return filename

full_path = "/home/jors/sources/proyectos/naufrago/samples/1/"
url = "http://www.abc.es/20110328/local-castilla-leon/abci-tere-201103280754.html"

# Obtain base url
rgxp = '''(http|https)://+[^/]*?/'''
m = re.search(rgxp, url)
if m is not None:
 base_url = m.group(0)

# Retrieve html document
web_file = urlopen(url)
local_file = open(full_path + '1.html', 'w')
page = web_file.read()
web_file.close()
local_file.write(page)
local_file.close()
# Filter needed content
rgxp = '''<(link|script|img|iframe)\s+[^>]*?(href|src)=["]?([^">]+)[^>]*?>'''
tags = re.findall(rgxp, page, re.I)
url_list = []
url_mod_list = []
for tag in tags:
 url_list.append(tag[2])
 if tag[2].startswith("http") or tag[2].startswith("https"):
  url_mod_list.append(tag[2])
 else:
  url_mod_list.append(base_url + tag[2])

# Retrieve needed content (if not present already)
url_mod_list = set(url_mod_list) # Remove duplicates
for url in url_mod_list:
 # Get file name to save
 filename = get_filename(url)
 if not os.path.exists(full_path + filename):
  print "Retrieving " + full_path + filename + "..."
  print "(" + url + ")"
  try:
   web_file = urlopen(url)
   # Chunk filename if it is too large!
   if len(filename) > 256:
    m = re.search('[^?=&]+', filename)
    filename = m.group(0)
   local_file = open(full_path + filename, 'w')
   local_file.write(web_file.read())
   local_file.close()
   web_file.close()
  except:
   print "Oops!"
   pass
 else:
  print "Skipping " + full_path + filename + "..."

# Translate html document for local viewing
url_list = set(url_list) # Remove duplicates
for url in url_list:
 # Get file name to replace
 filename = get_filename(url)
 print "Reemplazamos '" + url + "' por '" + filename + "'."
 page = page.replace(url, filename)
local_file = open(full_path + '1.html', 'w')
local_file.write(page)
local_file.close()

