import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
 
class WSHandler(tornado.websocket.WebSocketHandler):
    global clients
    clients = list()
    def open(self):
        self.clients.append(self)
        #Fails at anything involving clients...Not sure why :(
        print 'new connection'
        self.write_message("Hello World")
      
    def on_message(self, message):
        print 'message received %s' % message
        for item in clients:
            item.write_message(message)
       # self.write_message("You said "+ message)
 
    def on_close(self):
      self.clients.remove(self)
      print 'connection closed'
 
 
application = tornado.web.Application([
    (r'/', WSHandler),
])
 
 
if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
