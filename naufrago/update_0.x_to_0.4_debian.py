#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Script to update sqlite database from Naufrago! version 0.1 to 0.2.
import os
import sqlite3

def v01to02(cursor):
 try:
  cursor.execute('ALTER TABLE config ADD show_trayicon integer NOT NULL DEFAULT 0')
  cursor.execute('ALTER TABLE config ADD toolbar_mode integer NOT NULL DEFAULT 0')
  cursor.execute('ALTER TABLE config ADD show_newentries_notification integer NOT NULL DEFAULT 1')
  cursor.execute('ALTER TABLE config ADD hide_readentries integer NOT NULL DEFAULT 0')
  cursor.execute('UPDATE categoria SET nombre = \'General\' WHERE id = 1')
  conn.commit()
  print 'Naufrago! 0.1 database found, changes correctly applied :)'
 except:
    pass

def v02to03(cursor):
 try:
  cursor.execute('ALTER TABLE config ADD hide_dates integer NOT NULL DEFAULT 0')
  cursor.execute('ALTER TABLE config ADD driven_mode integer NOT NULL DEFAULT 1')
  cursor.execute('ALTER TABLE config ADD update_freq_timemode integer NOT NULL DEFAULT 0')
  cursor.execute('ALTER TABLE config ADD init_check_app_updates integer NOT NULL DEFAULT 1')
  cursor.execute('ALTER TABLE articulo ADD ghost integer NOT NULL DEFAULT 0')
  cursor.execute('UPDATE config SET init_unfolded_tree = 0')
  conn.commit()
  print 'Naufrago! 0.2 database found, changes correctly applied :)'
 except:
  pass

def v03to04(cursor):
 try:
  cursor.execute('ALTER TABLE config ADD clear_mode integer NOT NULL DEFAULT 0')
  cursor.execute('ALTER TABLE config ADD deep_offline_mode integer NOT NULL DEFAULT 0')
  cursor.execute('CREATE TABLE contenido_offline(id integer PRIMARY KEY, nombre varchar(256) NOT NULL, id_articulo integer NOT NULL);')
  conn.commit()
  print 'Naufrago! 0.3 database found, changes correctly applied :)'
 except:
  pass

for user in os.listdir('/home'):
 homedir = '/home/' + user
 if os.path.isdir(homedir):
  if os.path.exists(homedir + '/.naufrago/'): # Are we dealing with 0.1...
   os.rename(homedir + '/.naufrago/', homedir + '/.config/naufrago/')
   conn = sqlite3.connect(homedir + '/.config/naufrago/naufrago.db')
   cursor = conn.cursor()
   v01to02(cursor)
   v02to03(cursor)
   v03to04(cursor)
   conn.commit()
   cursor.close()
  elif os.path.exists(homedir + '/.config/naufrago/naufrago.db'): # ... or 0.2/later version?
   conn = sqlite3.connect(homedir + '/.config/naufrago/naufrago.db')
   cursor = conn.cursor()
   v02to03(cursor)
   v03to04(cursor)
   conn.commit()
   cursor.close()
