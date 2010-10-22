#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
 import sys
 import caca
except ImportError:
 print 'Error importing modules: ' + str(sys.exc_info()[1])
 sys.exit(1)
