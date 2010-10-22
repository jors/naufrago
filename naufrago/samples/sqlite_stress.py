#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sqlite3

q1 = 'SELECT articulo.id,articulo.titulo FROM articulo, feed, categoria WHERE articulo.leido=0 AND articulo.id_feed=feed.id AND feed.id_categoria=categoria.id'
q2 = 'SELECT articulo.id,articulo.titulo FROM articulo LEFT JOIN feed LEFT JOIN categoria WHERE articulo.leido=0 AND articulo.id_feed=feed.id AND feed.id_categoria=categoria.id'

db_path = '/home/jors/.config/naufrago/naufrago.db.bkp'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
for i in range(0,100):
 cursor.execute(q2)
 row = cursor.fetchall()
#for i in range(0,1000):
# cursor.execute(q2)
# row = cursor.fetchall()
cursor.close()
