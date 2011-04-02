#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, subprocess

full_path = "/home/jors/test"
url = "http://feedproxy.google.com/~r/CuantoCabron/~3/FrVvvzDfRMk/118540"

p = subprocess.Popen("wget -p -nc -nd -k -P \""+full_path+"\" \""+url+"\"", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output,errors = p.communicate()
print output
print errors
rgxp = '''(Saving to:) `([^']*?)[']'''
m = re.search(rgxp, errors)
if m is not None:
 print "File saved to: " + m.group(2)
