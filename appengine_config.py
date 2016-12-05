from google.appengine.ext import vendor

# Add any libraries installed in the "lib" folder
vendor.add('lib')

from gaesessions import SessionMiddleware

COOKIE_KEY = 'oib23b234,mnasd[f898yhk4jblafiuhd2jk341m2n3vb'

def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    app = SessionMiddleware(app, cookie_key=COOKIE_KEY)
    app = recording.appstats_wsgi_middleware(app)
    return app
