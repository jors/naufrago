#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sqlite3

db_path = '/home/jors/.config/naufrago/naufrago.db.bkp'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# CHECK 1. Tot el de la BD esta al disc dur?
check_ok = 0
check_fail = 0
print '******************************************'
print 'CHECK 1. Tot el de la BD esta al disc dur?'.encode('utf-8')
print '******************************************'
cursor.execute('SELECT id,nombre FROM feed')
feed = cursor.fetchall()
for i in feed:
 l = len('On feed ' + i[1])
 print l * '-'
 print 'On feed ' + i[1].encode('utf-8')
 print l * '-'
 cursor.execute('SELECT nombre,id_articulo FROM contenido_offline WHERE id_articulo IN (SELECT id FROM articulo WHERE id_feed = ?)', [`i[0]`])
 contenido_offline = cursor.fetchall()
 path = '/home/jors/.config/naufrago/contenido/' + `i[0]` + '/'
 for j in contenido_offline:
  # Check if database element is on filesystem
  if not os.path.exists(path + j[0]):
   check_fail+=1
   msg = '[ERR] File ' + path + j[0] + ' exist on database but NOT on filesystem!'
   print msg.encode('utf-8')
  else:
   check_ok+=1
   msg = 'Everything OK with ' + path + j[0]
   print msg.encode('utf-8')
   # CHECK 3. Tot el de la BD pertany a un article existent?
   cursor.execute('SELECT titulo FROM articulo WHERE id = ?', [j[1]])
   articulo = cursor.fetchall()
   if articulo is None:
    print '[ERR] File has NO ASSOCIATED article!'.encode('utf-8')
   else:
    print 'File belongs to article: ' + articulo[0][0].encode('utf-8')
cursor.close()
print ''
print ' * check_ok: ' + `check_ok`
print ' * check_fail: ' + `check_fail`
print ''

# CHECK 2. Tot el del disc dur esta a la BD?
check_ok = 0
check_fail = 0
print '******************************************'
print 'CHECK 2. Tot el del disc dur esta a la BD?'.encode('utf-8')
print '******************************************'
path = '/home/jors/.config/naufrago/contenido/'
dirList = os.listdir(path)
for dirName in dirList:
 fileList = os.listdir(path + dirName)
 for fname in fileList:
  #try:
  fname_encoded = fname.encode('utf-8')
  cursor.execute('SELECT id_articulo FROM contenido_offline WHERE nombre = ?', [fname_encoded])
  contenido_offline = cursor.fetchall()
  if contenido_offline is None:
   check_fail+=1
   print '[ERR] File ' + fname_encoded + ' exists on disc but NOT on the database!'
  else:
   print 'Everything OK with ' + fname_encoded
   # CHECK 3. Tot el del disc dur i bd pertany a un article existent?
   ids_articulo = ''
   for i in contenido_offline:
    ids_articulo += `i[0]` + ','
   ids_articulo = ids_articulo[0:-1]

   cursor.execute('SELECT titulo FROM articulo WHERE id IN ('+ids_articulo+')')
   articulo = cursor.fetchall()
   if articulo is None:
    check_fail+=1
    print '[ERR] File ('+fname_encoded+') has NO ASSOCIATED article!'.encode('utf-8')
   else:
    check_ok+=1
    print 'File belongs to article/s: ' + `articulo`
  #except:
  # print 'Encoding problem; skipping...'
print ''
print ' * check_ok: ' + `check_ok`
print ' * check_fail: ' + `check_fail`
print ''
