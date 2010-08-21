#!/usr/bin/env python

import urllib

url = 'http://www.hispasec.com/favicon.ico'

web_file = urllib.urlopen(url)
local_file = open(url.split('/')[-1], 'w')
local_file.write(web_file.read())
web_file.close()
local_file.close()

