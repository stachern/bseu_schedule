def setup_logging():
    import os

    if not os.environ.get('GAE_ENV') == 'localdev':
        # Imports the Cloud Logging client library
        import google.cloud.logging

        # Instantiates a client
        client = google.cloud.logging.Client()

        # Retrieves a Cloud Logging handler based on the environment
        # you're running in and integrates the handler with the
        # Python logging module. By default this captures all logs
        # at INFO level and higher
        client.setup_logging()

    global logging
    # Imports Python standard library logging
    import logging
