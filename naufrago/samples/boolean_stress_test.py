#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

loop_count = 1000000
var = True

def check1():
 for num in xrange(loop_count):
  if var:
   continue

def check2():
 for num in xrange(loop_count):
  if var is True:
   continue

t0 = time.time()
check1()
print 'check1_function(): ' + `time.time()-t0`

t0 = time.time()
check2()
print 'check2_function(): ' + `time.time()-t0`
