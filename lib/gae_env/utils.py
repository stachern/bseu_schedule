from google.appengine.api import namespace_manager

__all__ = ['set_current_namespace', ]

def set_current_namespace(new_namespace):
    # type: (str) -> str
    """Set the app engine namespace for the current http session

    Arguments:
        new_namespace {str} -- The namespace to set to

    Returns:
        str -- The previously set namespace
    """
    previous_namespace = namespace_manager.get_namespace()
    namespace_manager.set_namespace(new_namespace)
    return previous_namespace

def run_in_namespace(func, namespace, *func_args, **func_kwargs):
    # type: (callable, str, list, dict) -> obj
    """ Run a function in the context of a Google App Engine namespace.

    Arguments:
        func {callable} -- The function/callable to be run.
        namespace {str} -- The GAE namespace to run :func: in.
        *func_args {list} -- Args that will be passed to :func:
        **func_kwargs {dict} -- Keyword args that will be passed to :func:
    """
    previous_namespace = set_current_namespace(namespace)
    try:
        return func(*func_args, **func_kwargs)
    finally:
        set_current_namespace(previous_namespace)
