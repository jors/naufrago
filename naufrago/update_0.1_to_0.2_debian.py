#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Script to update sqlite database from Naufrago! version 0.1 to 0.2.
import os
import sqlite3

for user in os.listdir('/home'):
 if os.path.isdir(os.path.join('/home', user)):
  # Appdir move!
  homedir = '/home/' + user
  if os.path.exists(homedir + '/.naufrago/'):
   os.rename(homedir + '/.naufrago/', homedir + '/.config/naufrago/')
  # Database conditioning!
  if os.path.exists(homedir + '/.config/naufrago/naufrago.db'):
   conn = sqlite3.connect(homedir + '/.config/naufrago/naufrago.db')
   cursor = conn.cursor()
   try:
    cursor.execute('ALTER TABLE config ADD show_trayicon integer NOT NULL DEFAULT 0')
    cursor.execute('ALTER TABLE config ADD toolbar_mode integer NOT NULL DEFAULT 0')
    cursor.execute('ALTER TABLE config ADD show_newentries_notification integer NOT NULL DEFAULT 1')
    cursor.execute('ALTER TABLE config ADD hide_readentries integer NOT NULL DEFAULT 0')
    cursor.execute('UPDATE categoria SET nombre = \'General\' WHERE id = 1')
    conn.commit()
    cursor.close()
   except:
    pass
