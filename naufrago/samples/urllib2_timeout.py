#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib2

web_file = urllib2.urlopen('http://enchufado.com/proyectos/naufrago/app_version', timeout=1)
read = web_file.read().rstrip()
web_file.close()
