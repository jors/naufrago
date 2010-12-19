#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sqlite3
import time

t0 = time.time()
db_path = '/home/jors/.config/naufrago/naufrago.db.bkp'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('SELECT id FROM feed')
feeds = cursor.fetchall()
s_total = ''
for row in feeds:
 cursor.execute('SELECT id FROM articulo WHERE id_feed=? AND importante=0 ORDER BY fecha ASC', [row[0]])
 row2 = cursor.fetchall()
 s = ','.join(str(n[0]) for n in row2)
 s_total = s_total + s
print s_total
cursor.close()
print 'Time: ' + `time.time()-t0`
