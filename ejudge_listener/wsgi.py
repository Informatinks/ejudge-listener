from ejudge_listener import create_app
from ejudge_listener.config import CONFIG_MODULE

application = create_app(CONFIG_MODULE)

if __name__ == '__main__':
    application.run()