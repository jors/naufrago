#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.etree import ElementTree

f = open('liferea_feedlist.opml', 'r')
tree = ElementTree.parse(f)
current_category = ''

for node in tree.getiterator('outline'):
 name = node.attrib.get('text')
 url = node.attrib.get('xmlUrl')
 tipo = node.attrib.get('type')
 if name and url:
  print ' - %s ( %s )' % (name, url)
 elif tipo == 'folder' and len(node) is not 0:
  #if len(node) is not 0:
  if node[0].attrib.get('type') != 'folder':
   print 'CATEGORIA: ' + name
   #print 'Node with ' + str(len(node)) + ' subelements!'

f.close()
