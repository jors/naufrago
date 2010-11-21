#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Naufrago RSS Reader, by jors ( worbynet at gmail dot com ), 14-05-2010
#
# This app has been done (and needs) thanks to:
# - python
# - pygtk
# - sqlite
# - feedparser
# - ...
# 
# Also thanks to:
# - #python @ irc.freenode.net & irc.hispano.org
# - The cool svg logo done by: GMcGlinn (http://www.openclipart.org/user-detail/GMcGlinn)
#
# Special thanks for the _great_ DnD stuff to:
# - Doug Quale ( quale1 at charter dot net )
# - Walter Anger ( WalterAnger at aon dot at )
#
# It was also great to have the pygtk tutorial: http://www.pygtk.org/pygtk2tutorial/index.html

import pygtk
pygtk.require('2.0')
import gtk
import os
import sqlite3
import feedparser
import time
import datetime

window_visible = True
db_path = os.getenv("HOME") + '/.naufrago/naufrago.db'

class Naufrago:

 # CALLBACKS #
 #############

 def quit(self):
  """Quits the app"""
  self.save_config()
  self.hide()
  self.destroy()

 # Imprime una cadena por pantalla
 def callback(self, data):
  print "Hello again - %s was pressed" % data

 def delete_event(self, event, data=None):
  """Closes the app through window manager signal"""
  self.save_config()
  gtk.main_quit()
  return False

 def button_press_event(self, widget, event):
  """Tells which mouse button was pressed"""
  print 'Button ' + str(event.button) + '  pressed!'
  #if(event.button == 3):
   #menu1 = gtk.Menu()
   # TODO

 def tree_key_press_event(self, widget, event):
  """Tells which keyboard button was pressed"""
  key = gtk.gdk.keyval_name(event.keyval)
  print 'Key ' + key + ' pressed!'
  if(key == 'Delete'):
   (model, iter) = self.treeselection.get_selected()
   if(iter is not None): # Si hay algún nodo seleccionado...
    text = self.treestore.get_value(iter, 0)
    if(model.iter_depth(iter) == 0): # Si es un nodo padre...
     self.delete_category()
    elif(model.iter_depth(iter) == 1): # Si es un nodo hijo...
     self.delete_feed()

 def make_pb(self, tvcolumn, cell, model, iter):
  """Renders the parameter received icons"""
  stock = model.get_value(iter, 1)
  pb = self.treeview.render_icon(stock, gtk.ICON_SIZE_MENU, None)
  cell.set_property('pixbuf', pb)
  return

 def toggle_importante(self, cell, path, model):
  """Sets the toggled state on the toggle button to true or false"""
  model[path][1] = not model[path][1]
  print "Toggle '%s' to: %s" % (model[path][4], model[path][1])
  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()
  cursor.execute('UPDATE articulo SET importante = ? WHERE id = ?', [model[path][1],model[path][4]])
  conn.commit()
  cursor.close()
  return

 def toggle_leido(self, event, data=None):
  """Toggled entries between read/non-read states."""
  (model, iter) = self.treeselection2.get_selected()
  if(iter is not None): # Hay alguna fila de la lista seleccionada
   fecha = self.liststore.get_value(iter, 0)
   titulo = self.liststore.get_value(iter, 2)
   id_articulo = self.liststore.get_value(iter, 4)
   print 'Fila *' + titulo + '* (' + fecha + ') con id ' + str(id_articulo) + ' seleccionada'
   conn = sqlite3.connect(db_path)
   cursor = conn.cursor()
   font_style = model.get(iter, 3)[0]
   if(data == 'single'):
    #font_style = model.get(iter, 3)[0]
    if(font_style == 'normal'):
     self.liststore.set_value(iter, 3, 'bold')
     #model.set(iter, 0, fecha, 2, titulo, 3, 'bold') # That sucks (it doesn't update the model)!
     cursor.execute('UPDATE articulo SET leido=0 WHERE id = ?', [id_articulo])
    else:
     self.liststore.set_value(iter, 3, 'normal')
     #model.set(iter, 0, fecha, 2, titulo, 3, 'normal') # That sucks too (same crap)!
     cursor.execute('UPDATE articulo SET leido=1 WHERE id = ?', [id_articulo])
   elif(data == 'all'):
    leido = 0
    if(font_style == 'normal'):
     font_style = 'bold'
     leido = 0
    else:
     font_style = 'normal'
     leido = 1
    iter = model.get_iter_root() # Magic
    entry_ids = ''
    while iter: 
     self.liststore.set_value(iter, 3, font_style)
     id_articulo = self.liststore.get_value(iter, 4)
     entry_ids += str(id_articulo)+','
     iter = self.liststore.iter_next(iter)
    entry_ids = entry_ids[0:-1]
    print 'entry_ids: ' + str(entry_ids)
    q = 'UPDATE articulo SET leido=' + str(leido) +' WHERE id IN (' + entry_ids + ')'
    print q
    cursor.execute(q)
   conn.commit()
   cursor.close()

# FUNCTIONS #
#############

 def list_row_selection(self, event):
  """List row change detector"""
  (model, iter) = self.treeselection2.get_selected()
  if(iter is not None): # Hay alguna fila de la lista seleccionada
   fecha = self.liststore.get_value(iter, 0)
   titulo = self.liststore.get_value(iter, 2)
   id_articulo = self.liststore.get_value(iter, 4)
   print 'Fila *' + titulo + '* (' + fecha + ') con id ' + str(id_articulo) + ' seleccionada'
   model.set(iter, 0, fecha, 2, titulo, 3, 'normal')
   conn = sqlite3.connect(db_path)
   cursor = conn.cursor()
   # Si no estaba leído, marcarlo como tal.
   cursor.execute('SELECT leido FROM articulo WHERE id = ?', [id_articulo])
   row = cursor.fetchone()
   if(row[0] == 0):
    cursor.execute('UPDATE articulo SET leido=1 WHERE id = ?', [id_articulo])
    conn.commit()
   cursor.close()

 def tree_row_selection(self, event):
  """Feed row change detector; triggers entry visualization on the list."""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Hay algún nodo seleccionado
   row_name = self.treestore.get_value(iter, 0)
   path = str(model.get_path(iter))
   print 'Nodo *' + row_name + '* seleccionado'
   print 'Path: ' + path
   if(model.iter_depth(iter) == 1): # Si es hoja, presentar entradas
    print 'Feed *' + row_name + '* seleccionado'
    # Instead of updating the feed, it should only show its entries on the liststore!!!
    self.get_feed(row_name)
    self.populate_entries(row_name)
   elif(model.iter_depth(iter) == 0): # Si es padre, limpliar 
    self.liststore.clear() # Limpieza de tabla de entries/articulos
    print 'Categoría *' + row_name + '* seleccionada'

 def tree_row_activated(self, treeview, iter, path):
  """Toggles expansion of a tree node when double clicking on it."""
  (model, iter) = self.treeselection.get_selected()
  path = model.get_path(iter)
  if(treeview.row_expanded(path)):
   treeview.collapse_row(path)
  else:
   treeview.expand_row(path, open_all=False)

 def statusicon_activate(self, data=None):
  """Activates the tray icon."""
  global window_visible # Global since we need to modify it

  if(window_visible):
   self.window.hide()
   window_visible = False
  else:
   self.window.show()
   window_visible = True

 def warning_message(self, str):
  """Shows a custom warning message dialog"""
  dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, str)
  dialog.run()
  dialog.destroy()

 def help_about(self, action):
  """Shows the about message dialog"""
  about = gtk.AboutDialog()
  about.set_program_name("Naufrago!")
  about.set_version("0.1")
  about.set_copyright("(c) jors")
  about.set_comments("Naufrago! is a simple RSS reader")
  about.set_website("http://www.enchufado.com/")
  about.set_logo(gtk.gdk.pixbuf_new_from_file("wilson.png"))
  about.run()
  about.destroy()

 def create_ui(self, window):
  """Creates the menubar"""
  ui_string = """<ui>
  <menubar name='Menubar'>
    <menu action='ArchivoMenu'>
      <menuitem action='Nuevo feed'/>
      <menuitem action='Nueva categoria'/>
      <menuitem action='Eliminar feed'/>
      <menuitem action='Eliminar categoria'/>
      <separator/>
      <menuitem action='Salir'/>
    </menu>
    <menu action='EditarMenu'>
      <menuitem action='Editar'/>
      <menuitem action='Preferencias'/>
    </menu>
    <menu action='RedMenu'>
      <menuitem action='Actualizar'/>
      <menuitem action='Actualizar todo'/>
    </menu>
    <menu action='AyudaMenu'>
      <menuitem action='Acerca de'/>
    </menu>
  </menubar>
</ui>"""

  # Una opción para que se muestren los iconos:
  # gconf-editor: Desktop -> Gnome -> Interface -> menus_have_icons (y buttons_have_icons)
  ag = gtk.ActionGroup('WindowActions')
  actions = [
            ('ArchivoMenu', None, '_Archivo'),
            ('Nuevo feed', gtk.STOCK_FILE, 'Nuevo _feed', '<control>F', 'Crea un feed', self.add_feed),
            ('Nueva categoria', gtk.STOCK_DIRECTORY, 'Nueva _categoria', '<control>C', 'Crea una categoria', self.add_category),
            ('Eliminar feed', gtk.STOCK_CLEAR, 'Eliminar _feed', '<alt>F', 'Elimina un feed', self.delete_feed),
            ('Eliminar categoria', gtk.STOCK_CLOSE, 'Eliminar _categoria', '<alt>C', 'Elimina una categoria', self.delete_category),
            ('Salir', gtk.STOCK_QUIT, '_Salir', '<control>S', 'Salir', self.delete_event),
            ('EditarMenu', None, '_Editar'),
            ('Editar', gtk.STOCK_EDIT, '_Editar', '<control>E', 'Edita el elemento seleccionado', self.edit),
            ('Preferencias', gtk.STOCK_EXECUTE, '_Preferencias', '<control>P', 'Muestra las preferencias', self.callback),
            ('RedMenu', None, '_Red'),
            ('Actualizar', None, '_Actualizar', '<control>A', 'Actualiza el feed seleccionado', self.callback),
            ('Actualizar todo', gtk.STOCK_REFRESH, 'Actualiza_r todo', '<control>R', 'Actualiza todos los feeds', self.callback),
            ('AyudaMenu', None, 'A_yuda'),
            ('Acerca de', gtk.STOCK_ABOUT, 'Acerca de', None, 'Acerca de', self.help_about),
            ]
  ag.add_actions(actions)
  self.ui = gtk.UIManager()
  self.ui.insert_action_group(ag, 0)
  self.ui.add_ui_from_string(ui_string)
  self.window.add_accel_group(self.ui.get_accel_group())

 def create_base(self):
  """Creates the base app structure on the user home dir"""
  if not os.path.exists(db_path):
    os.makedirs(os.getenv("HOME") + '/.naufrago')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executescript('''
     CREATE TABLE config(window_position varchar(16) NOT NULL, window_size varchar(16) NOT NULL, num_entries integer NOT NULL, update_freq integer NOT NULL);
     CREATE TABLE categoria(id integer PRIMARY KEY, nombre varchar(32) NOT NULL);
     CREATE TABLE feed(id integer PRIMARY KEY, nombre varchar(32) NOT NULL, url varchar(1024) NOT NULL, id_categoria integer NOT NULL);
     CREATE TABLE articulo(id integer PRIMARY KEY, titulo varchar(256) NOT NULL, contenido text, fecha integer NOT NULL, enlace varchar(1024) NOT NULL, leido INTEGER NOT NULL, importante INTEGER NOT NULL, id_feed integer NOT NULL);
     CREATE TABLE imagen(id integer PRIMARY KEY, imagen blob NOT NULL, id_articulo integer NOT NULL);
     INSERT INTO config VALUES('0,0', '600x400', 10, 1);
     INSERT INTO categoria VALUES(null, 'General');
     INSERT INTO feed VALUES(null, 'enchufado.com', 'http://www.enchufado.com/rss2.php', 1);''')
    conn.commit()
    cursor.close()

 def get_config(self):
  """Retrieves the app configuration"""
  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()
  cursor.execute('SELECT * FROM config')
  row = cursor.fetchone()
  self.x = int(row[0].split(",")[0])
  self.y = int(row[0].split(",")[1])
  self.w = int(row[1].split("x")[0])
  self.h = int(row[1].split("x")[1])
  self.num_entries = int(row[2])
  self.update_freq = int(row[3])
  cursor.close()

 def save_config(self):
  """Saves user window configuration"""
  (x, y) = self.window.get_position()
  (w, h) = self.window.get_size()
  position = str(x)+','+str(y)
  size = str(w)+'x'+str(h)
  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()
  cursor.execute('UPDATE config SET window_position = ?, window_size = ?', [position,size])
  conn.commit()
  cursor.close()

 def create_main_window(self):
  """Creates the main window with all it's widgets"""
  # Creamos una ventana
  self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
  self.window.set_title("Naufrago!")
  self.window.set_icon_from_file("Viking_Longship.svg")
  self.window.connect("delete_event", self.delete_event)
  self.window.set_border_width(5) # Grosor del borde de la ventana
  self.window.move(self.x, self.y)
  self.window.resize(self.w, self.h)
  #self.window.set_size_request(600, 400) # Dimensionamiento estático de la ventana

  ########################
  # PARTE 1 (feeds tree) #
  ########################
  # Creación del VBox.
  self.vbox = gtk.VBox(False, 0)
  # Creación del menubar
  self.create_ui(self.window)
  self.vbox.pack_start(self.ui.get_widget('/Menubar'), expand=False)
  # Creación del HPaned.
  self.hpaned = gtk.HPaned()
  # Creación del Tree izquierdo para los feeds
  self.treestore = self.populate_feeds() # Propaga los feeds del usuario
  # Create the TreeView using treestore
  self.treeview = gtk.TreeView(self.treestore)
  # Control de eventos de ratón y teclado del tree.
  self.treeview.connect("button_press_event", self.tree_button_press_event)
  self.treeview.connect("key_press_event", self.tree_key_press_event)
  self.treeview.connect("row-activated", self.tree_row_activated)
  self.treeselection = self.treeview.get_selection()
  self.treeselection.connect("changed", self.tree_row_selection)
  self.tvcolumn = gtk.TreeViewColumn('Feeds')
  # Add tvcolumn to treeview
  self.treeview.append_column(self.tvcolumn)
  # CellRenderers para Iconos y Texto
  self.cellpb = gtk.CellRendererPixbuf()
  self.cell = gtk.CellRendererText()
  # Añadimos las cells a la tvcolumn
  self.tvcolumn.pack_start(self.cellpb, False)
  self.tvcolumn.pack_start(self.cell, True)
  if gtk.gtk_version[1] < 2:
     self.tvcolumn.set_cell_data_func(self.cellpb, self.make_pb)
  else:
     self.tvcolumn.set_attributes(self.cellpb, stock_id=1)
  self.tvcolumn.set_attributes(self.cell, text=0)
  # Allow sorting on the column
  self.tvcolumn.set_sort_column_id(0)
  # Allow drag and drop reordering of rows
  self.treeview.set_reorderable(True)
  self.treeview_setup_dnd(self.treeview)
  self.scrolled_window1 = gtk.ScrolledWindow()
  self.scrolled_window1.add_with_viewport(self.treeview)
  self.scrolled_window1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
  self.scrolled_window1.set_size_request(175,50) # Sets an acceptable tree sizing
  self.hpaned.add1(self.scrolled_window1)

  ########################
  # PARTE 2 (entry list) #
  ########################
  # Creación del VPaned
  self.vpaned = gtk.VPaned()
  # Creación de los 2 elementos restantes: la lista y el browser.
  # Create a liststore
  # Campos: fecha, flag_importante, titulo, font-style, id_entry/articulo
  self.liststore = gtk.ListStore(str, bool, str, str, int)
  # create the TreeView using liststore
  self.treeview2 = gtk.TreeView(self.liststore)
  self.treeview2.set_rules_hint(True) # differentiate rows...
  self.treeview2.connect("button_press_event", self.tree2_button_press_event)
  self.treeselection2 = self.treeview2.get_selection()
  self.treeselection2.connect("changed", self.list_row_selection)

  # Create CellRenderers to render the data
  self.cellt = gtk.CellRendererToggle()
  self.cellt.set_property('activatable', True)
  self.cellt.connect('toggled', self.toggle_importante, self.liststore) # toggle signal capture
  self.celldate = gtk.CellRendererText()
  self.celltitle = gtk.CellRendererText()

  # Create the TreeViewColumns to display the data
  self.image = gtk.Image()
  self.image.set_from_stock(gtk.STOCK_MEDIA_RECORD, gtk.ICON_SIZE_MENU) # Record icon
  self.image.show() # Sin esto, no aparece!!! :S
  self.tvcolumn_important = gtk.TreeViewColumn(None, self.cellt)
  self.tvcolumn_important.set_widget(self.image)
  ###self.tvcolumn_important = gtk.TreeViewColumn('')
  self.tvcolumn_fecha = gtk.TreeViewColumn('Fecha', self.celldate, text=0, font=3)
  self.tvcolumn_titulo = gtk.TreeViewColumn('Título', self.celltitle, text=2, font=3)
  # Append data to the liststore
  ###self.liststore = self.populate_entries(None) # Propaga las entradas de cada feed
  # (...)
  # Add columns to treeview
  self.treeview2.append_column(self.tvcolumn_important)
  self.treeview2.append_column(self.tvcolumn_fecha)
  self.treeview2.append_column(self.tvcolumn_titulo)
  # Add the cells to the columns
  ###self.tvcolumn_important.pack_start(self.cellt, False)
  # En este caso, no necesitamos lo siguiente (definimos su cell al crear self.tvcolumn_titulo)
  ###self.tvcolumn_fecha.pack_start(self.celldate, True)
  ###self.tvcolumn_titulo.pack_start(self.celltitle, True)
  self.tvcolumn_important.add_attribute(self.cellt, "active", 1)
  # Y esto tampoco!
  ###self.tvcolumn_fecha.set_attributes(self.celldate, text=0)
  ###self.tvcolumn_titulo.set_attributes(self.celltitle, text=2) # ORIG
  # make treeview searchable
  self.treeview2.set_search_column(2)
  # Allow sorting on the column
  self.tvcolumn_fecha.set_sort_column_id(0)
  self.tvcolumn_titulo.set_sort_column_id(2)
  self.scrolled_window2 = gtk.ScrolledWindow()
  self.scrolled_window2.add_with_viewport(self.treeview2)
  self.scrolled_window2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
  self.scrolled_window2.set_size_request(300,100) # Sets an acceptable list sizing
  self.vpaned.add1(self.scrolled_window2)

  ###########
  # PARTE 3 #
  ###########
  self.button2 = gtk.Button("Button 2")
  #self.button2.connect("clicked", self.callback, "button 2")
  self.vpaned.add2(self.button2)
  self.hpaned.add2(self.vpaned)
  
  self.vbox.pack_start(self.hpaned, True, True, 0)
  self.window.add(self.vbox)

  # Create TrayIcon
  self.create_trayicon()
  self.window.show_all()

 def create_trayicon(self):
  """Creates the TrayIcon of the app."""
  self.statusicon = gtk.StatusIcon()
  self.statusicon.set_tooltip('Náufrago!')
  self.statusicon.set_from_file('Viking_Longship.svg')
  self.statusicon.set_visible(True)
  self.window.connect('hide', self.statusicon_activate) # Hide window associated
  self.statusicon.connect('activate', self.statusicon_activate) # StatusIcon associated

 def populate_feeds(self):
  """Obtains the user feed tree structure"""
  conn = sqlite3.connect(db_path)
  conn2 = sqlite3.connect(db_path)
  cursor = conn.cursor()
  cursor2 = conn2.cursor()
  self.treestore = gtk.TreeStore(str, str, 'gboolean', int)
  cursor.execute('SELECT id,nombre FROM categoria ORDER BY nombre ASC')
  for row in cursor:
   dad = self.treestore.append(None, [row[1], gtk.STOCK_OPEN, True, row[0]])
   cursor2.execute('SELECT id,nombre FROM feed WHERE id_categoria = ' + str(row[0]) + ' ORDER BY nombre ASC')
   for row2 in cursor2:
    son = self.treestore.append(dad, [row2[1], gtk.STOCK_NEW, True, row[0]])
  cursor2.close()
  cursor.close()
  return self.treestore

 def populate_entries(self, str):
  """Obtains the entries of the selected feed"""
  font_style=''
  importante=False
  self.liststore.clear()
  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()
  cursor.execute('SELECT id FROM feed WHERE nombre = ?', [str])
  print 'SELECT id FROM feed WHERE nombre = %s' % (str)
  row = cursor.fetchone()
  print row
  cursor.execute('SELECT id,titulo,fecha,leido,importante FROM articulo WHERE id_feed = ? ORDER BY fecha DESC', [row[0]])
  print 'SELECT id,titulo,fecha,leido,importante FROM articulo WHERE id_feed = %s ORDER BY fecha DESC' % (row[0])
  for row in cursor:
   now = datetime.datetime.now().strftime("%Y-%m-%d")
   fecha = datetime.datetime.fromtimestamp(row[2]).strftime("%Y-%m-%d")
   if now == fecha: fecha = 'Hoy'
   if row[3] == 1: font_style='normal'
   else: font_style='bold'
   if row[4] == 1: importante=True
   else: importante=False
   self.liststore.append([fecha, importante, row[1], font_style, row[0]])
  cursor.close()

 def add_category(self, data=None):
  """Adds/edits a category to/from the user feed tree structure"""
  dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, None)
  entry = gtk.Entry()

  if(data is not None): # Modo edición I
   entry.set_text(data)
   dialog.set_markup('Cambia el nombre de la <b>categoría</b> a:')
  else:
   dialog.set_markup('Por favor, introduce la <b>categoría</b>:')

  # These are for 'capturing Enter' as OK
  dialog.set_default_response(gtk.RESPONSE_OK) # Sets default response
  entry.set_activates_default(True) # Activates default response

  dialog.vbox.pack_end(entry, True, True, 0)
  dialog.show_all()
  response = dialog.run()
  text = entry.get_text()
  dialog.destroy()

  if((text != '') and (response == gtk.RESPONSE_OK)):
   conn = sqlite3.connect(db_path)
   cursor = conn.cursor()
   # Create category in the database (if it does not exist!)
   cursor.execute('SELECT id FROM categoria WHERE nombre = ?', [text])
   if(cursor.fetchone() is None):
    if(data is not None): # Modo edición II
     if(text != data):
      cursor.execute('UPDATE categoria SET nombre = ? WHERE nombre = ?', [text,data])
      (model, iter) = self.treeselection.get_selected()
      model.set(iter, 0, text)
    else:
     cursor.execute('SELECT MAX(id) FROM categoria')
     row = cursor.fetchone()
     dad = self.treestore.append(None, [text, gtk.STOCK_OPEN, True, row[0]+1])
     cursor.execute('INSERT INTO categoria VALUES(null, ?)', [text])
    conn.commit()
   cursor.close()

 def delete_category(self, data=None):
  """Deletes a category from the user feed tree structure"""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   #text = self.treestore.get_value(iter, 0)
   if(model.iter_depth(iter) == 0): # ... y es un nodo padre
    id_categoria = self.treestore.get_value(iter, 3)
    #if(text != 'General'):
    if(id_categoria != 1):
     dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, None)
     dialog.set_markup('¿Borrar la <b>categoría</b> seleccionada?')
     dialog.format_secondary_markup('<b>Atención:</b> todos los RSS contenidos en ella serán borrados. ¿Proceder?')
     dialog.show_all()
     response = dialog.run()
     dialog.destroy()

     if(response == gtk.RESPONSE_OK):
      # De cara al model, esto es suficiente :-o
      result = self.treestore.remove(iter)
      conn = sqlite3.connect(db_path)
      cursor = conn.cursor()
      # Esto eliminará todo lo que la categoria contenga: feeds y entries. Pero
      # antes hay que corregir lo que está fallando...
      #
      cursor.execute('SELECT id FROM feed WHERE id_categoria = ?', [id_categoria])
      feed_ids = ''
      for row in cursor:
       feed_ids += str(row[0])+','
      if(feed_ids != ''):
       print 'Eliminando entries...'
       feed_ids = feed_ids[0:-1]
       q = 'DELETE FROM articulo WHERE id_feed IN (' + feed_ids+ ')'
       cursor.execute(q)
      print 'Eliminando feeds...'
      cursor.execute('DELETE FROM feed WHERE id_categoria = ?', [id_categoria])
      print 'Eliminando categoria...'
      cursor.execute('DELETE FROM categoria WHERE id = ?', [id_categoria])
      conn.commit()
      cursor.close()
    else:
     self.warning_message('¡La categoría General no puede ser eliminada!')
   else:
    self.warning_message('¡Debe seleccionar una carpeta de categoría!')
  else:
   self.warning_message('¡Debe seleccionar una carpeta de categoría!')

 def add_feed(self, data=None):
  """Adds a feed to the user feed tree structure"""
  dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, None)
  entryName = gtk.Entry()
  entryURL = gtk.Entry()
  labelName = gtk.Label('Nombre ')
  labelURL = gtk.Label('URL       ')

  if(data is not None): #  Modo edición I
   entryName.set_text(data)
   conn = sqlite3.connect(db_path)
   cursor = conn.cursor()
   cursor.execute('SELECT url FROM feed WHERE nombre = ?', [data])
   print 'SELECT url FROM feed WHERE nombre = %s' % data
   url = cursor.fetchone()
   cursor.close()
   entryURL.set_text(url[0])
   dialog.set_markup('Cambia los datos del <b>feed</b>:')
  else:
   dialog.set_markup('Por favor, introduce los datos del <b>feed</b>:')

  hbox1 = gtk.HBox()
  hbox1.pack_start(labelName, True, True, 0)
  hbox1.pack_start(entryName, True, True, 0)
  dialog.vbox.pack_start(hbox1, True, True, 0)
  hbox2 = gtk.HBox()
  hbox2.pack_start(labelURL, True, True, 0)
  hbox2.pack_start(entryURL, True, True, 0)
  dialog.vbox.pack_start(hbox2, True, True, 0)
  # These are for 'capturing Enter' as OK
  dialog.set_default_response(gtk.RESPONSE_OK) # Sets default response
  entryName.set_activates_default(True) # Activates default response for this entry
  entryURL.set_activates_default(True) # Activates default response for this entry
  dialog.show_all()
  response = dialog.run()
  textName = entryName.get_text()
  textURL = entryURL.get_text()
  dialog.destroy()

  if((textName != '') and (textURL != '') and (response == gtk.RESPONSE_OK)):
   conn = sqlite3.connect(db_path)
   cursor = conn.cursor()
   (model, iter) = self.treeselection.get_selected()
   if(data is not None): # Modo edición II
    cursor.execute('UPDATE feed SET nombre = ?,url = ? WHERE nombre = ?', [textName,textURL,data])
    print 'UPDATE feed SET nombre = %s,url = %s WHERE nombre = %s' % (textName,textURL,data)
    model.set(iter, 0, textName)
   else:
    # Create feed in the database (if it does not exist!)
    cursor.execute('SELECT id FROM feed WHERE nombre = ?', [textName])
    if(cursor.fetchone() is None):
     # Lo colocamos en la categoría seleccionada, o en 'General' (default) si no la hubiere
     id_categoria = 1
     if(iter is not None): # Si hay algún nodo seleccionado..
      if(model.iter_depth(iter) == 0): # ... y es un nodo padre
       id_categoria = self.treestore.get_value(iter, 3)
      elif(model.iter_depth(iter) == 1): # ... y es un nodo hijo
       iter = model.iter_parent(iter) # Cogemos al padre para usarlo como categoría destino
       id_categoria = self.treestore.get_value(iter, 3)
      else:
       iter = self.treestore.get_iter((0,)) # Hallamos el iter del nodo 'General'
     cursor.execute('SELECT MAX(id) FROM feed')
     row = cursor.fetchone()
     son = self.treestore.append(iter, [textName, gtk.STOCK_NEW, True, row[0]+1])
     cursor.execute('INSERT INTO feed VALUES(null, ?, ?, ?)', [textName,textURL,id_categoria])
   conn.commit()
   cursor.close()

 def delete_feed(self, data=None):
  """Deletes a feed from the user feed tree structure"""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   if(model.iter_depth(iter) == 1): # ... y es un nodo hijo
    dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, None)
    dialog.set_markup('¿Borrar el <b>feed</b> seleccionado?')
    dialog.show_all()
    response = dialog.run()
    dialog.destroy()

    if(response == gtk.RESPONSE_OK):
     text = self.treestore.get_value(iter, 0)
     print 'Eliminando feed ' + text + '...'
     result = self.treestore.remove(iter)
     self.liststore.clear() # Limpieza de tabla de entries/articulos
     conn = sqlite3.connect(db_path)
     cursor = conn.cursor()
     cursor.execute('DELETE FROM feed WHERE nombre = ?', [text])
     conn.commit()
     cursor.close()
   else:
    self.warning_message('¡Debe seleccionar un feed!')
  else:
   self.warning_message('¡Debe seleccionar un feed!')

 def edit(self, data=None):
  """Edits a tree node, whether it is root or leaf."""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   text = self.treestore.get_value(iter, 0)
   if(model.iter_depth(iter) == 0): # ... y es un nodo padre
    self.add_category(text)
   elif(model.iter_depth(iter) == 1): # ... y es un nodo hijo
    self.add_feed(text)
  else:
   self.warning_message('¡Debe seleccionar una carpeta de categoría o un feed a editar!')

 def treeview_expand_to_path(self, treeview, path):
  """Expand row at path, expanding any ancestors as needed.
  This function is provided by gtk+ >=2.2, but it is not yet wrapped
  by pygtk 2.0.0."""
  for i in range(len(path)):
   treeview.expand_row(path[:i+1], open_all=False)

 def treeview_copy_row(self, treeview, model, source, target, drop_position):
  """Copy tree model rows from treeiter source into, before or after treeiter target.
  All children of the source row are also copied and the
  expanded/collapsed status of each row is maintained."""
  source_row = model[source]
  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()
  if drop_position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE:
   print '---Prepend---'
   new = model.prepend(parent=target, row=source_row)
  elif drop_position == gtk.TREE_VIEW_DROP_INTO_OR_AFTER:
   print '---Append---'
   new = model.append(parent=target, row=source_row)
  #elif drop_position == gtk.TREE_VIEW_DROP_BEFORE:
  # new = model.insert_before(parent=None, sibling=target, row=source_row)
  # print 'option c'
  #elif drop_position == gtk.TREE_VIEW_DROP_AFTER:
  # new = model.insert_after(parent=None, sibling=target, row=source_row)
  # print 'option d'
  parent_value = str(model.get_value(target, 0))
  row_value = str(model.get_value(source_row.iter, 0))
  print 'Parent_value: ' + parent_value
  print 'Row_value: ' + row_value
  print "UPDATE feed SET id_categoria = (SELECT id FROM categoria WHERE nombre = %s) WHERE id = (SELECT id FROM feed WHERE nombre = %s)" % (parent_value,row_value)
  cursor.execute('UPDATE feed SET id_categoria = (SELECT id FROM categoria WHERE nombre = ?) WHERE id = (SELECT id FROM feed WHERE nombre = ?)', [parent_value,row_value])
  conn.commit()
  cursor.close()

  # If the source row is expanded, expand the newly copied row
  # also.  We must add at least one child before we can expand,
  # so we expand here after the children have been copied.
  source_is_expanded = treeview.row_expanded(model.get_path(source))
  if source_is_expanded:
   self.treeview_expand_to_path(treeview, model.get_path(new))

 def checkSanity(self, model, iter_to_copy, target_iter):
  """Prevents that a node can be copied inside himself (anti-recursivity!),
  and also checks for application node logic."""

  iter_to_copy_value = model.get_value(iter_to_copy, 0)
  target_iter_value = model.get_value(target_iter, 0)

  path_of_iter_to_copy = model.get_path(iter_to_copy)
  path_of_target_iter = model.get_path(target_iter)

  if((path_of_target_iter[0:len(path_of_iter_to_copy)] == path_of_iter_to_copy) or # anti-recursive
    (len(path_of_iter_to_copy) == 1) or # source is parent
    (len(path_of_target_iter) == 2) or # dest is child
    (self.treestore.is_ancestor(target_iter, iter_to_copy))): # dest is already child's parent
     return False
  else:
   return True

 def treeview_on_drag_data_received(self, treeview, drag_context, x, y, selection_data, info, eventtime):
  """Handler for 'drag-data-received' that moves dropped TreeView rows."""
  model, source = treeview.get_selection().get_selected()
  # Workaround for DnD at the end of the tree.
  temp = treeview.get_dest_row_at_pos(x, y)
  if temp != None:
   target_path, drop_position = temp
  else:
   target_path, drop_position = (len(model)-1,), gtk.TREE_VIEW_DROP_AFTER

  target = model.get_iter(target_path)
  if self.checkSanity(model, source, target):
   self.treeview_copy_row(treeview, model, source, target, drop_position)
   # If the drop has created a new child (drop into), expand
   # the parent so the user can see the newly copied row.
   if(drop_position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE or drop_position == gtk.TREE_VIEW_DROP_INTO_OR_AFTER):
    treeview.expand_row(target_path, open_all=False)
    # Finish the drag and have gtk+ delete the drag source rows.
    drag_context.finish(success=True, del_=True, time=eventtime)
   else:
    drag_context.finish(success=False, del_=False, time=eventtime)

 def treeview_setup_dnd(self, treeview):
  """Setup a treeview to move rows using drag and drop."""
  target_entries = [('example', gtk.TARGET_SAME_WIDGET, 0)]
  # target_entries=[(drag type string, target_flags, application integer ID used for identification purposes)]
  # Drag start operation (origin)
  treeview.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, target_entries, gtk.gdk.ACTION_MOVE)
  # Params: 1st mouse button, target_entries (ver arriba), type of action to do
  # Drag end operation (destination)
  treeview.enable_model_drag_dest(target_entries, gtk.gdk.ACTION_MOVE)
  # Params: target_entries (ver arriba), type of action to do
  treeview.connect('drag-data-received', self.treeview_on_drag_data_received)

 def tree_button_press_event(self, treeview, event):
  """Fires the tree menu popup. This handles the feed list options.
  Showing feed entries is handled through *tree_row_selection* handler
  callbacked by the *change* event."""
  if event.button == 3:
   x = int(event.x)
   y = int(event.y)
   time = event.time
   pthinfo = treeview.get_path_at_pos(x, y)
   if pthinfo is not None:
    path, col, cellx, celly = pthinfo
    treeview.grab_focus()
    treeview.set_cursor(path, col, 0)

    tree_menu = gtk.Menu()
    # Create the menu items
    new_feed_item = gtk.ImageMenuItem("Nuevo feed")
    icon = new_feed_item.render_icon(gtk.STOCK_FILE, gtk.ICON_SIZE_BUTTON)
    new_feed_item.set_image(gtk.image_new_from_pixbuf(icon))
    new_category_item = gtk.ImageMenuItem("Nueva categoría")
    icon = new_category_item.render_icon(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_BUTTON)
    new_category_item.set_image(gtk.image_new_from_pixbuf(icon))
    delete_feed_item = gtk.ImageMenuItem("Eliminar feed")
    icon = delete_feed_item.render_icon(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON)
    delete_feed_item.set_image(gtk.image_new_from_pixbuf(icon))
    delete_category_item = gtk.ImageMenuItem("Eliminar categoría")
    icon = delete_category_item.render_icon(gtk.STOCK_CLOSE, gtk.ICON_SIZE_BUTTON)
    delete_category_item.set_image(gtk.image_new_from_pixbuf(icon))
    edit_item = gtk.ImageMenuItem("Editar")
    icon = edit_item.render_icon(gtk.STOCK_EDIT, gtk.ICON_SIZE_BUTTON)
    edit_item.set_image(gtk.image_new_from_pixbuf(icon))
    # Add them to the menu
    tree_menu.append(new_feed_item)
    tree_menu.append(new_category_item)
    tree_menu.append(delete_feed_item)
    tree_menu.append(delete_category_item)
    tree_menu.append(edit_item)
    # Attach the callback functions to the activate signal
    new_feed_item.connect_object("activate", self.add_feed, None)
    new_category_item.connect_object("activate", self.add_category, None)
    delete_feed_item.connect_object("activate", self.delete_feed, None)
    delete_category_item.connect_object("activate", self.delete_category, None)
    edit_item.connect_object("activate", self.edit, None)
    tree_menu.show_all()
    tree_menu.popup(None, None, None, event.button, event.get_time())
   return True

 def tree2_button_press_event(self, treeview, event):
  """Fires the tree2 menu popup. This one handles entries options."""
  if event.button == 3:
   x = int(event.x)
   y = int(event.y)
   time = event.time
   pthinfo = treeview.get_path_at_pos(x, y)
   if pthinfo is not None:
    path, col, cellx, celly = pthinfo
    treeview.grab_focus()
    treeview.set_cursor(path, col, 0)

    tree_menu = gtk.Menu()
    # Create the menu items
    toggle_leido_item = gtk.ImageMenuItem("Alternar leído/no leído")
    icon = toggle_leido_item.render_icon(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON)
    toggle_leido_item.set_image(gtk.image_new_from_pixbuf(icon))
    toggle_todos_leido_item = gtk.ImageMenuItem("Alternar leído/no leído (todos)")
    icon = toggle_todos_leido_item.render_icon(gtk.STOCK_SELECT_ALL, gtk.ICON_SIZE_BUTTON)
    toggle_todos_leido_item.set_image(gtk.image_new_from_pixbuf(icon))
    # Add them to the menu
    tree_menu.append(toggle_leido_item)
    tree_menu.append(toggle_todos_leido_item)
    # Attach the callback functions to the activate signal
    #toggle_leido_item.connect_object("activate", self.toggle_leido, None)
    #toggle_todos_leido_item.connect_object("activate", self.callback, None)
    toggle_leido_item.connect("activate", self.toggle_leido, 'single')
    toggle_todos_leido_item.connect("activate", self.toggle_leido, 'all')
    tree_menu.show_all()
    tree_menu.popup(None, None, None, event.button, event.get_time())
   return True

 def get_feed(self, str):
  """Obtains & stores the feeds (thanks feedparser!)"""
  conn = sqlite3.connect(db_path)
  conn2 = sqlite3.connect(db_path)
  cursor = conn.cursor()
  cursor2 = conn2.cursor()
  cursor.execute('SELECT id,url FROM feed WHERE nombre = ?', [str])
  for row in cursor:
   print 'Obteniendo feed de ' + str + ' (' + row[1] + ') ...'
   d = feedparser.parse(row[1])
   count = len(d.entries)
   for i in range(0, count):
    print 'Comprobando existencia del artículo...'
    dp = d.entries[i].date_parsed
    secs = time.mktime(datetime.datetime(dp[0], dp[1], dp[2], dp[3], dp[4], dp[5], dp[6]).timetuple())
    cursor2.execute('SELECT id FROM articulo WHERE fecha = ? AND id_feed = ?', [secs,row[0]])
    print 'SELECT id FROM articulo WHERE fecha = %s AND id_feed = %s' % (secs,row[0])
    if(cursor2.fetchone() is None):
     print 'No encontrado, salvando en BD...'
     cursor2.execute('INSERT INTO articulo VALUES(null, ?, ?, ?, ?, 0, 0, ?)', [d.entries[i].title.encode('utf-8'),d.entries[i].description.encode('utf-8'),secs,d.entries[i].link.encode('utf-8'),row[0]])
     print 'INSERT INTO articulo VALUES(null, %s, %s, %s, %s, 0, 0, %s)' % (d.entries[i].title.encode('utf-8'),d.entries[i].description.encode('utf-8'),secs,d.entries[i].link.encode('utf-8'),row[0])
     conn2.commit()
    else:
     print 'Encontrado, skipping...'
   if(count == 0):
    print 'No se pudo recuperar nada: URI incorrecta o site offline.'
  cursor2.close()
  cursor.close()

 # INIT #
 ########

 def __init__(self):

  # Crea la base para la aplicación (directorio + feed de regalo!), si no la hubiere
  self.create_base()
  # Obtiene la config de la app
  self.get_config()
  # Creamos la ventana principal
  self.create_main_window()

def main():
 gtk.main()
 
if __name__ == "__main__":
 hello = Naufrago()
 main()

