#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygtk
pygtk.require('2.0')
import gtk

class Naufrago:

 # Callbacks
 def callback(self, widget, data):
  print "Hello again - %s was pressed" % data

 def delete_event(self, widget, event, data=None):
  gtk.main_quit()
  return False

 def main_menu(self, window):
  accel_group = gtk.AccelGroup()
  # Inicializamos la factoría de elementos.
  # Item 1 - El tipo de menú.
  # Item 2 - La ruta al menú.
  # Itme 3 - La factoría de elementos para los aceleradores.
  item_factory = gtk.ItemFactory(gtk.MenuBar, "<main>", accel_group)
  # Generamos los elementos del menú.
  item_factory.create_items(self.menu_items)
  # Añadir el nuevo grupo de aceleradores a la ventana.
  window.add_accel_group(accel_group)
  # Es necesario mantener una referencia a item_factory para evitar su destrucción
  self.item_factory = item_factory
  # Finalmente, se devuelve la barra de menú creada por la factoría de elementos.
  return item_factory.get_widget("<main>")

 # Inicializacion
 def __init__(self):
  self.menu_items = (
                    ( "/_Archivo",         None,         None, 0, "<Branch>" ),
     	            ( "/Archivo/Nuevo _dir",     "<control>D", self.callback, 0, None ),
                    ( "/Archivo/_Nuevo feed",     "<control>N", self.callback, 0, None ),
   	            ( "/Archivo/_Eliminar",    "<control>O", self.callback, 0, None ),
   	            ( "/Archivo/sep1",     None,         None, 0, "<Separator>" ),
   	            ( "/Archivo/Salir",     "<control>Q", gtk.main_quit, 0, None ),
   	            ( "/_Ayuda",         None,         None, 0, "<LastBranch>" ),
   	            ( "/_Ayuda/Acerca de",   None,         None, 0, None ),
   	            )

  # Creamos una ventana
  self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
  # Título de la ventana
  self.window.set_title("Naufrago!")
  # Establecemos el manejador para delete_event
  self.window.connect("delete_event", self.delete_event)
  self.window.set_border_width(5) # Grosor del borde de la ventana
  self.window.set_size_request(300, 200) # Dimensionamiento de la ventana

  # Creación de la tabla (3x2)
  self.table = gtk.Table(3, 2, False)
  self.window.add(self.table)

  # Creación del menubar
  self.menubar = self.main_menu(self.window)
  self.menubar.show()
  self.table.attach(self.menubar, 0, 2, 0, 1)

  self.button1 = gtk.Button("Button 1")
  self.button1.connect("clicked", self.callback, "button 1")
  self.table.attach(self.button1, 0, 1, 1, 3)
  self.button1.show()

  self.button2 = gtk.Button("Button 2")
  self.button3 = gtk.Button("Button 3")
  self.button2.connect("clicked", self.callback, "button 2")
  self.button3.connect("clicked", self.callback, "button 3")
  self.table.attach(self.button2, 1, 2, 1, 2)
  self.table.attach(self.button3, 1, 2, 2, 3)
  self.button2.show()
  self.button3.show()
  self.table.show()
  self.window.show()

def main():
 gtk.main()
 
if __name__ == "__main__":
 hello = Naufrago()
 main()

