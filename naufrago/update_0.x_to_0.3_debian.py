#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Script to update sqlite database from Naufrago! version 0.1 to 0.2.
import os
import sqlite3

def 01to02(cursor):
 try:
  cursor.execute('ALTER TABLE config ADD show_trayicon integer NOT NULL DEFAULT 0')
  cursor.execute('ALTER TABLE config ADD toolbar_mode integer NOT NULL DEFAULT 0')
  cursor.execute('ALTER TABLE config ADD show_newentries_notification integer NOT NULL DEFAULT 1')
  cursor.execute('ALTER TABLE config ADD hide_readentries integer NOT NULL DEFAULT 0')
  cursor.execute('UPDATE categoria SET nombre = \'General\' WHERE id = 1')
  conn.commit()
 except:
    pass

def 02to03(cursor):
 try:
  cursor.execute('ALTER TABLE config ADD hide_dates integer NOT NULL DEFAULT 0')
  cursor.execute('ALTER TABLE config ADD driven_mode integer NOT NULL DEFAULT 1')
  cursor.execute('ALTER TABLE config ADD update_freq_timemode integer NOT NULL DEFAULT 0')
  cursor.execute('ALTER TABLE config ADD init_check_app_updates integer NOT NULL DEFAULT 1')
  cursor.execute('ALTER TABLE articulo ADD ghost integer NOT NULL DEFAULT 0')
 except:
  pass

for user in os.listdir('/home'):
 homedir = '/home/' + user
 if os.path.isdir(homedir):
  if os.path.exists(homedir + '/.naufrago/'): # Are we dealing with 0.1...
   os.rename(homedir + '/.naufrago/', homedir + '/.config/naufrago/')
   conn = sqlite3.connect(homedir + '/.config/naufrago/naufrago.db')
   cursor = conn.cursor()
   01to02(cursor)
   02to03(cursor)
   cursor.close()
  elif os.path.exists(homedir + '/.config/naufrago/naufrago.db'): # ... or 0.2 version?
   conn = sqlite3.connect(homedir + '/.config/naufrago/naufrago.db')
   cursor = conn.cursor()
   02to03(cursor)
   cursor.close()
