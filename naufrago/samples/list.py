#!/usr/bin/env python

L = ['uno', 'dos', 'tres']
if 'uno' in L:
 print 'Trobat!'
 L.append('cuatre')
 print L
 print 'Mide ' + `len(L)`
else:
 print 'No trobat!'
