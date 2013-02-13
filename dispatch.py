import webapp2
import urls

site_app = webapp2.WSGIApplication(urls.SITE_URLS, debug=True)
tasks_app = webapp2.WSGIApplication(urls.TASKS_URLS, debug=True)