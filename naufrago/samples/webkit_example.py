#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygtk
pygtk.require("2.0")
import gtk
import webkit

class Browser():

    global url, ABOUT_PAGE
    url = 'http://www.google.es/'
    url = ''
    ABOUT_PAGE = """
                <html><head><title>PyWebKitGtk - About</title></head><body>
                <h1>Welcome to <code>webbrowser.py</code></h1>
                <p><a href="http://code.google.com/p/pywebkitgtk/">http://code.google.com/p/pywebkitgtk/</a><br/>
                </p>
                </body></html>
                """

    # Ventana del programa
    def __init__(self):

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.set_default_size(640, 480)
        self.window.connect("destroy", self.on_quit)

        # La parte en donde se muestra la pagina que se visita (con scroll incluido)
        self.scroll_window = gtk.ScrolledWindow()
        self.webview = webkit.WebView()
        self.scroll_window.add(self.webview)
        self.window.add(self.scroll_window)

        if(url != ''):
            # abrimos la pagina de inicio (opcional)
            self.webview.open(url)
        else:
            self.webview.load_string(ABOUT_PAGE, "text/html", "iso-8859-15", "about")

        self.window.show_all()
        self.dump(self.webview)

    def dump(self, obj):
        """Internal use only"""
        for attr in dir(obj):
           print "obj.%s = %s" % (attr, getattr(obj, attr))

    def on_quit(self, widget):
        gtk.main_quit()

    def main(self):
        gtk.main()

if __name__ == "__main__":
    browser = Browser()
    browser.main()
