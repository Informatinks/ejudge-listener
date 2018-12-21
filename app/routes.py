from app.views import update


def setup_routes(app):
    app.add_url_rule('/notification/update_run', view_func=update)
