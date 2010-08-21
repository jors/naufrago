#!/usr/bin/env python

# example treeviewcolumn.py

import pygtk
pygtk.require('2.0')
import gtk

class TreeViewColumnExample:

    # close the window and quit
    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

    def make_pb(self, tvcolumn, cell, model, iter):
        stock = model.get_value(iter, 1)
        pb = self.treeview.render_icon(stock, gtk.ICON_SIZE_MENU, None)
        cell.set_property('pixbuf', pb)
        return

    def button_press_event(self, treeview, event):
	if event.button == 1:
            # Esto cambia los atributos de la celda (caso de que la encontremos)
            #model.set(iter, 1, 'string', 2, 'string two')
   	    x = int(event.x)
   	    y = int(event.y)
   	    time = event.time
   	    pthinfo = treeview.get_path_at_pos(x, y)
   	    if pthinfo is not None:
                # Nos interesa col (como sabemos si es la 1a columna???)
    	        path, col, cellx, celly = pthinfo
    		###treeview.grab_focus()
    		###treeview.set_cursor(path, col, 0)
                ###print col
                #self.treeselection = self.treeview.get_selection()
                (model, iter) = self.treeselection.get_selected()
                model.set(iter, 1, gtk.STOCK_MEDIA_RECORD)
                #print self.tvcolumn.get_cell_renderers()

    def __init__(self):
        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("TreeViewColumn Example")
        self.window.connect("delete_event", self.delete_event)

        # create a liststore with one string column to use as the model
        self.liststore = gtk.ListStore(str, str, str)

        # create the TreeView using liststore
        self.treeview = gtk.TreeView(self.liststore)
	self.treeview.connect("button_press_event", self.button_press_event) # Toggle "important" icon
        self.treeselection = self.treeview.get_selection()

        # create the TreeViewColumns to display the data
        self.tvcolumn = gtk.TreeViewColumn('Pixbuf')
        self.tvcolumn1 = gtk.TreeViewColumn('Text1')
        self.tvcolumn2 = gtk.TreeViewColumn('Text2')

        # add a row with text and a stock item - color strings for the background
        self.liststore.append(['A', None, 'Lala lala lala laaa 1'])
        self.liststore.append(['B', gtk.STOCK_MEDIA_RECORD, 'Lala la laaaaaaaaaa 2'])
        self.liststore.append(['C', gtk.STOCK_MEDIA_RECORD, 'Lala la lalala la lala la la la 3'])

        # add columns to treeview
        self.treeview.append_column(self.tvcolumn)
        self.treeview.append_column(self.tvcolumn1)
        self.treeview.append_column(self.tvcolumn2)

        # create a CellRenderers to render the data
        self.cellpb = gtk.CellRendererPixbuf()
        self.cell = gtk.CellRendererText()
        self.cell1 = gtk.CellRendererText()

        # add the cells to the columns - 2 in the first
        self.tvcolumn.pack_start(self.cellpb, False)
        self.tvcolumn1.pack_start(self.cell, True)
        self.tvcolumn2.pack_start(self.cell1, True)

        # set the cell attributes to the appropriate liststore column
        # GTK+ 2.0 doesn't support the "stock_id" property
        if gtk.gtk_version[1] < 2:
            self.tvcolumn.set_cell_data_func(self.cellpb, self.make_pb)
        else:
            self.tvcolumn.set_attributes(self.cellpb, stock_id=1)
        self.tvcolumn1.set_attributes(self.cell, text=0)
        self.tvcolumn2.set_attributes(self.cell1, text=2)
        #self.tvcolumn2.set_attributes(self.cell1, text=2, cell_background_set=3)

        # make treeview searchable
        self.treeview.set_search_column(0)
        # Allow sorting on the column
        self.tvcolumn.set_sort_column_id(0)
        self.tvcolumn1.set_sort_column_id(0)
        # Allow drag and drop reordering of rows
        ###self.treeview.set_reorderable(False)
        self.window.add(self.treeview)
        self.window.show_all()

def main():
    gtk.main()

if __name__ == "__main__":
    tvcexample = TreeViewColumnExample()
    main()
