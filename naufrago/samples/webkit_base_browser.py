#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
""" 
    SimpleBrowser - Navegador muy muy simple de internet, sólo de ejemplo,
                    que utiliza la biblioteca Webkit GTK desde Python (PyWebkitGTK).
 
    Marcelo Fidel Fernández - http://www.marcelofernandez.info 
    Licencia: BSD. Disponible en: http://www.freebsd.org/copyright/license.html
"""
 
import sys
import gtk
import webkit
 
DEFAULT_URL = 'http://www.python.org'
 
class SimpleBrowser:
 
    def __init__(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.window.connect('delete_event', self.close_application)
        self.window.set_default_size(800, 600)
 
        vbox = gtk.VBox(spacing=5)
        vbox.set_border_width(5)
 
        self.txt_url = gtk.Entry()
        self.txt_url.connect('activate', self._txt_url_activate)
 
        self.scrolled_window = gtk.ScrolledWindow()
        self.webview = webkit.WebView()
        self.scrolled_window.add(self.webview)
 
        vbox.pack_start(self.txt_url, fill=False, expand=False)
        vbox.pack_start(self.scrolled_window, fill=True, expand=True)
        self.window.add(vbox)
 
    def _txt_url_activate(self, entry):
        self._load(entry.get_text())
 
    def _load(self, url):
        self.webview.open(url)
 
    def open(self, url):
        self.txt_url.set_text(url)
        self.window.set_title('SimpleBrowser - %s' % url)
        self._load(url)
 
    def show(self):
        self.window.show_all()
 
    def close_application(self, widget, event, data=None):
        gtk.main_quit()
 
if __name__ == '__main__':
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = DEFAULT_URL
 
    # PyWebkitGTK necesita habilitar el soporte de los hilos en PyGTK
    #gtk.gdk.threads_init()
    browser = SimpleBrowser()
    browser.open(url)
    browser.show()
    gtk.main()
