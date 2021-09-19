# Schedule+

A simple webapp for Google App Engine for the students of Belarus State Economic University - parses student classes schedule from university website bseu.by and creates events in Google Calendar

## Available at:

The resource is hosted under [bseu-api.appspot.com](https://bseu-api.appspot.com/).

## Used stuff:

* webapp2 framework
* lxml
* leaf as lxml wrapper
* twitter bootstrap for responsive UI
* python-dateutil for computing date

## Deployment:

Use `gcloud` instead of the deprecated `appcfg` to deploy the project to the App Engine server:

    gcloud app deploy --project bseu-api -v 2-5-2

You might need to [download Cloud SDK](https://cloud.google.com/sdk/docs/install) and configure `gcloud` first:

    gcloud init
    gcloud auth login
