#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import urllib2
import re
import sys

def get_filename(url):
 """Obtains filename from a given link."""
 i = -1
 filename = url.split("/")[i]
 while filename == '':
  i -= 1
  filename = url.split("/")[i]
 return filename

def get_base_url(original_url):
 """Obtains base url from a given link."""
 rgxp = '''(http|https)://+[^/]*?/'''
 m = re.search(rgxp, original_url)
 if m is not None:
  base_url = m.group(0)
 else:
  base_url = original_url
 return base_url

def rebuild_link(original_url, relative_link, url_mod_list):
 """Builds an absolute link from a relative one."""
 original_url2 = original_url.split("http://")[1] # http://blog.liw.fi/posts/obnam-0.16/ => blog.liw.fi/posts/obnam-0.16/
 original_url_split = original_url2.split("/") # blog.liw.fi/posts/obnam-0.16/ => ('blog.liw.fi', 'posts', 'obnam-0.16', '')
 copy_of_clean_original_url_split = clean_original_url_split = filter(None, original_url_split)
 relative_link_split = relative_link.split("/") # ../../favicon.ico => ('..', '..', 'favicon.ico')
 clean_relative_link_split = filter(None, relative_link_split)

 if clean_relative_link_split[0] != "." and clean_relative_link_split[0] != "..":
  a = base_url = get_base_url(original_url)
  b = "/".join(clean_relative_link_split)
  if a.endswith("/") or b.startswith("/"):
   final_url = a + b
  else:
   final_url = a + "/" + b
  url_mod_list.append(final_url)
  print 'Rebuilt_link (A): ' + final_url
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

def filter_needed_content(f, original_url, url_list, url_mod_list):
 """Obtains the needed content to correctly show a page offline."""
 if not os.path.exists(full_path + f):
  web_file = urllib2.urlopen(original_url)
  local_file = open(full_path + f, 'w')
  page = web_file.read()
  web_file.close()
  local_file.write(page)
  local_file.close()
 else:
  local_file = open(full_path + f, 'r')
  page = local_file.read()
  local_file.close()

 # Obtain base url
 base_url = get_base_url(original_url)
 #regexps = ('''<(link|script|img|iframe)\s+[^>]*?(href|src)=["]?([^">\s]+)[^>]*?>''', '''(url)\(('|")*([^\)]*?)('|")*\)''')
 #regexps = ('''<(link|script|img|iframe)\s+[^>]*?(href|src|longdesc)=["']?([^'">\s]*?)["'\s/]*?>''', '''(url)\(('|")*([^\)]*?)('|")*\)''')
 regexps = ('''<(link|script|img|iframe)\s+[^>]*?(href|src)=["']?([^"'>\s]+)[^>]*?>''', '''(url)\(('|")*([^\)]*?)('|")*\)''')
 #url_list = [] # Dict for original urls
 #url_mod_list = [] # Dict for modified urls
 css_list = [] # Dict for css files
 for rgxp in regexps:
  tags = re.findall(rgxp, page, re.I)
  for tag in tags:
   clean_tag = tag[2].strip().strip("'")
   #if tag[2] != base_url and tag[2] != base_url[0:-1]:
   if clean_tag != base_url and clean_tag != base_url[0:-1] and clean_tag != '':
    print "Detected " + clean_tag
    if ".css" in clean_tag:
     css_list.append(clean_tag)
    url_list.append(clean_tag)
    #if tag[2].startswith("http") or tag[2].startswith("https"): # Enlace absoluto
    if clean_tag.startswith("http") or clean_tag.startswith("https"): # Enlace absoluto
     url_mod_list.append(clean_tag)
    else: # Enlace relativo. ¡Cabe reconstruir el link!
     url_mod_list = rebuild_link(original_url, clean_tag, url_mod_list)
 return page, url_list, url_mod_list, css_list

def retrieve_needed_content(url_mod_list):
 """Retrieves the content chosen from the filter content (if not present already)."""
 url_mod_set = set(url_mod_list) # Remove duplicates
 print "Links to download: " + `url_mod_set`
 for url in url_mod_set:
  # Get file name to save
  filename = get_filename(url)
  if not os.path.exists(full_path + filename):
   print "Retrieving " + url + "..."
   try:
    web_file = urllib2.urlopen(url)
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
   except urllib2.HTTPError, e:
    print "Oops! The error was: " + `e.code` + " - " + `e.msg`
   except urllib2.URLError, e:
    print "Other error: " + `e`
  else:
   print "Skipping " + full_path + filename + "..."

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

########
# MAIN #
########

full_path = "/home/jors/sources/proyectos/naufrago/samples/test/url_fetcher/"
#original_url = "http://perezmeyer.blogspot.com/2011/04/entradas-de-nfs-en-fstab-que-no-montan.html"
#original_url = "http://blog.48bits.com/2011/04/15/un-reloj-de-dos-colores/"
#original_url = "http://www.abc.es/20110425/internacional/abci-siria-frontera-201104251200.html"
#original_url = "http://www.elperiodico.com/es/noticias/sociedad/c-31-calonge-n-340-vendrell-sufren-mediodia-los-mayores-atascos-983946"
#original_url = "http://ciberderechos.barrapunto.com/ciberderechos/11/04/26/1157233.shtml" # LINKS MAL CONSTRUIDOS, poco podemos hacer :(
#original_url = "http://bulma.net/body.phtml?nIdNoticia=2614"
#original_url = "http://www.cuantocabron.com/me_gusta/fffsssshhhh"
#original_url = "http://foro.elhacker.net/noticias/google_acelera_gmail-t325746.0.html"
#original_url = "http://www.elladodelmal.com/2011/04/la-fiesta-el-badge-y-la-troopers-2011.html"
#original_url = "http://www.elmundo.es/elmundo/2011/04/26/valencia/1303828717.html"
#original_url = "http://enchufado.com/post.php?ID=339"
#original_url = "http://es.engadget.com/2011/04/27/qik-video-connect-une-para-siempre-a-usuarios-de-iphone-y-androi/"
#original_url = "http://kriptopolis.org/secretitos-dni-electronico"
#original_url = "http://www.lavanguardia.es/vida/20110427/54144994022/un-instituto-usa-perros-para-detectar-droga-en-las-mochilas.html"
#original_url = "http://m.menea.me/qlv4" # DISEÑO
#original_url = "http://mariodebian.com/post/1/697"
#original_url = "http://www.rubenortiz.es/2011/04/20/linux-regenerar-raid-con-mdstat/"
#original_url = "http://www.sahw.com/wp/archivos/2011/04/14/analisis-forense-de-sistemas-de-ficheros-ufs-particionado-bsd386/" # DISEÑO
#original_url = "http://www.securitybydefault.com/2011/04/trasteando-con-una-alarma-de-securitas.html"
original_url = "http://www.vistoenfb.com/conversaciones/y-luego-a-los-que-de-verdad-la-necesitan-no-se-la-conceden"

# Filter needed content
url_list = [] # Dict for original urls
url_mod_list = [] # Dict for modified urls
page, url_list, url_mod_list, css_list = filter_needed_content('1.html', original_url, url_list, url_mod_list)

# Retrieve needed content (if not present already)
retrieve_needed_content(url_mod_list)
# Translate html document for local viewing
translate_document(page, url_list, '1.html')

for f in css_list:
 filename = get_filename(f)
 print "Scrapping css file " + filename + "..."
 page, url_list, url_mod_list, css_list = filter_needed_content(filename, original_url, url_list, url_mod_list)
 retrieve_needed_content(url_mod_list)
 translate_document(page, url_list, filename)

