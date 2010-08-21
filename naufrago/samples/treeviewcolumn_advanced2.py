#!/usr/bin/env python

# example treeviewcolumn.py

import pygtk
pygtk.require('2.0')
import gtk, gobject

class TreeViewColumnExample:

    # close the window and quit
    def delete_event(self, widget, event, data=None):
        gtk.main_quit()
        return False

    def toggler(self, cell, path, model):
        """
        Sets the toggled state on the toggle button to true or false.
        """
        model[path][1] = not model[path][1]
        print "Toggle '%s' to: %s" % (model[path][0], model[path][1],)
        return

    def __init__(self):
        # Create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("TreeViewColumn Example")
        self.window.connect("delete_event", self.delete_event)

        # create a liststore with one string column to use as the model
        #self.liststore = gtk.ListStore(str, gobject.TYPE_BOOLEAN, str)
	self.liststore = gtk.ListStore(str, bool, str)

        # create the TreeView using liststore
        self.treeview = gtk.TreeView(self.liststore)
	self.treeview.set_rules_hint(True) # differentiate rows...
        self.treeselection = self.treeview.get_selection()

        # create the TreeViewColumns to display the data
        self.tvcolumn = gtk.TreeViewColumn('')
        self.tvcolumn1 = gtk.TreeViewColumn('Text1')
        self.tvcolumn2 = gtk.TreeViewColumn('Text2')

        # add a row with text and a stock item - color strings for the background
        #self.liststore.append(['A', gobject.TYPE_BOOLEAN, 'Lala lala lala laaa 1'])
	self.liststore.append(['A', False, 'Lala lala lala laaa 1'])
        self.liststore.append(['B', False, 'Lala la laaaaaaaaaa 2'])
        self.liststore.append(['C', False, 'Lala la lalala la lala la la la 3'])

        # add columns to treeview
        self.treeview.append_column(self.tvcolumn)
        self.treeview.append_column(self.tvcolumn1)
        self.treeview.append_column(self.tvcolumn2)

        # create a CellRenderers to render the data
        self.cellt = gtk.CellRendererToggle()
	self.cellt.set_property('activatable', True)
	self.cellt.connect('toggled', self.toggler, self.liststore) # toggle signal capture
        self.celldate = gtk.CellRendererText()
        self.celltitle = gtk.CellRendererText()

        # add the cells to the columns - 2 in the first
        self.tvcolumn.pack_start(self.cellt, False)
        self.tvcolumn1.pack_start(self.celldate, True)
        self.tvcolumn2.pack_start(self.celltitle, True)

	self.tvcolumn.add_attribute(self.cellt, "active", 1)
        self.tvcolumn1.set_attributes(self.celldate, text=0)
        self.tvcolumn2.set_attributes(self.celltitle, text=2)
        #self.tvcolumn2.set_attributes(self.cell1, text=2, cell_background_set=3)

        # make treeview searchable
        self.treeview.set_search_column(0)
        # Allow sorting on the column
        self.tvcolumn1.set_sort_column_id(0)
        self.window.add(self.treeview)
        self.window.show_all()

def main():
    gtk.main()

if __name__ == "__main__":
    tvcexample = TreeViewColumnExample()
    main()
