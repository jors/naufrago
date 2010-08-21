#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

rgxp = r''' \((\d)\)$'''
replacement = r'''[\1]'''
text = 'Esto es un texto (1)'
text = 'Plas plas (test)'

m = re.search(rgxp, text)
if m is not None:
 split = text.split(' ')
 print ' '.join(split[0:len(split)-1])
else:
 print text

#try:
# m = re.search(rgxp, text)
# print m.group(0)
# print 'Patrón encontrado!'
#except AttributeError, e:
# pass

#print 'Original: ' +  text
#outtext = re.sub(rgxp, replacement, text)
#print 'Salida: ' + outtext

