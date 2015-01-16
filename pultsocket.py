import tornado.ioloop
import tornado.websocket
import tornado.web
import random, string


LISTENERS = {}


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        key = self.get_cookie('user_key', None)
        if not key:
            key = ''.join(random.choice(string.lowercase + string.digits) for i in range(8))
            self.set_cookie('user_key', key)
        self.render("index.html", key=key, host=self.request.host)


class PultHandler(tornado.web.RequestHandler):
    def get(self, key):
        self.render("pult.html", key=key, host=self.request.host)


class WSHandler(tornado.websocket.WebSocketHandler):

    __key__ = None

    def check_origin(self, origin):
        return True

    def open(self, key):
        self.__key__ = key
        if key not in LISTENERS:
            LISTENERS[key] = self
        print "WebSocket opened: %s" % key

    def on_message(self, message):
        print "Received from %s: %s" % (self.__key__, message)
        if self.__key__ in LISTENERS:
            LISTENERS[self.__key__].write_message(message)

    def on_close(self):
        del LISTENERS[self.__key__]
        print "WebSocket closed: %s" % self.__key__


if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/pult/(.*)", PultHandler),
        (r"/ws/(.*)", WSHandler),
    ])
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
