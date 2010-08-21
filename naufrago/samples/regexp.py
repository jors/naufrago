#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

rgxp = r''' \((\d)\)'''
replacement = r''' [\1]'''
replacement2 = r''''''
text = 'Esto es un texto (1)'

print 'Original: ' +  text
outtext = re.sub(rgxp, replacement2, text)
print 'Salida: ' + outtext

