import gtk
import os
import subprocess as sp
import time
import threading

gtk.gdk.threads_init()
#gobject.threads_init()

CMD = 'du -sh /home/jors/ut'

class MainWin:
    """
    Creates a main window object
    """
    def __init__(self):
     w = gtk.Window()
     self.pb = gtk.ProgressBar()
     box = gtk.HBox(False, 0)
     self.btn_start = gtk.Button("Start")
     self.btn_start.connect("clicked", self.btn_start_click)
     box.pack_start(self.btn_start)
     btn_test = gtk.Button("Test")
     btn_test.connect("clicked", self.btn_test_click)
     box.pack_end(btn_test)

     self.btn_stop = gtk.Button("Stop")
     self.btn_stop.connect("clicked", self.btn_stop_click)
     self.btn_stop.set_sensitive(False)
     box.pack_end(self.btn_stop)

     box.pack_start(self.pb)

     w.add(box)
     w.show_all()
     w.connect("destroy", self.quit)

    def get_popen(self, cmd):
        return sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT)
   
    def pulse(self):
     while not self.quit:
      time.sleep(0.1)
      gtk.gdk.threads_enter()
      self.pb.pulse()
      gtk.gdk.threads_leave()

    def exec_cmd(self):
     self.popen = self.get_popen(CMD.split())
     out = self.popen.stdout.read()
     if out:
      print out
     self.terminate()
       
    def terminate(self):
     self.quit = True
     os.kill(self.popen.pid, 9)
     self.btn_stop.set_sensitive(False)
     self.btn_start.set_sensitive(True)
     print "Terminate threads"

    def quit(self, widget):
     gtk.main_quit()
     self.terminate()

    def btn_test_click(self, widget):
     print "gtkMain thread"

    def btn_stop_click(self, widget):
     self.pb.set_text("Completed")
     self.terminate()

    def new_thread(self, method):
     t = threading.Thread(target=method, args=())
     t.start()

    def btn_start_click(self, widget):
     print "Start threads"
     self.quit = False
     self.btn_stop.set_sensitive(True)
     widget.set_sensitive(False)
     self.pb.set_text('Running')
     self.new_thread(self.pulse)
     self.new_thread(self.exec_cmd)
       
if __name__ == "__main__":
    gui = MainWin()
    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()
