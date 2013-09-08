#! /usr/bin/python
import gtk
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib

from pyxhook import HookManager

from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor, threads
from autobahn.websocket import WebSocketServerFactory, WebSocketServerProtocol, listenWS

'''
KeySocket Linux Server
@author geekingreen, Tonic Artos
'''

PORT = 1337

# 171 = Prev, 172 = Play/Pause, 173 = Next, 174 = Stop
keys = [171, 172, 173, 174]
# Convert media keys for client
media_key_map = { 'Previous':'20', 'Play':'16', 'Next':'19', 'Stop':'16' }

# Convert local keys to what the client is expecting
key_map = { '171': '19', '172': '16', '173': '20', '174': '16' }


class KeySocketServerProtocol(WebSocketServerProtocol):
    """
    The Protocol simply adds the client to a list of
    clients that will be broadcasted to when the Server
    receives the first message "Ping".
    """
    def onMessage(self, message, binary):
        if self not in self.factory.clients:
            self.factory.clients.append(self)

class KeySocketServerFactory(WebSocketServerFactory):
    """
    The Factory implements the broadcast method which
    sends the media key to the clients. 
    """
    protocol = KeySocketServerProtocol
    clients = []

    def broadcast(self, msg):
        for client in self.clients:
            client.sendMessage(msg)

class KeySocket:
    """
    The KeySocket class which creates GTK2 StatusIcon and
    starts the server.
    """
    def __init__(self):
	# set up the glib main loop.
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
	bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
	bus_object = bus.get_object('org.gnome.SettingsDaemon', '/org/gnome/SettingsDaemon/MediaKeys')

	# this is what gives us the multi media keys.
	dbus_interface='org.gnome.SettingsDaemon.MediaKeys'
	bus_object.GrabMediaPlayerKeys("MediaKeySocketServer", 0, dbus_interface=dbus_interface)

	# connect_to_signal registers our callback function.
	bus_object.connect_to_signal('MediaPlayerKeyPressed', self.on_mediakey)

        self.statusicon = gtk.StatusIcon()
        self.statusicon.set_from_file('icon48.png')
        self.statusicon.connect('popup-menu', self.right_click_event)
        self.statusicon.set_tooltip('KeySockets')      

        self.factory = KeySocketServerFactory('ws://localhost:{}'.format(PORT), debug=True)

        listenWS(self.factory)
        reactor.run()

    def main_quit(self, widget):
#        self.hm.cancel()
	gtk.main_quit()
        reactor.stop()

    def on_mediakey(self, comes_from, what):
	if what in ['Stop','Play','Next','Previous']:
		self.factory.broadcast(media_key_map[what])
    
    def right_click_event(self, icon, button, time):
        menu = gtk.Menu()

        quit = gtk.MenuItem('Quit')

        quit.connect('activate', self.main_quit)

        menu.append(quit)

        menu.show_all()

        menu.popup(None, None, gtk.status_icon_position_menu, button, time, self.statusicon)

ks = KeySocket()
gtk.main()
