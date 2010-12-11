#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.etree import ElementTree

feedlist = 'liferea_feedlist.opml'
feedlist = 'naufrago-subscriptions.opml'
feedlist = 'feedr-subscriptions.xml'

f = open(feedlist, 'r')
tree = ElementTree.parse(f)
current_category = ''

for node in tree.getiterator('outline'):
 name = node.attrib.get('text')
 url = node.attrib.get('xmlUrl')
 if url:
  print ' - %s ( %s )' % (name, url)
 else:
  if len(node) is not 0:
   print 'CATEGORIA: ' + name
f.close()
