#!/usr/bin/env python
# -*- coding: utf-8 -*-

tel = {'jack': 4098, 'sape': 4139}
print tel
tel['guido'] = 4127
print tel
print tel['jack']
del tel['sape']
print tel
print tel.keys()
print 'guido' in tel

for k, v in tel.iteritems():
 print k, v
