from app.views import update_run


def setup_routes(app):
    app.add_url_rule('/notification/update_run', view_func=update_run)
