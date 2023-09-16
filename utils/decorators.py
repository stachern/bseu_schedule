from flask import abort
from google.appengine.api import memcache
from google.appengine.api import users
import functools
import logging


def decorator_with_args(decorator_to_enhance):
    """
    This function is supposed to be used as a decorator.
    It must decorate an other function, that is intended to be used as a decorator.
    Take a cup of coffee.
    It will allow any decorator to accept an arbitrary number of arguments,
    saving you the headache to remember how to do that every time.

    This comes from http://stackoverflow.com/questions/739654/understanding-python-decorators
    """

    # We use the same trick we did to pass arguments
    def decorator_maker(*args, **kwargs):

        # We create on the fly a decorator that accepts only a function
        # but keeps the passed arguments from the maker .
        def decorator_wrapper(func):

            # We return the result of the original decorator, which, after all,
            # IS JUST AN ORDINARY FUNCTION (which returns a function).
            # Only pitfall : the decorator must have this specific signature or it won't work :
            return decorator_to_enhance(func, *args, **kwargs)

        return decorator_wrapper

    return decorator_maker


@decorator_with_args
def cached(func, *args, **kwargs):
    """
    Caches the result of a method for a specified time in seconds

    Use it as:

      @cached(time=1200)
      def functionToCache(arguments):
    Note:
      @cached
      def function(args):

      WILL NOT WORK - decorator has to be called
    """
    @functools.wraps(func)
    def wrapper(*pars, **kpars):
        key = func.__name__ + '_' + '_'.join([str(par) for par in pars])
        val = memcache.get(key)
        logging.debug('Cache lookup for %s, found: %s', key, val is not None)
        if not val:
            val = func(*pars, **kpars)
            memcache.set(key, val, time=kwargs['time'])
        return val

    return wrapper


def memoized(obj):
    cache = obj.cache = {}

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        if args not in cache:
            cache[args] = obj(*args, **kwargs)
        return cache[args]
    return memoizer


def login_required(f):
    """A decorator to require that a user be logged in to access a URL.

    To use it, decorate your route function like this:

        @app.route('/greet')
        @login_required
        def greet():
            user = users.get_current_user()
            return render_template_string('Hello, ' + user.nickname())

    We will redirect to a login page if the user is not logged in. We always
    redirect to the request URL, and Google Accounts only redirects back as a GET
    request, so this should not be used for POSTs.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        user = users.get_current_user()
        if not user:
            return redirect(users.create_login_url(request.url))
        else:
            return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """A decorator to require that a user be an admin for this application
    to access a URL.

    To use it, decorate your route function like this:

        @app.route('/greet')
        @admin_required
        def greet():
            user = users.get_current_user()
            return render_template_string('Hello, ' + user.nickname())

    We will redirect to a login page if the user is not logged in. We always
    redirect to the request URL, and Google Accounts only redirects back as
    a GET request, so this should not be used for POSTs.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        user = users.get_current_user()
        if not user:
            return redirect(users.create_login_url(request.url))
        elif not users.is_current_user_admin():
            return abort(403)
        else:
            return f(*args, **kwargs)
    return decorated_function
