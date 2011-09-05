#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

url = 'http://www.facebook.com/plugins/like.php?href=http://blog.segu-info.com.ar/2011/09/f-secure-encuentra-el-email-utilizado.html&layout=button_count&show_faces=true&width=140&action=like&font=arial&colorscheme=light'
print "Retrieving " + url + "..."
filename = get_filename(url)
print "Filename is: " + filename
try:
 web_file = urllib2.urlopen(url, timeout=5)
 #self.statusbar.set_text(_('Obtaining offline content ') + url + '...'.encode("utf8"))
 # Chunk filename if it is too large!
 if len(filename) > 256:
  m = re.search('[^?=&]+', filename)
  filename = m.group(0)
  print "Filename (processed) is: " + filename
 local_file = open(filename, 'w')
 local_file.write(web_file.read())
 local_file.close()
 web_file.close()
 #store_values[filename] = `id_articulo` # Storing all filename, id_articulo pairs
 print "Done!"
except urllib2.HTTPError, e:
 print "Oops! The error was: " + `e.code` + " - " + `e.msg`
except urllib2.URLError, e:
 print "Other error: " + `e`
except urllib2.httplib.BadStatusLine, e: # We need this because it does not seem to be handled by urllib2 :(
 print "BadStatusLine error: " + `e`
except:
 print "Unknown error:", sys.exc_info()[0]
