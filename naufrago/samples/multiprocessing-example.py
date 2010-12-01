#!/usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing

def worker():
 print 'Worker ' + `i`

#jobs = []
for i in range(5):
 p = multiprocessing.Process(target=worker)
 #jobs.append(p)
 p.start()
