#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time

loop_count = 10
label = 'Nombre del feed [10]'

def regexp_function():
 rgxp = r''' \[.*\]$'''
 for num in xrange(loop_count):
  m = re.search(rgxp, label)
  if m is not None:
   continue

def string_function():
 for num in xrange(loop_count):
  if '[' in label and ']' in label:
   continue

t0 = time.time()
regexp_function()
print 'regexp_function(): ' + `time.time()-t0`

t0 = time.time()
string_function()
print 'string_function(): ' + `time.time()-t0`
