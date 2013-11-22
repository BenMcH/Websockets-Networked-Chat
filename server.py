import tornado.httpserver
import tornado.websocket as ws
import tornado.ioloop
import tornado.wsgi
import tornado.web
 
class WSEchoHandler(ws.WebSocketHandler):
    # global clients
    # clients = list()
    def open(self):
        # self.clients.append(self)
        #Fails at anything involving clients...Not sure why :(
        print 'new connection'
        self.write_message("Hello World")
      
    def on_message(self, message):
        print 'message received %s' % message
        # for item in clients:
        #     item.write_message(message)
        # self.write_message("You said "+ message)
 
    def on_close(self):
        self.clients.remove(self)
        print 'connection closed'
 
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
            ws.send("Hello, world");
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
