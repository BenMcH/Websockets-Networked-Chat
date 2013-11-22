from __future__ import print_function
import tornado.httpserver
import tornado.websocket as ws
import tornado.ioloop
import tornado.wsgi
import tornado.web

class ChatServer(object):
    """
    A chat server that broadcasts messages to multiple clients.
    """
    def __init__(self):
        self.clients = {}
        self.next_id = 1

    def name(self, client_id):
        if client_id == 0:
            return "Server"
        else:
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
            self.broadcast(0, msg)
        except Exception as e:
            print('ERROR: ', e)
        return client_id

    def remove_client(self, client_id):
        if client_id in self.clients:
            self.broadcast(0, "{0} has left the chat.".format(self.name(client_id)))
            del self.clients[client_id]

    def broadcast(self, sender_id, message):
        msg = "{0}: {1}".format(self.name(sender_id), message)
        for client in self.clients.values():
            client.write_message(msg)
        print(msg)

server = ChatServer()

class WSEchoHandler(ws.WebSocketHandler):

    def open(self):
        self.client_id = server.add_client(self)
        self.write_message("connected.")

    def on_message(self, message):
        server.broadcast(self.client_id, message)

    def on_close(self):
        server.remove_client(self.client_id)

def echo_test_wsgi(env, start):
    status = "200 OK"
    response_headers = [("Content-type", "text/html")]
    start(status, response_headers)

    js = """
    <html>
    <head>
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
      <script type="text/javascript">
        var ws = new WebSocket("ws://%s/ws/echo");
        ws.onopen = function() {
            ws.send("Hello, world!");
        };
        ws.onmessage = function (evt) {
            alert(evt.data);
        };
      </script>
    </head>
    <body>
      Hopefully, this will call the websocket.
    </body>
    </html>
    """ % (env['HTTP_HOST']) #  env['SERVER_PORT'])

    return js



application = tornado.web.Application([
    (r'/', WSEchoHandler),
])


def main(cfg):
    """
    A tornado application that supports serving both http and websockets.
    cfg should be a dict-like thing with 'host' and 'port' entries.
    """
    app = tornado.web.Application([
            (r'/ws/echo', WSEchoHandler),
            (r'/echo-test', tornado.web.FallbackHandler, {
                    'fallback': tornado.wsgi.WSGIContainer(echo_test_wsgi) }),
            ], debug=True)

    server = tornado.httpserver.HTTPServer(app)
    server.listen(port=cfg['port'], address=cfg['host'])

    print("starting server at http://{host}:{port}/".format(**cfg))
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    cfg = { "host": "0.0.0.0", "port" : "8888" }
    main(cfg)
