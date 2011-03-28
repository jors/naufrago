#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sqlite3
import time

count = 100
q1 = 'SELECT articulo.id,articulo.titulo FROM articulo, feed, categoria WHERE articulo.leido=0 AND articulo.id_feed=feed.id AND feed.id_categoria=categoria.id'
q2 = 'SELECT articulo.id,articulo.titulo FROM articulo LEFT JOIN feed LEFT JOIN categoria WHERE articulo.leido=0 AND articulo.id_feed=feed.id AND feed.id_categoria=categoria.id'

db_path = '/home/jors/.config/naufrago/naufrago.db.bkp'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

t0 = time.time()
for i in xrange(count):
 cursor.execute(q1)
 row = cursor.fetchall()
print 'sql1 (TRADITIONAL): ' + `time.time()-t0`

t0 = time.time()
for i in xrange(count):
 cursor.execute(q2)
 row = cursor.fetchall()
print 'sql2 (LEFT JOIN): ' + `time.time()-t0`

cursor.close()
