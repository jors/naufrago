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

def rebuild_link(original_url, relative_link):
 """Builds an absolute link from a relative one."""
 clean_original_url = original_url.split("http://")[1] # http://blog.liw.fi/posts/obnam-0.16/ => blog.liw.fi/posts/obnam-0.16/
 original_url_split = clean_original_url.split("/") # blog.liw.fi/posts/obnam-0.16/ => ('blog.liw.fi', 'posts', 'obnam-0.16', '')
 original_url_split = filter(None, original_url_split)
 relative_link_split = relative_link.split("/") # ../../favicon.ico => ('..', '..', 'favicon.ico')
 for elem in relative_link_split:
  print 'elem: ' + elem
  if elem == '..':
   original_url_split = original_url_split[0:-1]
   print 'link: ' + `original_url_split`
  else:
   break
 print "Rebuild_link: reeturning " + "http://" + "/".join(original_url_split) + "/" + relative_link_split[-1]
 return "http://" + "/".join(original_url_split) + "/" + relative_link_split[-1]

def filter_needed_content(page, original_url):
 """Filter needed content."""
 # Obtain base url
 rgxp = '''(http|https)://+[^/]*?/'''
 m = re.search(rgxp, original_url)
 if m is not None:
  base_url = m.group(0)

 regexps = ('''<(link|script|img|iframe)\s+[^>]*?(href|src)=["]?([^">]+)[^>]*?>''', '''(url)\(('|")*([^\)]*?)('|")*\)''')
 url_list = [] # Dict for original urls
 url_mod_list = [] # Dict for modified urls
 rgxp_lap = 0
 for rgxp in regexps:
  tags = re.findall(rgxp, page, re.I)
  for tag in tags:
   if tag[2] != base_url and tag[2] != base_url[0:-1]:
    print "Detected " + `tag[2]`
    url_list.append(tag[2])
    if tag[2].startswith("http") or tag[2].startswith("https"): # Enlace absoluto
     url_mod_list.append(tag[2])
    else: # Enlace relativo. ¡Cabría recontruir el link!
     #url_mod_list.append(base_url + tag[2])
     if rgxp_lap == 0:
      url = rebuild_link(original_url, tag[2])
      url_mod_list.append(url)
     else:
      url_mod_list.append(base_url + tag[2])
  rgxp_lap += 1
 return page, url_list, url_mod_list

def retrieve_needed_content(url_mod_list):
 """Retrieve needed content (if not present already)."""
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
  else:
   print "Skipping " + full_path + filename + "..."
 return url_mod_list

def translate_document(page, url_list, f):
 """# Translate html document for local viewing."""
 url_list = set(url_list) # Remove duplicates
 for url in url_list:
  # Get file name to replace
  filename = get_filename(url)
  if url != filename:
   print "Reemplazamos '" + url + "' por '" + filename + "'."
   page = page.replace(url, filename)
  else:
   print "No hace falta reemplazar, skipping!"
 local_file = open(full_path + f, 'w')
 local_file.write(page)
 local_file.close()

full_path = "/home/jors/sources/proyectos/naufrago/samples/test/url_fetcher/"
#url = "http://www.abc.es/20110416/deportes-futbol/abci-futbol-real-madrid-barcelona-201104162226.html"
#url = "http://ciberderechos.barrapunto.com/ciberderechos/11/04/17/1251258.shtml"
#url = "http://m.menea.me/qfq6"
original_url = "http://blog.liw.fi/posts/obnam-0.16/"

# Retrieve main html document
if not os.path.exists(full_path + '1.html'):
 web_file = urlopen(original_url)
 local_file = open(full_path + '1.html', 'w')
 page = web_file.read()
 web_file.close()
 local_file.write(page)
 local_file.close()

try:
 # Filter needed content
 page, url_list, url_mod_list = filter_needed_content(page, original_url)
except:
 local_file = open(full_path + '1.html', 'r')
 page = local_file.read()
 local_file.close()
 page, url_list, url_mod_list = filter_needed_content(page, original_url)

# Retrieve needed content (if not present already)
url_mod_list = retrieve_needed_content(url_mod_list)
# Translate html document for local viewing
translate_document(page, url_list, '1.html')

for f in os.listdir(full_path):
 if f.endswith(".css"):
  local_file = open(full_path + f, 'r')
  page = local_file.read()
  local_file.close()
  page, url_list, url_mod_list = filter_needed_content(page, original_url)
  url_mod_list = retrieve_needed_content(url_mod_list)
  translate_document(page, url_list, f)

