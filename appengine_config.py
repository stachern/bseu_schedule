from gaesessions import SessionMiddleware

COOKIE_KEY = 'oib23b234,mnasd[f898yhk4jblafiuhd2jk341m2n3vb'

def webapp_add_wsgi_middleware(app):
    app = SessionMiddleware(app, cookie_key=COOKIE_KEY)
    return app