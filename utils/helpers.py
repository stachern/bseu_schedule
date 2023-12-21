from gaesessions import get_current_session

# TODO: Replace with Flask's `flash` method eventually:
#   https://flask.palletsprojects.com/en/1.1.x/quickstart/#message-flashing.
def _flash(message, session=None):
    if session is None:
        session = get_current_session()
    session['messages'] = [message]
