#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Naufrago RSS Reader, by jors ( worbynet at gmail dot com ), 14-05-2010
#
# Thanks to:
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
import webkit
import gobject
import threading
import webkit
import webbrowser
import pango
from xml.etree import ElementTree

window_visible = True
current_path = os.getcwd()
# On the final release, it should be this:
#db_path = current_path + '/.naufrago/naufrago.db'
index_path = current_path + '/index.html'
db_path = os.getenv("HOME") + '/.naufrago/naufrago.db'
ABOUT_PAGE = '''<html>
               <body>
                <h1>Náufrago!</h1>
                <p>Lector simple de RSS, by jors/qat :)</p>
                <p>Licenciado bajo los términos de la <a href="http://www.gnu.org/licenses/gpl-3.0.html">GPLv3</a>.</p>
               </body>
              </html>'''

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
  """Toggle entries between read/non-read states."""
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

 def abrir_browser(self, event=None, data=None):
  """Opens a given url in the user sensible web browser."""
  (model, iter) = self.treeselection2.get_selected()
  if(iter is not None): # Hay alguna fila de la lista seleccionada
   id_articulo = self.liststore.get_value(iter, 4)
   conn = sqlite3.connect(db_path)
   cursor = conn.cursor()
   cursor.execute('SELECT enlace FROM articulo WHERE id = ?', [id_articulo])
   link = cursor.fetchone()[0]
   webbrowser.open_new(link) # new win
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
   
   self.headerlink.set_markup('<b><u><span foreground="blue">'+titulo+'</span></u></b>');
   self.headerlink.set_justify(gtk.JUSTIFY_CENTER)
   self.headerlink.set_ellipsize(pango.ELLIPSIZE_END)
   self.eb.show()
   self.eb_image_zoom.show()

   conn = sqlite3.connect(db_path)
   cursor = conn.cursor()
   # Turno de webkit...
   cursor.execute('SELECT leido,contenido FROM articulo WHERE id = ?', [id_articulo])
   row = cursor.fetchone()
   self.webview.load_string(row[1], "text/html", "utf-8", "about")
   # That won't work because it's not ported to pywevkitgtk :(
   #self.webframe = self.webview.get_main_frame()
   #self.webframe.load_alternate_string("UNREACHABLE by jors", "text/html", "utf-8", "about")
   # Si no estaba leído, marcarlo como tal.
   if(row[0] == 0):
    cursor.execute('UPDATE articulo SET leido=1 WHERE id = ?', [id_articulo])
   conn.commit()
   cursor.close()

 def tree_row_selection(self, event):
  """Feed row change detector; triggers entry visualization on the list."""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Hay algún nodo seleccionado
   row_name = self.treestore.get_value(iter, 0)
   ###print 'Nodo *' + row_name + '* seleccionado'
   if(model.iter_depth(iter) == 1): # Si es hoja, presentar entradas
    print 'Feed *' + row_name + '* seleccionado'
    self.scrolled_window2.set_size_request(300,100)
    self.scrolled_window2.show()
    # Instead of updating the feed, it should only show its entries on the liststore!!!
    ###self.get_feed(row_name) # En todo caso, self.get_feed(id_feed)
    id_feed = self.treestore.get_value(iter, 2)
    self.populate_entries(id_feed)
   elif(model.iter_depth(iter) == 0): # Si es padre, limpliar 
    self.liststore.clear() # Limpieza de tabla de entries/articulos
    print 'Categoría *' + row_name + '* seleccionada'
    self.scrolled_window2.set_size_request(0,0)
    self.scrolled_window2.hide()
   #self.webview.load_string(ABOUT_PAGE, "text/html", "utf-8", "about") # Limpieza ventana browser
   # This is usefull to store an URI (in case of reloads):
   self.webview.load_string(ABOUT_PAGE, "text/html", "utf-8", "file://"+index_path)
   self.eb.hide()
   self.eb_image_zoom.hide()

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

  # Deactivates tray icon blinking
  self.statusicon.set_blinking(False)

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
  about.set_logo(gtk.gdk.pixbuf_new_from_file("Viking_Longship.svg"))
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
      <menuitem action='Importar feeds'/>
      <menuitem action='Exportar feeds'/>
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
            ('Importar feeds', gtk.STOCK_REDO, 'Importar feeds', None, 'Importa una lista de feeds', self.import_feeds),
            ('Exportar feeds', gtk.STOCK_UNDO, 'Exportar feeds', None, 'Exporta la lista de feeds', self.export_feeds),
            ('Salir', gtk.STOCK_QUIT, '_Salir', '<control>S', 'Salir', self.delete_event),
            ('EditarMenu', None, '_Editar'),
            ('Editar', gtk.STOCK_EDIT, '_Editar', '<control>E', 'Edita el elemento seleccionado', self.edit),
            ('Preferencias', gtk.STOCK_EXECUTE, '_Preferencias', '<control>P', 'Muestra las preferencias', self.preferences),
            ('RedMenu', None, '_Red'),
            ('Actualizar', None, '_Actualizar', '<control>A', 'Actualiza el feed seleccionado', self.update_feed),
            ('Actualizar todo', gtk.STOCK_REFRESH, 'Actualiza_r todo', '<control>R', 'Actualiza todos los feeds', self.update_all_feeds),
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
    #os.makedirs(os.getenv("HOME") + '/.naufrago')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executescript('''
     CREATE TABLE config(window_position varchar(16) NOT NULL, window_size varchar(16) NOT NULL, num_entries integer NOT NULL, update_freq integer NOT NULL, init_unfolded_tree integer NOT NULL, init_tray integer NOT NULL);
     CREATE TABLE categoria(id integer PRIMARY KEY, nombre varchar(32) NOT NULL);
     CREATE TABLE feed(id integer PRIMARY KEY, nombre varchar(32) NOT NULL, url varchar(1024) NOT NULL, id_categoria integer NOT NULL);
     CREATE TABLE articulo(id integer PRIMARY KEY, titulo varchar(256) NOT NULL, contenido text, fecha integer NOT NULL, enlace varchar(1024) NOT NULL, leido INTEGER NOT NULL, importante INTEGER NOT NULL, id_feed integer NOT NULL);
     CREATE TABLE imagen(id integer PRIMARY KEY, imagen blob NOT NULL, id_articulo integer NOT NULL);
     INSERT INTO config VALUES('0,0', '600x400', 10, 1, 1, 0);
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
  self.init_unfolded_tree = int(row[4])
  self.init_tray = int(row[5])
  cursor.close()

 def save_config(self):
  """Saves user window configuration"""
  (x, y) = self.window.get_position()
  (w, h) = self.window.get_size()
  position = str(x)+','+str(y)
  size = str(w)+'x'+str(h)
  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()
  cursor.execute('UPDATE config SET window_position = ?, window_size = ?, num_entries = ?, update_freq = ?, init_unfolded_tree = ?, init_tray = ?', [position,size,self.num_entries,self.update_freq,self.init_unfolded_tree,self.init_tray])
  conn.commit()
  cursor.close()

 def purge_entries(self):
  """Purges excedent entries from each feed."""
  updated_feed_ids = []
  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()
  cursor.execute('SELECT id FROM feed')
  feeds = cursor.fetchall()
  for row in feeds:
   cursor.execute('SELECT count(id) FROM articulo WHERE id_feed = ?', [row[0]])
   print 'SELECT count(id) FROM articulo WHERE id_feed = %s' % row[0]
   row2 = cursor.fetchone()
   print 'count(id): ' + str(row2[0])
   print 'self.num_entries: ' + str(self.num_entries)
   if((row2 is not None) and (row2[0]>self.num_entries)):
    excedente = int(row2[0]) - self.num_entries
    cursor.execute('DELETE FROM articulo WHERE id IN (SELECT id FROM articulo WHERE id_feed = ? AND importante = 0 ORDER BY fecha ASC LIMIT ?) AND id_feed = ?', [row[0],excedente,row[0]])
    print 'DELETE FROM articulo WHERE id IN (SELECT id FROM articulo WHERE id_feed = %s AND importante = 0 ORDER BY fecha ASC LIMIT %s) AND id_feed = %s' % (row[0],excedente,row[0])
    conn.commit()
    updated_feed_ids.append(row[0])
  cursor.close()
  # Refresh the model if we have to
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   if(model.iter_depth(iter) == 1): # ... y es un nodo hijo...
    id_feed = self.treestore.get_value(iter, 2)
    if(id_feed in updated_feed_ids):
     self.populate_entries(id_feed)

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
  # Campos: nombre, icono, id_categoria
  self.treestore = gtk.TreeStore(str, str, int)
  ###self.treestore = self.populate_feeds() # Propaga los feeds del usuario
  self.populate_feeds() # Propaga los feeds del usuario
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
  self.scrolled_window1.add(self.treeview)
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
  # Append data to the liststore (not here!)
  # Add columns to treeview
  self.treeview2.append_column(self.tvcolumn_important)
  self.treeview2.append_column(self.tvcolumn_fecha)
  self.treeview2.append_column(self.tvcolumn_titulo)
  self.tvcolumn_important.add_attribute(self.cellt, "active", 1)
  # make treeview searchable
  self.treeview2.set_search_column(2)
  # Allow sorting on the column
  self.tvcolumn_fecha.set_sort_column_id(0)
  self.tvcolumn_titulo.set_sort_column_id(2)
  self.scrolled_window2 = gtk.ScrolledWindow()
  self.scrolled_window2.add(self.treeview2)
  self.scrolled_window2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
  self.scrolled_window2.set_size_request(300,100) # Sets an acceptable list sizing
  self.vpaned.add1(self.scrolled_window2)

  ###########
  # PARTE 3 #
  ###########
  self.scrolled_window3 = gtk.ScrolledWindow()
  self.scrolled_window3.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
  self.webview = webkit.WebView()
  self.webview.set_full_content_zoom(True)
  self.webview.load_string(ABOUT_PAGE, "text/html", "utf-8", "file://"+index_path)
  self.webview.connect_after("populate-popup", self.create_webview_popup)
  self.scrolled_window3.add(self.webview)

  self.vbox2 = gtk.VBox(homogeneous=False, spacing=0)

  self.hbox = gtk.HBox(homogeneous=False, spacing=0)
  self.fullscreen = False
  self.image_zoom = gtk.Image()
  self.image_zoom.set_from_stock(gtk.STOCK_ZOOM_FIT, gtk.ICON_SIZE_MENU) # Record icon
  self.image_zoom.set_tooltip_text("Clic to toggle fullscreen")
  self.eb_image_zoom = gtk.EventBox() # Wrapper for the image to be able to catch 'button_press_event'
  self.eb_image_zoom.add(self.image_zoom)
  self.eb_image_zoom.connect("button_press_event", self.image_zoom_button_press_event)
  self.hbox.pack_start(self.eb_image_zoom, expand=False, fill=False, padding=5)

  self.headerlink = gtk.Label("")
  self.headerlink.set_tooltip_text("Clic to open in new browser")
  self.eb = gtk.EventBox() # Wrapper for the label to be able to catch 'button_press_event'
  self.eb.add(self.headerlink)
  self.eb.connect("button_press_event", self.headerlink_button_press_event)
  self.hbox.pack_start(self.eb, expand=True, fill=True, padding=5) # NEW
  self.vbox2.pack_start(self.hbox, expand=False, fill=False, padding=5) # NEW
  self.vbox2.pack_start(self.scrolled_window3, expand=True, fill=True, padding=0)

  self.vpaned.add2(self.vbox2)
  self.hpaned.add2(self.vpaned)
  
  self.vbox.pack_start(self.hpaned, True, True, 0)
  self.window.add(self.vbox)
  # Create TrayIcon
  self.create_trayicon()
  self.window.show_all()
  # The cursor change has to be done once the affected widget
  # and its parents are shown!
  self.eb.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))
  self.eb.hide() # Specific hiding...
  self.eb_image_zoom.hide()
  self.scrolled_window2.set_size_request(0,0)
  self.scrolled_window2.hide()

  # Finally, check init options!
  self.check_init_options()

 def create_webview_popup(self, view, menu):
  """Creates the webview (browser item) popup menu."""
  zoom_in = gtk.ImageMenuItem(gtk.STOCK_ZOOM_IN)
  zoom_in.connect('activate', self.zoom_in_cb, view)
  menu.append(zoom_in)
  zoom_out = gtk.ImageMenuItem(gtk.STOCK_ZOOM_OUT)
  zoom_out.connect('activate', self.zoom_out_cb, view)
  menu.append(zoom_out)
  zoom_hundred = gtk.ImageMenuItem(gtk.STOCK_ZOOM_100)
  zoom_hundred.connect('activate', self.zoom_hundred_cb, view)
  menu.append(zoom_hundred)
  menu.show_all()
  return False

 def zoom_in_cb(self, menu_item, web_view):
  """Zoom into the page"""
  web_view.zoom_in()

 def zoom_out_cb(self, menu_item, web_view):
  """Zoom out of the page"""
  web_view.zoom_out()

 def zoom_hundred_cb(self, menu_item, web_view):
  """Zoom 100%"""
  if not (web_view.get_zoom_level() == 1.0):
   web_view.set_zoom_level(1.0)

 def check_init_options(self):
  """Checks & applies init options."""
  if(self.init_unfolded_tree == 1): self.treeview.expand_all()
  if(self.init_tray == 1): self.statusicon_activate()

 def create_trayicon(self):
  """Creates the TrayIcon of the app and its popup menu."""
  self.statusicon = gtk.StatusIcon()
  self.statusicon.set_tooltip('Náufrago!')
  self.statusicon.set_from_file('Viking_Longship.svg')
  self.statusicon.set_visible(True)
  self.window.connect('hide', self.statusicon_activate) # Hide window associated
  self.statusicon.connect('activate', self.statusicon_activate) # StatusIcon associated

  # StatusIcon popup menu
  self.statusicon_menu = gtk.Menu()
  # Create the menu items
  update_item = gtk.ImageMenuItem("Actualizar")
  icon = update_item.render_icon(gtk.STOCK_REFRESH, gtk.ICON_SIZE_BUTTON)
  update_item.set_image(gtk.image_new_from_pixbuf(icon))
  quit_item = gtk.ImageMenuItem("Salir")
  icon = quit_item.render_icon(gtk.STOCK_QUIT, gtk.ICON_SIZE_BUTTON)
  quit_item.set_image(gtk.image_new_from_pixbuf(icon))
  # Add them to the menu
  self.statusicon_menu.append(update_item)
  self.statusicon_menu.append(quit_item)
  # Attach the callback functions to the activate signal
  update_item.connect("activate", self.update_all_feeds)
  quit_item.connect("activate", self.delete_event)
  self.statusicon_menu.show_all()
  self.statusicon.connect('popup-menu', self.statusicon_popup_menu)

 def statusicon_popup_menu(self, statusicon, button, time):
  """StatusIcon popup menu launcher."""
  self.statusicon_menu.popup(None, None, None, button, time, self)

 def populate_feeds(self):
  """Obtains the user feed tree structure"""
  conn = sqlite3.connect(db_path)
  conn2 = sqlite3.connect(db_path)
  cursor = conn.cursor()
  cursor2 = conn2.cursor()
  # Campos: nombre, icono, id_categoria
  #self.treestore = gtk.TreeStore(str, str, int)
  cursor.execute('SELECT id,nombre FROM categoria ORDER BY nombre ASC')
  for row in cursor:
   dad = self.treestore.append(None, [row[1], gtk.STOCK_OPEN, row[0]])
   cursor2.execute('SELECT id,nombre FROM feed WHERE id_categoria = ' + str(row[0]) + ' ORDER BY nombre ASC')
   for row2 in cursor2:
    ###son = self.treestore.append(dad, [row2[1], gtk.STOCK_NEW, row[0]])
    son = self.treestore.append(dad, [row2[1], gtk.STOCK_NEW, row2[0]])
  cursor2.close()
  cursor.close()
  return self.treestore

 def populate_entries(self, id_feed):
  """Obtains the entries of the selected feed"""
  font_style=''
  importante=False
  self.liststore.clear()
  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()
  cursor.execute('SELECT id,titulo,fecha,leido,importante FROM articulo WHERE id_feed = ? ORDER BY fecha DESC', [int(id_feed)])
  print 'SELECT id,titulo,fecha,leido,importante FROM articulo WHERE id_feed = %s ORDER BY fecha DESC' % (str(id_feed))
 
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

  if((data is not None) and (type(data) is not gtk.Action)): # Modo edición I
   conn = sqlite3.connect(db_path)
   cursor = conn.cursor()
   cursor.execute('SELECT nombre FROM categoria WHERE id = ?', [data])
   nombre_categoria = cursor.fetchone()[0]
   cursor.close()
   entry.set_text(nombre_categoria)
   dialog.set_title('Editar categoría')
   dialog.set_markup('Cambia el nombre de la <b>categoría</b> a:')
  else:
   dialog.set_title('Añadir categoría')
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
    if((data is not None) and (type(data) is not gtk.Action)): # Modo edición II
     cursor.execute('SELECT nombre FROM categoria WHERE id = ?', [data])
     nombre_categoria = cursor.fetchone()[0]
     if(text != nombre_categoria):
      cursor.execute('UPDATE categoria SET nombre = ? WHERE id = ?', [text,data])
      (model, iter) = self.treeselection.get_selected()
      model.set(iter, 0, text)
    else:
     cursor.execute('SELECT MAX(id) FROM categoria')
     row = cursor.fetchone()
     dad = self.treestore.append(None, [text, gtk.STOCK_OPEN, row[0]+1])
     cursor.execute('INSERT INTO categoria VALUES(null, ?)', [text])
    conn.commit()
   cursor.close()

 def delete_category(self, data=None):
  """Deletes a category from the user feed tree structure"""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   if(model.iter_depth(iter) == 0): # ... y es un nodo padre
    id_categoria = self.treestore.get_value(iter, 2)
    if(id_categoria != 1):
     dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, None)
     dialog.set_title('Eliminar categoría')
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

  if((data is not None) and (type(data) is not gtk.Action)): #  Modo edición I
   conn = sqlite3.connect(db_path)
   cursor = conn.cursor()
   cursor.execute('SELECT url,nombre FROM feed WHERE id = ?', [data])
   row = cursor.fetchone()
   entryName.set_text(row[1])
   entryURL.set_text(row[0])
   cursor.close()
   dialog.set_title('Editar feed')
   dialog.set_markup('Cambia los datos del <b>feed</b>:')
  else:
   dialog.set_title('Añadir feed')
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
   if((data is not None) and (type(data) is not gtk.Action)): # Modo edición II
    cursor.execute('UPDATE feed SET nombre = ?,url = ? WHERE id = ?', [textName,textURL,data])
    print 'UPDATE feed SET nombre = %s,url = %s WHERE id = %s' % (textName,textURL,data)
    model.set(iter, 0, textName)
   else:
    # Create feed in the database (if it does not exist!)
    cursor.execute('SELECT id FROM feed WHERE nombre = ?', [textName])
    if(cursor.fetchone() is None):
     # Lo colocamos en la categoría seleccionada, o en 'General' (default) si no la hubiere
     id_categoria = 1
     if(iter is not None): # Si hay algún nodo seleccionado..
      if(model.iter_depth(iter) == 0): # ... y es un nodo padre
       id_categoria = self.treestore.get_value(iter, 2)
      elif(model.iter_depth(iter) == 1): # ... y es un nodo hijo
       iter = model.iter_parent(iter) # Cogemos al padre para usarlo como categoría destino
       id_categoria = self.treestore.get_value(iter, 2)
      else:
       iter = self.treestore.get_iter((0,)) # Hallamos el iter del nodo 'General'
     else:
      iter = self.treestore.get_iter((0,)) # Hallamos el iter del nodo 'General'
     cursor.execute('SELECT MAX(id) FROM feed')
     row = cursor.fetchone()
     son = self.treestore.append(iter, [textName, gtk.STOCK_NEW, row[0]+1])
     self.treeview.expand_row(model.get_path(iter), open_all=False) # Expand parent!
     cursor.execute('INSERT INTO feed VALUES(null, ?, ?, ?)', [textName,textURL,id_categoria])
   conn.commit()
   cursor.close()

 def delete_feed(self, data=None):
  """Deletes a feed from the user feed tree structure"""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   if(model.iter_depth(iter) == 1): # ... y es un nodo hijo
    dialog = gtk.MessageDialog(self.window, (gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT), gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK_CANCEL, None)
    dialog.set_title('Eliminar feed')
    dialog.set_markup('¿Borrar el <b>feed</b> seleccionado?')
    dialog.show_all()
    response = dialog.run()
    dialog.destroy()

    if(response == gtk.RESPONSE_OK):
     text = self.treestore.get_value(iter, 0)
     id_feed = self.treestore.get_value(iter, 2)
     print 'Eliminando feed ' + text + '...'
     result = self.treestore.remove(iter)
     self.liststore.clear() # Limpieza de tabla de entries/articulos
     conn = sqlite3.connect(db_path)
     cursor = conn.cursor()
     #cursor.execute('DELETE FROM feed WHERE nombre = ?', [text])
     cursor.execute('DELETE FROM feed WHERE id = ?', [id_feed])
     cursor.execute('DELETE FROM articulo WHERE id_feed = ?', [id_feed])
     conn.commit()
     cursor.close()
   else:
    self.warning_message('¡Debe seleccionar un feed!')
  else:
   self.warning_message('¡Debe seleccionar un feed!')

 def delete(self, data=None):
  """Summons deleting feed or category, depending on selection."""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   if(model.iter_depth(iter) == 0): # Si es un nodo padre...
    self.delete_category()
   if(model.iter_depth(iter) == 1): # ... y es un nodo hijo
    self.delete_feed()

 def edit(self, data=None):
  """Edits a tree node, whether it is root or leaf."""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   id_categoria_o_feed = model.get_value(iter, 2)
   print 'id_categoria_o_feed: ' + str(id_categoria_o_feed)
   if(model.iter_depth(iter) == 0): # ... y es un nodo padre
    self.add_category(id_categoria_o_feed)
   elif(model.iter_depth(iter) == 1): # ... y es un nodo hijo
    self.add_feed(id_categoria_o_feed)
  else:
   self.warning_message('¡Debe seleccionar una carpeta de categoría o un feed a editar!')

 def preferences(self, data=None):
  """Preferences dialog."""
  dialog = gtk.Dialog("Preferencias", None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                   (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
  dialog.set_border_width(5)
  dialog.set_resizable(False)
  dialog.set_has_separator(False)
  
  hbox = gtk.HBox()
  label = gtk.Label("Número de entradas por feed")
  hbox.pack_start(label, True, True, 2)
  # Spin button
  adjustment = gtk.Adjustment(value=10, lower=10, upper=100, step_incr=10, page_incr=10, page_size=0)
  spin_button = gtk.SpinButton(adjustment=adjustment, climb_rate=0.0, digits=0)
  spin_button.set_numeric(numeric=True) # Only numbers can be typed
  spin_button.set_update_policy(gtk.UPDATE_IF_VALID) # Only update on valid changes
  spin_button.set_value(self.num_entries)
  hbox.pack_start(spin_button, True, True, 2)
  dialog.vbox.pack_start(hbox)

  hbox2 = gtk.HBox()
  label2 = gtk.Label("Actualizar cada (en horas)")
  hbox2.pack_start(label2, True, True, 2)
  # Spin button 2
  adjustment2 = gtk.Adjustment(value=1, lower=1, upper=24, step_incr=1, page_incr=1, page_size=0)
  spin_button2 = gtk.SpinButton(adjustment=adjustment2, climb_rate=0.0, digits=0)
  spin_button2.set_numeric(numeric=True) # Only numbers can be typed
  spin_button2.set_update_policy(gtk.UPDATE_IF_VALID) # Only update on valid changes
  spin_button2.set_value(self.update_freq)
  hbox2.pack_start(spin_button2, True, True, 2)
  dialog.vbox.pack_start(hbox2)

  frame = gtk.Frame("Inicio")
  frame.set_border_width(5)
  vbox2 = gtk.VBox(homogeneous=True)
  align = gtk.Alignment()
  align.set_padding(0, 0, 15, 0)
  checkbox = gtk.CheckButton("Iniciar con árbol desplegado")
  if(self.init_unfolded_tree == 1): checkbox.set_active(True)
  else: checkbox.set_active(False)
  vbox2.pack_start(checkbox, True, True, 5)
  checkbox2 = gtk.CheckButton("Iniciar como Tray Icon")
  if(self.init_tray == 1): checkbox2.set_active(True)
  else: checkbox2.set_active(False)
  vbox2.pack_start(checkbox2, True, True, 5)
  align.add(vbox2)
  frame.add(align)
  dialog.vbox.pack_start(frame)

  dialog.show_all()
  response = dialog.run() # Dialog loop
  dialog.destroy()

  if(response == gtk.RESPONSE_ACCEPT):
   # Purge excedent entries in case of decreasing their number in configuration
   num_entries_prev = self.num_entries
   self.num_entries = spin_button.get_value_as_int()
   if self.num_entries < num_entries_prev:
    self.purge_entries()
   self.update_freq = spin_button2.get_value_as_int()
   if(checkbox.get_active()): self.init_unfolded_tree = 1
   else: self.init_unfolded_tree = 0
   if(checkbox2.get_active()): self.init_tray = 1
   else: self.init_tray = 0
   self.save_config()

# def treeview_expand_to_path(self, treeview, path):
#  """Expand row at path, expanding any ancestors as needed.
#  This function is provided by gtk+ >=2.2, but it is not yet wrapped
#  by pygtk 2.0.0."""
#  for i in range(len(path)):
#   treeview.expand_row(path[:i+1], open_all=False)

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
   #self.treeview_expand_to_path(treeview, model.get_path(new))
   self.treeview.expand_row(model.get_path(new), open_all=False)

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
   # Some cleaning...
   self.liststore.clear()
   self.eb.hide()
   self.eb_image_zoom.hide()
   self.webview.load_string(ABOUT_PAGE, "text/html", "utf-8", "file://"+index_path)
   self.scrolled_window2.set_size_request(0,0)
   self.scrolled_window2.hide()

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
    update_item = gtk.ImageMenuItem("Actualizar")
    icon = update_item.render_icon(gtk.STOCK_REFRESH, gtk.ICON_SIZE_BUTTON)
    update_item.set_image(gtk.image_new_from_pixbuf(icon))
    new_feed_item = gtk.ImageMenuItem("Nuevo feed")
    icon = new_feed_item.render_icon(gtk.STOCK_FILE, gtk.ICON_SIZE_BUTTON)
    new_feed_item.set_image(gtk.image_new_from_pixbuf(icon))
    new_category_item = gtk.ImageMenuItem("Nueva categoría")
    icon = new_category_item.render_icon(gtk.STOCK_DIRECTORY, gtk.ICON_SIZE_BUTTON)
    new_category_item.set_image(gtk.image_new_from_pixbuf(icon))
    delete_item = gtk.ImageMenuItem("Eliminar")
    icon = delete_item.render_icon(gtk.STOCK_CLOSE, gtk.ICON_SIZE_BUTTON)
    delete_item.set_image(gtk.image_new_from_pixbuf(icon))
    edit_item = gtk.ImageMenuItem("Editar")
    icon = edit_item.render_icon(gtk.STOCK_EDIT, gtk.ICON_SIZE_BUTTON)
    edit_item.set_image(gtk.image_new_from_pixbuf(icon))
    # Add them to the menu
    tree_menu.append(update_item)
    tree_menu.append(new_feed_item)
    tree_menu.append(new_category_item)
    tree_menu.append(delete_item)
    tree_menu.append(edit_item)
    # Attach the callback functions to the activate signal
    update_item.connect_object("activate", self.update_feed, None)
    new_feed_item.connect_object("activate", self.add_feed, None)
    new_category_item.connect_object("activate", self.add_category, None)
    delete_item.connect_object("activate", self.delete, None)
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
    abrir_browser_item = gtk.MenuItem("Abrir en un navegador")
    #abrir_browser_item = gtk.ImageMenuItem("Abrir en un navegador")
    #icon = abrir_browser_item.render_icon(gtk.STOCK_DND, gtk.ICON_SIZE_BUTTON)
    #abrir_browser_item.set_image(gtk.image_new_from_pixbuf(icon))
    toggle_leido_item = gtk.ImageMenuItem("Alternar leído/no leído")
    icon = toggle_leido_item.render_icon(gtk.STOCK_INDEX, gtk.ICON_SIZE_BUTTON)
    toggle_leido_item.set_image(gtk.image_new_from_pixbuf(icon))
    toggle_todos_leido_item = gtk.ImageMenuItem("Alternar leído/no leído (todos)")
    icon = toggle_todos_leido_item.render_icon(gtk.STOCK_SELECT_ALL, gtk.ICON_SIZE_BUTTON)
    toggle_todos_leido_item.set_image(gtk.image_new_from_pixbuf(icon))
    # Add them to the menu
    tree_menu.append(abrir_browser_item)
    tree_menu.append(toggle_leido_item)
    tree_menu.append(toggle_todos_leido_item)
    # Attach the callback functions to the activate signal
    abrir_browser_item.connect("activate", self.abrir_browser, None)
    toggle_leido_item.connect("activate", self.toggle_leido, 'single')
    toggle_todos_leido_item.connect("activate", self.toggle_leido, 'all')
    tree_menu.show_all()
    tree_menu.popup(None, None, None, event.button, event.get_time())
   return True

 def image_zoom_button_press_event(self, eventbox, event):
  """Toggles fullscreen mode for the browser."""
  if event.button == 1:
   if self.fullscreen:
    self.scrolled_window1.set_size_request(175,50)
    self.scrolled_window1.show()
    self.scrolled_window2.set_size_request(300,100)
    self.scrolled_window2.show()
    self.fullscreen = False
   else:
    self.scrolled_window1.set_size_request(0,0)
    self.scrolled_window1.hide()
    self.scrolled_window2.set_size_request(0,0)
    self.scrolled_window2.hide()
    self.fullscreen = True

 def headerlink_button_press_event(self, eventbox, event):
  """Launches a browser opening the selected feed entry."""
  if event.button == 1:
   print 'EventBox/Label clicked!'
   self.abrir_browser(self)
#  elif event.button == 2:
#   self.scrolled_window1.set_size_request(0,0)
#   self.scrolled_window1.hide()
#   self.scrolled_window2.set_size_request(0,0)
#   self.scrolled_window2.hide()
#  elif event.button == 3:
#   self.scrolled_window1.set_size_request(175,50)
#   self.scrolled_window1.show()
#   self.scrolled_window2.set_size_request(300,100)
#   self.scrolled_window2.show()

 def update_feed(self, data=None):
  """Updates a single (selected) feed or the ones from a (selected) category, if any."""
  (model, iter) = self.treeselection.get_selected()
  if(iter is not None): # Si hay algún nodo seleccionado...
   if(model.iter_depth(iter) == 0): # Si es un nodo padre...
    # Update all feeds of this category
    feed_ids = ''
    iter = model.iter_children(iter)
    while iter:
     id_feed = self.treestore.get_value(iter, 2)
     feed_ids += str(id_feed)+','
     iter = self.treestore.iter_next(iter)
    feed_ids = feed_ids[0:-1]
    print 'feed_ids: ' + feed_ids
    # Old way: self.get_feed(feed_ids)
    # New way:
    t = threading.Thread(target=self.get_feed, args=(feed_ids, ))
    t.start()
   elif(model.iter_depth(iter) == 1): # Si es un nodo hijo...
    # Update this single feed
    id_feed = self.treestore.get_value(iter, 2)
    # Old way: self.get_feed(id_feed)
    # New way:
    t = threading.Thread(target=self.get_feed, args=(id_feed, ))
    t.start()

 def update_all_feeds(self, data=None):
  """Updates all feeds (no complications!)."""
  # Old way: self.get_feed()
  # New way:
  t = threading.Thread(target=self.get_feed, args=())
  t.start()

 def check_feed_item(self, dentry):
  """Sets a default value for feed items if there's not any."""
  if(hasattr(dentry,'date_parsed')):
   dp = dentry.date_parsed
   secs = time.mktime(datetime.datetime(dp[0], dp[1], dp[2], dp[3], dp[4], dp[5], dp[6]).timetuple())
  else: secs = None
  if(hasattr(dentry,'title')): title = dentry.title.encode('utf-8')
  else: title = 'Sin título'
  if(hasattr(dentry,'description')): description = dentry.description.encode('utf-8')
  else: title = 'Sin descripción'
  if(hasattr(dentry,'link')): link = dentry.link.encode('utf-8')
  else: link = 'Sin enlace'

  return (secs, title, description, link)

 def get_feed(self, data=None):
  """Obtains & stores the feeds (thanks feedparser!)"""
  gtk.gdk.threads_enter() # NEW
  new_posts = False
  if(data is None): q = 'SELECT id,url,nombre FROM feed'
  else: q = 'SELECT id,url,nombre FROM feed WHERE id IN (' + str(data) + ')'
  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()
  cursor.execute(q)
  results = cursor.fetchall()
  for row in results:
   # Obtain feed 
   print 'Obteniendo feed ' + row[2] + ' (id #' + str(row[0]) + ', ' + row[1] + ') ...'
   d = feedparser.parse(row[1])
   count = len(d.entries)
   # Check for article existence...
   for i in range(0, count):
    (secs, title, description, link) = self.check_feed_item(d.entries[i])
    print 'Comprobando existencia del artículo...'
    if(secs is not None):
     cursor.execute('SELECT id FROM articulo WHERE fecha = ? AND id_feed = ?', [secs,row[0]])
     print 'SELECT id FROM articulo WHERE fecha = %s AND id_feed = %s' % (secs,row[0])
    else: # Slower but surely working...
     cursor.execute('SELECT id FROM articulo WHERE enlace = ? AND id_feed = ?', [link,row[0]])
     print 'SELECT id FROM articulo WHERE enlace = %s AND id_feed = %s' % (link,row[0])
    # Non-existant entry? Insert!
    if(cursor.fetchone() is None):
     # Check first is the feed is full
     print 'Comprobando capacidad del feed ' + row[2] + '...'
     cursor.execute('SELECT count(id) FROM articulo WHERE id_feed = ? AND importante = 0', [row[0]])
     print 'SELECT count(id) FROM articulo WHERE id_feed = %s AND importante = 0' % (row[0])
     row2 = cursor.fetchone()
     if((row2 is not None) and (row2[0]>=self.num_entries)):
      # If so, do some purging first...
      print 'Purgando una entrada para hacer espacio...'
      cursor.execute('DELETE FROM articulo WHERE fecha = (SELECT MIN(fecha) FROM articulo WHERE importante = 0 AND id_feed = ?) AND id_feed = ?', [row[0],row[0]])
      conn.commit()
     print 'No encontrado, salvando en BD...'
     if(secs is None):
      split = str(datetime.datetime.now()).split(' ')
      ds = split[0].split('-')
      ts = split[1].split(':')
      t = datetime.datetime(int(ds[0]), int(ds[1]), int(ds[2]), int(ts[0]), int(ts[1]), int(float(ts[2])))
      secs = time.mktime(t.timetuple())
     cursor.execute('INSERT INTO articulo VALUES(null, ?, ?, ?, ?, 0, 0, ?)', [title,description,secs,link,row[0]])
     conn.commit()
     new_posts = True
    else:
     print 'Encontrado, skipping...'
    cursor.close()

   if(count == 0):
    print 'No se pudo recuperar nada: URI incorrecta o site offline.'
   else:
    ## NEW ##
    (model, iter) = self.treeselection.get_selected()
    if(iter is not None): # Si hay algún nodo seleccionado...
     if(model.iter_depth(iter) == 1): # ... y es un nodo hijo
      id_feed = self.treestore.get_value(iter, 2)
      if id_feed == row[0]:
       print 'Actualizamos liststore...'
       self.populate_entries(id_feed)
    ## END ##

  # Fires tray icon blinking
  if((new_posts == True) and (window_visible == False)):
   self.statusicon.set_blinking(True)
  gtk.gdk.threads_leave() # NEW

 def import_feeds(self, data=None):
  """Imports feeds from an OPML file. It does not import categories
  or feeds with an existent name in the DB, and the later ones keep
  their settings (in case of feeds, they maintain url and category)."""
  dialog = gtk.FileChooserDialog("Abrir..",
                                self.window,
                                gtk.FILE_CHOOSER_ACTION_OPEN,
                                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
  dialog.set_default_response(gtk.RESPONSE_OK)

  filter = gtk.FileFilter()
  filter.set_name("opml/xml")
  filter.add_pattern("*.opml")
  dialog.add_filter(filter)

  filter = gtk.FileFilter()
  filter.set_name("All files")
  filter.add_pattern("*")
  dialog.add_filter(filter)

  response = dialog.run()
  if response == gtk.RESPONSE_OK:
   #print dialog.get_filename(), 'selected'
   f = open(dialog.get_filename(), 'r')
   tree = ElementTree.parse(f)
   current_category = 0
   conn = sqlite3.connect(db_path)
   cursor = conn.cursor()
   for node in tree.getiterator('outline'):
    name = node.attrib.get('text')
    url = node.attrib.get('xmlUrl')
    tipo = node.attrib.get('type')
    if name and url:
     #print ' - %s ( %s )' % (name, url)
     cursor.execute('SELECT id FROM feed WHERE nombre = ?', [name])
     if(cursor.fetchone() is None):
      # Create feed in the DB
      cursor.execute('INSERT INTO feed VALUES(null, ?, ?, ?)', [name,url,current_category])
      conn.commit()
    elif tipo == 'folder' and len(node) is not 0:
     if node[0].attrib.get('type') != 'folder':
      #print 'CATEGORIA: ' + name
      cursor.execute('SELECT id FROM categoria WHERE nombre = ?', [name])
      row = cursor.fetchone()
      if(row is None):
       # Create category in the DB (if it does not exist)
       cursor.execute('INSERT INTO categoria VALUES(null, ?)', [name])
       conn.commit()
       row = cursor.execute('SELECT MAX(id) FROM categoria')
       row = cursor.fetchone()
      current_category = row[0]
   cursor.close()
   f.close()
   self.liststore.clear()
   self.treestore.clear()
   self.populate_feeds()

  dialog.destroy()

 def export_feeds(self, data=None):
  """Exports feeds to an OPML file."""
  dialog = gtk.FileChooserDialog("Abrir..",
                                self.window,
                                gtk.FILE_CHOOSER_ACTION_SAVE,
                                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
  dialog.set_default_response(gtk.RESPONSE_OK)

  filter = gtk.FileFilter()
  filter.set_name("opml/xml")
  filter.add_pattern("*.opml")
  dialog.add_filter(filter)
  
  response = dialog.run()
  if response == gtk.RESPONSE_OK:
   f = open(dialog.get_filename()+'.opml', 'w')
   out = '<?xml version="1.0"?>\n<opml version="1.0">\n<head>\n<title>Liferea Feed List Export</title>\n</head>\n<body>\n'
   conn = sqlite3.connect(db_path)
   cursor = conn.cursor()
   cursor.execute('SELECT id,nombre FROM categoria')
   categorias = cursor.fetchall()
   for row in categorias:
    out += '<outline title="'+row[1]+'" text="'+row[1]+'" description="'+row[1]+'" type="folder">\n'
    cursor.execute('SELECT nombre,url FROM feed WHERE id_categoria = ?', [row[0]])
    feeds = cursor.fetchall()
    cursor.close()
    for row2 in feeds:
     out += '<outline title="'+row2[0]+'" text="'+row2[0]+'" description="'+row2[0]+'" type="rss" xmlUrl="'+row2[1]+'" htmlUrl="http://badopi.net"/>\n'
   out += '</body>\n</opml>'
   f.write(out)
   f.close()

  dialog.destroy()

 # INIT #
 ########

 def __init__(self):
  # Inicializamos el threading...
  # Crea la base para la aplicación (directorio + feed de regalo!), si no la hubiere
  self.create_base()
  # Obtiene la config de la app
  self.get_config()
  # Limpieza de entries sobrantes...
  ###self.purge_entries()
  # Creamos la ventana principal
  self.create_main_window()

def main():
 # Inicializamos los threads!
 gobject.threads_init()
 # Params: interval in miliseconds, callback, callback_data
 # Start timer (1h = 60min = 3600secs = 3600*1000ms)
 timer = gobject.timeout_add(hello.update_freq*3600*1000, hello.update_all_feeds)
 # Stop timer
 #gobject.source_remove(timer)
 gtk.main()
 
if __name__ == "__main__":
 hello = Naufrago()
 main()

