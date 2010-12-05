#!/usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing

def worker(q):
 print 'Worker ' + `i`
 var = q.get() + 1
 q.put(var)

var = 0
queue = multiprocessing.Queue()
queue.put(var)

print 'inicial: ' + `var`
for i in range(1):
 p = multiprocessing.Process(target=worker, args=(queue,))
 p.start()
 p.join()
print 'final: ' + `queue.get()`
