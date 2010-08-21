#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sqlite3

current_path = os.getcwd()
db_path = current_path + '/naufrago.db'
excedente = 1

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('SELECT id FROM articulo WHERE id_feed = 3 AND importante = 0 ORDER BY fecha ASC')
row = cursor.fetchall()
print row
print len(row)
id_articulos = ''
for i in row:
 id_articulos += str(i[0])+','
id_articulos = id_articulos[0:len(id_articulos)-1]
cursor.execute('SELECT count(id),id FROM articulo WHERE id_feed = 3 AND importante = 0 ORDER BY fecha ASC')
row2 = cursor.fetchall()
print row2
print "DELETE FROM articulo WHERE id IN ("+id_articulos+") LIMIT "+str(excedente)
#cursor.execute('DELETE FROM articulo WHERE id IN ('+row2[1]+') LIMIT ?', [excedente])
cursor.close()
