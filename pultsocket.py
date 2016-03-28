import random, string
import tornado.ioloop
import tornado.websocket
import tornado.web
from tornado.concurrent import Future
from tornado import gen

# for Web Socket
listeners = {}

# for Long Polling
waiters = {}

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
    """
    Web Server handler for event updates
    """

    __key__ = None

    def check_origin(self, origin):
        return True

    def open(self, key):
        self.__key__ = key
        if key not in listeners:
            listeners[key] = self
        print("WebSocket opened: %s" % key)

    def on_message(self, message):
        print("Received from %s: %s" % (self.__key__, message))
        if self.__key__ in listeners:
            listeners[self.__key__].write_message(message)

    def on_close(self):
        del listeners[self.__key__]
        print("WebSocket closed: %s" % self.__key__)


class MessageNewHandler(tornado.web.RequestHandler):
    """
    New message handler for long polling
    """
    def post(self, key):
        message = self.get_argument("message")
        if key in waiters:
            waiter = waiters[key]
            waiter.set_result(message)
            print("Received from %s: %s" % (key, message))
        else:
            print("Nobody waits for %s" % key)


class MessageUpdateHandler(tornado.web.RequestHandler):
    """
    Asynchronous handler for event updates (long polling)
    """

    @gen.coroutine
    def post(self, key):
        self.future = Future()
        waiters[key] = self.future
        value = yield self.future
        if self.request.connection.stream.closed():
            return
        self.write(value)


if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/pult/(.*)", PultHandler),
        (r"/ws/(.*)", WSHandler),
        (r"/poll/(.*)", MessageUpdateHandler),
        (r"/new/(.*)", MessageNewHandler),
    ])
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
