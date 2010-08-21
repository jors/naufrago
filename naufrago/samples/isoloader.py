#!/usr/bin/env python

###############################################################################
## ISOLoader
##
## Copyright (C) 2009-2009 Jorge Antonio Rey de Pinyo operador(at)gmai.com
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
###############################################################################

# Modulos requeridos para el programa
#
import ConfigParser, os, os.path, sys, string
import gtk
import pygtk
pygtk.require('2.0')

# Autoria del codigo
#
__auth_code__ = 'Worked <operador@gmail.com>'
__copyright__ = '2009 Jorge Antonio Rey de Pinyo <Worked>'
__comment__ = 'A simple ISO image loader using the power of mount and /dev/loop0... Who wants Daemon Tools when linux can do it better?'
__license__ = 'GPL' 
__version__ = '1.00'
__website__ = 'http://bandaancha.eu/store/worked/isoloader.py'

# StatusIcon
#	Creacion del programa en el area de notificacion
#
#	Sabado 06.06.2009 17:23
#
class StatusIcon(gtk.StatusIcon):
	# Esto hara que se muestre el menu de opciones
	def on_popup_menu(self, status, button, time):
		self.menu.popup(None, None, None, button, time)    
	# Llamamos a la clase para seleccionar archivos
	def on_open(self, data):
		fileSelect(self)
	# Llamamos a la clase para ver las imagenes montadas
	def on_list(self, data):
		fileMounts(self)
	# Dialog donde mostramos los creditos
	def on_about(self, data):
		dialog = gtk.AboutDialog()
		dialog.set_name('ISO Loader')
		dialog.set_version(__version__)
		dialog.set_comments(__comment__)
		dialog.set_website(__website__)
		dialog.set_copyright(__copyright__)
		dialog.run()
		dialog.destroy()
	# Destruccion del programa
	def on_exit(self, data):
		gtk.main_quit()
	# Iniciamos la clase
	def __init__(self):
		gtk.StatusIcon.__init__(self)
		menu = '''
			<ui>
				<menubar name="Menubar">
					<menu action="Menu">
						<menuitem action="Open"/>
						<menuitem action="List"/>
						<separator/>
						<menuitem action="About"/>
						<menuitem action="Quit"/>
					</menu>
				</menubar>
			</ui>
		'''
		actions = [
			('Menu',  None, 'Menu'),
			('Open', None, '_Open...', None, 'Search and open iso files', self.on_open),
			('List', None, '_List...', None, 'See all mounted images', self.on_list),
			('About', gtk.STOCK_ABOUT, '_About...', None, 'About ISO Loader', self.on_about),
			('Quit', gtk.STOCK_CANCEL, '_Quit...', None, 'Exit program', self.on_exit)]

		# Creamos las opciones por defecto del menu
		app = gtk.ActionGroup('Actions')
		app.add_actions(actions)
		# Opciones para el menu
		self.manager = gtk.UIManager()
		self.manager.insert_action_group(app, 0)
		self.manager.add_ui_from_string(menu)
		# Opciones por defecto que tendra el menu
		self.menu = self.manager.get_widget('/Menubar/Menu/About').props.parent
		search = self.manager.get_widget('/Menubar/Menu/Open')
		search.get_children()[0].set_markup('<b>_Open...</b>')
		search.get_children()[0].set_use_underline(True)
		search.get_children()[0].set_use_markup(True)
		# Icono que aparecera en el systray y el alt
		self.set_from_stock(gtk.STOCK_CDROM)
		self.set_tooltip('ISO Loader')
		self.set_visible(True)
		# Si se presiona el icono, llama por defecto al cargador de ISOs
		self.connect('activate', self.on_open)
		# Si se presiona el boton derecho muestra el menus
		self.connect('popup-menu', self.on_popup_menu)
		
# Message
#	Dialogo de error cuando alguna de las cosas que pensabamos no sale como esperabamos
#	(util para decir que sabemos que el programa falla... pero no el motivo xD)
#
#	Viernes 12.06.2009 14:44
class Message(gtk.Dialog):
	def __init__(self, title, message):
		self.dialog = gtk.Dialog()
		self.dialog.set_title(title)
		self.dialog.set_size_request(400, 200)
		self.dialog.set_resizable(False)
		self.dialog.connect("destroy", lambda w: self.dialog.destroy())
		hbox = gtk.HBox()
		self.dialog.vbox.pack_start(hbox, True, True, 10)
		label = gtk.Label(message)
		hbox.pack_start(label, True, False, 5)
		label.set_width_chars(35)
		label.set_line_wrap(True)
		self.dialog.show_all()

# fileVault
#	Cargamos en un objeto tanto el archivo como las isos previamente ejecutadas desde
#	nuestra aplicacion
#
#	Lunes 15.06.2009 10:35
#
class fileVault:
	# Agregamos un elemento a la lista
	def add(self, data):
		name = data.rsplit('/')
		self.file.set('LIST', name[len(name) - 1], data)
		self.write()
	# Salvamos todas las imagenes que han quedado despues de la criba del usuario
	def save(self, name, path):
                self.file.remove_section('LIST')
                self.file.add_section('LIST')
                i = 0
                while i < len(name):
                	self.file.set('LIST', name[i], path[i])
                        i = i + 1
		self.write()
	# Escribimos la configuracion en el archivo
	def write(self):
		self.file.write(open(self.path, 'w'))
	# Listado del contenido del archivo
	def list(self):
		items = self.file.items('LIST')
		return items
	# Iniciamos el archivo con las imagenes almacenadas
	def __init__(self, mode = None, item = None):
		if os.environ['HOME'] and os.path.isdir(os.environ['HOME']):
			self.path = os.environ['HOME'] + os.sep + '.isoloader'
		else:
			self.path = os.environ['HOME'] + os.sep + '.isoloader'
		self.file = ConfigParser.ConfigParser()
		self.file.readfp(open(self.path, 'r'))
		#self.file.add_section('LIST')

# fileSelect
#	Selector de la imagen ISO que daremos orden de montar
#
#	Sabado 06.06.2009 17:36
#
class fileSelect:
	# Cuando se seleccione un archivo damos la instruccion de montaje
	def on_select(self, data):
		# Cortamos para comprobar la extension del archivo
		temp = self.fileChooser.get_filename().split('/')
		temp = temp[len(temp) - 1].split('.')
		if temp[1] == "iso":
			os.system('mount -t iso9660 -o ro,loop=/dev/loop0 %s /media/cdrom' % self.fileChooser.get_filename())
			# Grabamos la nueva imagen dentro de nuestra lista
			fileVault().add(self.fileChooser.get_filename())
	                # Cambiamos el icono del programa y destruimos la ventana                                                                                                                                                                               		
			self.icon.set_from_stock(gtk.STOCK_EXECUTE)
		else:
			msg = Message('Archivo incompatible', 'El archivo que intenta montar no es una imagen ISO compatible con este programa.\n\nSi cree que puede tratarse de un error, por favor comuniqueselo por correo electronico al desarrollador de este software.')
		self.fileChooser.destroy()
	# Iniciamos la instruccion para seleccionar archivo
	def __init__(self, StatusIcon):
		# Recuperamos las propiedades de la aplicacion principal
		self.icon = StatusIcon
		# Dibujamos el selector de archivos
		self.fileChooser = gtk.FileSelection("Select ISO image to mount")
		self.fileChooser.ok_button.connect("clicked", self.on_select)
		self.fileChooser.cancel_button.connect("clicked", lambda w: self.fileChooser.destroy())
		self.fileChooser.set_filename("*.iso")
		self.fileChooser.show()

# fileMounts
#	Listado de las imagenes montadas y la opcion de remontarlas
#
#	Domingo 07.06.2009 21:27
#
class fileMounts:
	# Cuando pulsamos a eliminar | (self.iterador, 0) => id de la imagen en nuestra lista
	def on_remove(self, data):
		seleccion, self.iterador = self.treeview.get_selection().get_selected()
		id =  seleccion.get_value(self.iterador, 0)
		self.liststore.remove(self.iterador)
		self.iterador = ""
	# Cuando pulsamos en remontar | (self.iterador, 1) => path de la imagen en nuestra lista
	def on_mount(self, data):
		seleccion, self.iterador = self.treeview.get_selection().get_selected()
		path =  seleccion.get_value(self.iterador, 1)
		os.system('mount -t iso9660 -o ro,loop=/dev/loop0 %s /media/cdrom' % path)
		self.icon.set_from_stock(gtk.STOCK_EXECUTE)
		self.window.destroy()
	# Cuando cerramos la ventana dandole a la X guardamos lo que esta en la lista y lo incrustamos en la db
	def on_close(self, data):
		name = [ r[0] for r in self.liststore ]
		path = [ r[1] for r in self.liststore ]
		fileVault().save(name, path)
	# Iniciamos fileMounts	
	def __init__(self, StatusIcon):
		# Recuperamos las propiedades de la aplicacion principal
		self.icon = StatusIcon
		# Creamos la ventana donde dibujaremos todo
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_size_request(600, 200)
		self.window.set_title("ISO Loader | Mounted images")
		self.window.connect("destroy", self.on_close)
		# Adjuntamos dos ventanas (vertical y horizontal) donde incrustar los datos de las imagenes (vertical)
		# y los botones para interactuar (horizontal)
		self.scrolledwindow = gtk.ScrolledWindow()
		self.scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		self.vbox = gtk.VBox()
		self.hbox = gtk.HButtonBox()
		self.hbox.set_layout(gtk.BUTTONBOX_END)
		self.hbox.set_spacing(10)
		self.hbox.set_border_width(10)
		self.vbox.pack_start(self.scrolledwindow, True)
		self.vbox.pack_start(self.hbox, False)
		self.button_remove = gtk.Button('Remove', gtk.STOCK_REMOVE)
		self.button_mount = gtk.Button('Re-mount', gtk.STOCK_OPEN) 
		self.button_remove.connect("clicked", self.on_remove)
		self.button_mount.connect("clicked", self.on_mount)
		self.hbox.pack_start(self.button_remove)
		self.hbox.pack_start(self.button_mount) 
		# Creamos una lista con los valores que almacenara en dos columnas (name, path)
		self.liststore = gtk.ListStore(str, str, 'gboolean')
		self.treeview = gtk.TreeView(self.liststore)
		self.name = gtk.TreeViewColumn('Image')
		self.path = gtk.TreeViewColumn('Path') 
		# Funcion que leera e incluira en liststore la lista de imagenes
		items = fileVault().list()
		i = 0
		while i < len(items):
			self.liststore.append([items[i][0], items[i][1], True])
			i = i + 1
		# Agregamos las columnas a las celdas y asignamos algunas propiedades basicas a estas
		self.treeview.append_column(self.name)   
		self.treeview.append_column(self.path)   
		self.cell0 = gtk.CellRendererText()      
		self.cell1 = gtk.CellRendererText()      
		self.name.pack_start(self.cell0, True)   
		self.path.pack_start(self.cell1, True)   
		self.name.set_attributes(self.cell0, text=0)
		self.path.set_attributes(self.cell1, text=1)
		self.name.set_sort_column_id(0)
		self.scrolledwindow.add(self.treeview)
		self.window.add(self.vbox)
		self.window.show_all()

# Inicio del programa
#
#	Sabado 06.06.2009 17:00
if __name__ == '__main__':
	StatusIcon()
	gtk.main()
