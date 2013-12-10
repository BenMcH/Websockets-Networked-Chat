from __future__ import print_function
import tornado.httpserver
import tornado.websocket as ws
import tornado.ioloop
import tornado.wsgi
import tornado.web
import time
import re

class ChatServer(object):
    """
    A chat server that broadcasts messages to multiple clients.
    """
    def __init__(self):
        self.clients = {}
        self.next_id = 1
        self.pattern = re.compile("^user[\d]*", re.IGNORECASE)

    def name(self, client_id):
        if client_id == 0:
            return "Server"
        else:
            try:
                return self.clients[client_id].name 
            except:
                return "User{0}".format(client_id)

    def add_client(self, client):
        """
        Add a client. Return a client_id.
        """
        client_id = self.next_id
        self.next_id += 1
        self.clients[ client_id ] = client

        # this shouldn't throw an error in production but while
        # we're working on it, we want to make sure we assign the
        # client_id correctly no matter what.
        #
        # I was thinking it would make sense to use a numeric id
        # rather than the object directly so it would be usable
        # as a key in a dictionary. (Alternatively, we could write
        # a __hash__ function for the client class, and then look
        # it up directly.
        try:
            msg = ('client {0} has connected as {1}'
                   .format(client_id, self.name(client_id)))
            self.broadcast(0, msg, self.clients[client_id].room)
        except Exception as e:
            print('ERROR: ', e)
        return client_id

    def remove_client(self, client_id):
        if client_id in self.clients:
            name = self.name(client_id)
            del self.clients[client_id]

    def broadcast(self, sender_id, message, topic = "all"):
        if topic == "all":
            try:
                topic = self.clients[sender_id].room
            except:
                topic = "all"
        msg = "{0}: {1}".format(self.name(sender_id), message)
        for client in self.clients.values():
            if client.room == topic:
                client.write_message(msg)
        print(msg)

    def change_name(self, client_id, new_name):
        if self.pattern.match("".join(new_name.split())):
            self.clients[client_id].write_message("Server: This username is following an incorrect format for custom names.")
            return None
        for client in self.clients:
            if self.name(client) == new_name:
                self.clients[client_id].write_message("Server: This name is already taken")
                return None
        self.broadcast(0, "{0} has been renamed to {1}.".format(self.name(client_id),new_name), self.clients[client_id].room)
        self.clients[client_id].name=new_name

    
      
server = ChatServer()

class WSEchoHandler(ws.WebSocketHandler):
    
    def open(self):
        self.room = "CrystalChat"
        self.client_id = server.add_client(self)
        self.name="User{0}".format(self.client_id)
        self.time = int(round(time.time()*1000))
        self.spam_msg = int(round(time.time()*1000))
    def on_message(self, message):
        """
        This block of if statements checks for spam an disallows the input to be broadcast.
        It will also send a message to the user to not spam.
        """
        if int(round(time.time()*1000))-self.time < 300:
            self.time=int(round(time.time()*1000))
            if int(round(time.time()*1000))-self.spam_msg > 250:
                self.write_message("Server: <font color=\"red\">Please do not spam</font>")
                self.spam_msg=int(round(time.time()*1000))
            return None
        self.time=int(round(time.time()*1000))
        if message.startswith("/name"):
            server.change_name(self.client_id, message.split(" ",1)[1])
            return None
        if message.startswith("/topic"):
            if self.room != "all":
                server.broadcast(0,"{0} has left the topic".format(self.name), self.room)
            self.room = message.split(" ",1)[1]
            server.broadcast(0,"{0} has joined the topic".format(self.name), self.room)
            return None

        """
        Safegaurd to disallow xss and html injection.
        """
        message=message.replace('&','&amp;');
        message=message.replace('>','&gt;');
        message=message.replace('<','&lt;');
        message=message.replace('"','&quot;');
        message=message.replace("'","&#x27;");
        if(not bool(not message or message.isspace())):
            server.broadcast(self.client_id, message)

    def on_close(self):
        server.remove_client(self.client_id)
        server.broadcast(0, "{0} has left the chat".format(self.name), self.room)
          
application = tornado.web.Application([
    (r'/', WSEchoHandler),
])


def main(cfg):
    """
    A tornado application that supports serving websockets.
    cfg should be a dict-like thing with 'host' and 'port' entries.
    """
    app = tornado.web.Application([
            (r'/ws/echo', WSEchoHandler),
            ], debug=(cfg['debug']=="true"))

    server = tornado.httpserver.HTTPServer(app)
    server.listen(port=cfg['port'], address=cfg['host'])
    on = "on"
    if not cfg['debug']=="true":
        on = "off"
    print("starting server at http://{host}:{port}/".format(**cfg))
    print("Debug mode {0}".format(on))
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    cfg = { "host": "0.0.0.0", "port" : "8888","debug": "true" }
    main(cfg)
