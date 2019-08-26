from sanic import Sanic


class CreatorApp(Sanic):
    def __init__(self, *args, **kwargs):
        super().__init__('CreatprApp', *args, **kwargs)
        self.setup_config()
        self.setup_views()
        self.ws_clients = set()

    def setup_config(self):
        self.config.from_object('config.Config')

    def setup_views(self):
        from .views import notify, feed
        self.blueprint(notify)
        self.add_websocket_route(feed, '/feed')
