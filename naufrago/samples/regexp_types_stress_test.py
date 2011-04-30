#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time

loop_count = 100000
regexp = '''[^\W]'''
a = "http://this-is-a-web.com/1.html"

def regexptype1_function():
 for num in xrange(loop_count):
  m = re.search(regexp, a)
  continue

def regexptype2_function():
 for num in xrange(loop_count):
  m = re.findall(regexp, a, re.I)
  continue

t0 = time.time()
regexptype1_function()
print 'regexptype1_function(): ' + `time.time()-t0`

t0 = time.time()
regexptype2_function()
print 'regexptype2_function(): ' + `time.time()-t0`
