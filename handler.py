import os
from google.appengine.ext.webapp import template
import webapp2


class RequestHandler(webapp2.RequestHandler):

    def render_to_response(self, template_name, context):
        self.response.out.write(template.render(os.path.join(os.path.dirname(__file__), template_name), context))