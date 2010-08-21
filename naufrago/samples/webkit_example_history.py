#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygtk
pygtk.require("2.0")
import gtk
import webkit
#from webkit import WebHistoryItem, WebBackForwardList, WebView
import urllib

class Browser():

    global url, ABOUT_PAGE
    url = 'http://www.google.es/'
    url = ''
    ABOUT_PAGE = """
                <html><head><title>PyWebKitGtk - About</title></head><body>
                <h1>Welcome to <code>webbrowser.py</code></h1>
                <p><a href="http://code.google.com/p/pywebkitgtk/">http://code.google.com/p/pywebkitgtk/</a><br/></p>
                </body></html>
                """

    def navigation_requested(self, frame, request, navigation_action, policy_decision, data=None):
 	 #print "Navigation requested signal received!"
         #print 'Request: ' + str(navigation_action)
         #print policy_decision.get_reason() # navigation_action
	#uri = networkRequest.get_uri()
        uri = navigation_action.get_uri()
        print "request to go to %s" % uri
  
        # load the page somehow.....
        page = urllib.urlopen(uri)
        # load into associated view, passing in uri
        self.webview.load_string(page.read(), "text/html", "iso-8859-15", uri)
        # return 1 to stop any other handlers running
        # eg. the default uri handler...
        return 1

    def resource_request_starting(self, frame, resource, request, response, data=None):
	print frame
        print resource
        print request
        print response
        print data
        #response.set_uri("http://enchufado.com/")
        response.set_uri("about:blank")

    # Ventana del programa
    def __init__(self):

        global current_uri, current_title

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.set_default_size(640, 480)
        self.window.connect("destroy", self.on_quit)

        # La parte en donde se muestra la pagina que se visita (con scroll incluido)
        self.scroll_window = gtk.ScrolledWindow()
        self.webview = webkit.WebView()
        self.webview.connect("navigation-policy-decision-requested", self.navigation_requested)
#        self.webview.connect("resource-request-starting", self.resource_request_starting)

#        self.webframe = self.webview.get_main_frame()
#        current_uri = self.webframe.get_uri()
#        current_title = self.webframe.get_title()

        self.scroll_window.add(self.webview)
        self.window.add(self.scroll_window)

        if(url != ''):
            # abrimos la pagina de inicio (opcional)
            self.webview.open(url)
        else:
            self.webview.load_string(ABOUT_PAGE, "text/html", "iso-8859-15", "about")

        self.window.show_all()
        ###self.dump(self.webview)

#    def dump(self, obj):
#        """Internal use only: it dumps all object data."""
#        for attr in dir(obj):
#           print "obj.%s = %s" % (attr, getattr(obj, attr))

    def on_quit(self, widget):
        gtk.main_quit()

    def main(self):
        gtk.main()

if __name__ == "__main__":
    browser = Browser()
    browser.main()
