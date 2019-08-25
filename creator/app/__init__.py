from flask import Flask
from .extensions import task


class CreatorApp(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__('CreatprApp', *args, **kwargs)
        self.setup_config()
        self.setup_extensions()
        self.setup_views()

    def setup_config(self):
        self.config.from_object('config.Config')

    def setup_extensions(self):
        task.init_app(self)

    def setup_views(self):
        from .views import main
        self.register_blueprint(main)
