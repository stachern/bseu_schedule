# Schedule+

A simple webapp for Google App Engine for the students of Belarus State Economic University - parses student classes schedule from university website bseu.by and creates events in Google Calendar

## Available at:

The resource is hosted under [bseu-api.appspot.com](https://bseu-api.appspot.com/).

## Used stuff:

* Flask framework
* lxml
* leaf as lxml wrapper
* twitter bootstrap for responsive UI

## Deployment:

Use `gcloud` instead of the deprecated `appcfg` to deploy the project to the App Engine server:

    gcloud app deploy --project bseu-api -v 2-5-2

You might need to [download Cloud SDK](https://cloud.google.com/sdk/docs/install) and configure `gcloud` first:

    gcloud init
    gcloud auth login

### Update cron jobs

Any time a `cron.yaml` file gets modified and deployed, make sure to run the following command:

    gcloud app deploy cron.yaml

To list cron jobs and see their statuses, head over to the [`App Engine Cron Jobs` tab on `Cloud Scheduler`](https://console.cloud.google.com/cloudscheduler?project=bseu-api).

More info on cron jobs:

* https://cloud.google.com/appengine/docs/legacy/standard/python/config/cron#upload-cron

## Run Locally:

Use `dev_appserver.py` from Google Cloud SDK to run the app locally, e.g.:

    python3 /usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/bin/dev_appserver.py --application=bseu-api --env_var APPLICATION_ID=dev~bseu-api app.yaml

NOTE the `--env_var APPLICATION_ID=dev~bseu-api` param – this is necessary to open the `Datastore Viewer` located on admin server at http://localhost:8000/datastore.

More on running a dev server locally:

* https://cloud.google.com/appengine/docs/legacy/standard/go111/tools/using-local-server
* https://cloud.google.com/appengine/docs/standard/testing-and-deploying-your-app?tab=python#running_the_local_development_server_3

### Setting Secrets

In order for the app to run properly, `client_id` and `client_secret` secrets need to be set.

To set them:

* start the app locally
* head over to the [`Datastore Viewer`](http://localhost:8000/datastore)
* find already created corresponding `GaeEnvSettings` records
* and replace their values with those for the only OAuth 2.0 Client ID on the [project's Google Cloud Credentials page](https://console.cloud.google.com/apis/credentials?project=bseu-api)
