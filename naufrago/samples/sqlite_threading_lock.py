#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import threading
import gtk
import gobject
gobject.threads_init()
import os

# FUNCTIONS #
def consulta():
 global lock
 lock.acquire()
 for i in range(10):
  q = 'SELECT * FROM a'
  print q
  cursor.execute(q)
  res = cursor.fetchall()
  print str(res)
 lock.release()
 
def base():
 global lock
 lock.acquire()
 gtk.gdk.threads_enter()
 q = 'CREATE TABLE a(col1 varchar(16) NOT NULL, col2 varchar(16) NOT NULL)'
 print q
 cursor.execute(q)
 for j in range(10):
  for i in range(10):
   q2 = "INSERT INTO a VALUES('"+str(j)+"', '"+str(i)+"')"
   print q2
   cursor.execute(q2)
   conn.commit()
 gtk.gdk.threads_leave()
 lock.release()

# MAIN #
lock = threading.Lock()
conn = sqlite3.connect('some.db', check_same_thread=False)
cursor = conn.cursor()
t = threading.Thread(target=base, args=())
t.start()
t2 = threading.Thread(target=consulta, args=())
t2.start()
t.join()
t2.join()
cursor.close()
os.unlink('some.db')
