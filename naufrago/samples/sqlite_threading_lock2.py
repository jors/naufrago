#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import threading
import gtk
import gobject
gobject.threads_init()
import os

# FUNCTIONS #
def consulta(j):
 global lock, conn, cursor
 gtk.gdk.threads_enter()
 q = 'SELECT * FROM a'
 print 'Thread #'+`j`+', ',q
 lock.acquire()
 cursor.execute(q)
 res = cursor.fetchall()
 lock.release()
 #print str(res)
 gtk.gdk.threads_leave()

def insercion(j):
 global lock, conn, cursor
 gtk.gdk.threads_enter()
 for i in range(10):
  q = "INSERT INTO a VALUES('"+str(j)+"', '"+str(i)+"')"
  print 'Thread #'+`j`+', ',q
  lock.acquire()
  cursor.execute(q)
  conn.commit()
  lock.release()
 gtk.gdk.threads_leave()
 
def base():
 global cursor
 q = 'CREATE TABLE a(col1 varchar(16) NOT NULL, col2 varchar(16) NOT NULL)'
 print q
 cursor.execute(q)
 conn.commit()

# MAIN #
conn = sqlite3.connect('some.db',  check_same_thread=False)
cursor = conn.cursor()
lock = threading.RLock()
base()
t_list = []
for j in range(0,5):
 t = threading.Thread(target=insercion, args=(j,))
 t_list.append(t)
 t.start()
 t2 = threading.Thread(target=consulta, args=(j,))
 t_list.append(t2)
 t2.start()
# Main thread/father will wait all his child...
for t in t_list:
 t.join()
cursor.close()
os.unlink('some.db')

