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

def get_base_url(original_url):
 # Obtain base url
 rgxp = '''(http|https)://+[^/]*?/'''
 m = re.search(rgxp, original_url)
 if m is not None:
  base_url = m.group(0)
 else:
  base_url = original_url
 return base_url

def remove_invalid_elements(s):
 if s.find(""): return True
 elif s.find("."): return True
 elif s.find(".."): return True
 else: return False

def rebuild_link(original_url, relative_link, url_mod_list):
 """Builds an absolute link from a relative one."""
 original_url2 = original_url.split("http://")[1] # http://blog.liw.fi/posts/obnam-0.16/ => blog.liw.fi/posts/obnam-0.16/
 original_url_split = original_url2.split("/") # blog.liw.fi/posts/obnam-0.16/ => ('blog.liw.fi', 'posts', 'obnam-0.16', '')
 copy_of_clean_original_url_split = clean_original_url_split = filter(None, original_url_split)
 relative_link_split = relative_link.split("/") # ../../favicon.ico => ('..', '..', 'favicon.ico')
 clean_relative_link_split = filter(None, relative_link_split)

 if clean_relative_link_split[0] != "." and clean_relative_link_split[0] != "..":
  #a = "http://" + "/".join(copy_of_clean_original_url_split)
  #b = "/".join(clean_relative_link_split)
  #if a.endswith("/") or b.startswith("/"):
  # final_url = a + b
  #else:
  # final_url = a + "/" + b
  #url_mod_list.append(final_url)
  #print 'Rebuilt_link (A): ' + final_url
  # NEW
  a = base_url = get_base_url(original_url)
  b = "/".join(clean_relative_link_split)
  if a.endswith("/") or b.startswith("/"):
   final_url = a + b
  else:
   final_url = a + "/" + b
  url_mod_list.append(final_url)
  print 'Rebuilt_link (A): ' + final_url
  # NEW
 else:
  for elem in clean_relative_link_split:
   if elem == ".": # ./archivo.html
    clean_relative_link_split.remove(elem)
   elif elem == "..": # ../archivo.html
    clean_relative_link_split.remove(elem)
    copy_of_clean_original_url_split = copy_of_clean_original_url_split.pop()

  a = "http://" + "/".join(copy_of_clean_original_url_split)
  b = "/".join(clean_relative_link_split)
  if a.endswith("/") or b.startswith("/"):
   final_url = a + b
  else:
   final_url = a + "/" + b
  url_mod_list.append(final_url)
  print 'Rebuilt_link (B): ' + final_url

 base_url = get_base_url(original_url)
 alt_final_url = base_url + b
 url_mod_list.append(alt_final_url)
 print 'Rebuilt_link (C): ' + alt_final_url

 return url_mod_list

def filter_needed_content(page, original_url):
 """Obtains the needed content to correctly show a page offline."""
 # Obtain base url
 base_url = get_base_url(original_url)
 regexps = ('''<(link|script|img|iframe)\s+[^>]*?(href|src)=["]?([^">]+)[^>]*?>''', '''(url)\(('|")*([^\)]*?)('|")*\)''')
 url_list = [] # Dict for original urls
 url_mod_list = [] # Dict for modified urls
 for rgxp in regexps:
  tags = re.findall(rgxp, page, re.I)
  for tag in tags:
   if tag[2] != base_url and tag[2] != base_url[0:-1]:
    print "Detected " + `tag[2]`
    url_list.append(tag[2])
    if tag[2].startswith("http") or tag[2].startswith("https"): # Enlace absoluto
     url_mod_list.append(tag[2])
    else: # Enlace relativo. ¡Cabría recontruir el link!
     url_mod_list = rebuild_link(original_url, tag[2], url_mod_list)
 return page, url_list, url_mod_list

def retrieve_needed_content(url_mod_list):
 """Retrieves the content chosen from the filter content (if not present already)."""
 url_mod_list = set(url_mod_list) # Remove duplicates
 for url in url_mod_list:
  # Get file name to save
  filename = get_filename(url)
  if not os.path.exists(full_path + filename):
   print "Retrieving " + url + "..."
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
    print "Done!"
    # TODO: Guardado en bd.
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
#original_url = "http://www.abc.es/20110418/internacional/abci-muertos-siria-201104181802.html"
#original_url = "http://eventos.barrapunto.com/eventos/11/04/18/0746236.shtml"
#original_url = "http://m.menea.me/qg9r"
#original_url = "http://www.elperiodico.com/es/noticias/internacional/bruselas-avala-decision-francia-bloquear-trenes-con-inmigrantes-llegados-italia-977794"
#original_url = "http://www.lavanguardia.es/sucesos/20110419/54141960580/un-incendio-en-la-sagrada-familia-obliga-a-su-desalojo.html"
#original_url = "http://enchufado.com/post.php?ID=339"
#original_url = "http://www.burtonini.com/blog/computers/synergy-2011-04-19-12-00"
#original_url = "http://www.elmundo.es/elmundo/2011/04/19/internacional/1303221837.html"
#original_url = "http://www.cuantocabron.com/yao/ponerse-en-forma"
#original_url = "http://es.engadget.com/2011/04/19/como-borrar-un-cd-con-electricidad-y-no-morir-en-el-intento/"
#original_url = "http://www.elpais.com/articulo/internacional/Gobierno/sirio/deroga/Ley/Emergencia/vigente/1963/elpepuint/20110419elpepuint_2/Tes"
#original_url = "http://www.vistoenfb.com/otros/si-salen-en-la-biblia-y-todo"
#original_url = "http://www.rubenortiz.es/2011/04/18/centos-5-instalar-nginx-desde-codigo-fuente/"
#original_url = "http://www.kriptopolis.org/dni-electronico-para-torpes"
#original_url = "http://foro.elhacker.net/noticias/stresslinux_07105-t325079.0.html"
#original_url = "http://blog.48bits.com/2011/04/15/un-reloj-de-dos-colores/"
#original_url = "http://www.sahw.com/wp/archivos/2011/04/14/analisis-forense-de-sistemas-de-ficheros-ufs-particionado-bsd386/"
#original_url = "http://www.elladodelmal.com/2011/04/el-ocr-scanning-y-la-piel-del-tarnbor.html"
#original_url = "http://www.securitybydefault.com/2011/04/mitos-de-https-y-la-navegacion-segura.html"
#original_url = "http://bulma.net/body.phtml?nIdNoticia=2613"
#original_url = "http://rhonda.deb.at/blog/2011/04/18#wise-guys"
original_url = "http://perezmeyer.blogspot.com/2011/04/entradas-de-nfs-en-fstab-que-no-montan.html"

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

print "links to download: " + `url_mod_list`

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

