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
 except:
  pass

app_path = os.getcwd()
db_path = app_path + '/naufrago.db'
homedir = os.getenv('HOME')

if os.path.exists(homedir + '/.naufrago/'): # Are we dealing with 0.1...
 os.rename(homedir + '/.naufrago/', homedir + '/.config/naufrago/')
 try:
  conn = sqlite3.connect(homedir + '/.config/naufrago/naufrago.db')
 except:
  print "Could not find database... Did you forget to move it to the current directory?"
 cursor = conn.cursor()
 v01to02(cursor)
 v02to03(cursor)
 conn.commit()
 cursor.close()
elif os.path.exists(homedir + '/.config/naufrago/'): # ... or 0.2 version?
 try:
  conn = sqlite3.connect(homedir + '/.config/naufrago/naufrago.db')
 except:
  print "Could not find database... Did you forget to move it to the current directory?"
 cursor = conn.cursor()
 v02to03(cursor)
 conn.commit()
 cursor.close()
