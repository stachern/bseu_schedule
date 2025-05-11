[![Code Climate Maintainability](https://codeclimate.com/github/stachern/bseu_schedule.svg)](https://codeclimate.com/github/stachern/bseu_schedule)

# Schedule+

A simple webapp for Google App Engine for the students of Belarus State Economic University - parses student classes schedule from university website bseu.by and creates events in Google Calendar

## Available at:

The resource is located at [bseu-api.appspot.com](https://bseu-api.appspot.com/).

## Used stuff:

* Google App Engine Gen 2 with [legacy bundled services](https://pypi.org/project/appengine-python-standard/)
* Python 3.12.x
* Flask framework
* Cloud Tasks
* lxml
* leaf as lxml wrapper
* twitter bootstrap for responsive UI

## Setup

You might need to [download Cloud SDK](https://cloud.google.com/sdk/docs/install) and configure `gcloud` first:

    gcloud init
    gcloud auth login

NOTE if you're using macOS then the easiest way to install Google Cloud SDK is via Homebrew:

    brew install google-cloud-sdk

### Installing Dependencies

Create an isolated Python environment to manage application dependencies (this creates a directory in your current directory):

    python3 -m venv venv

On Linux or Mac, activate the new Python environment:

    source venv/bin/activate

Because you've created your virtual environment using a version of Python 3, you don't need to call `python3` or `pip3` explicitly.
As long as your virtual environment is active, `python` and `pip` link to the same executable files that `python3` and `pip3` do.

    python -m pip install <package-name>

As long as you don't close your terminal, every Python package that you install will end up in this isolated environment instead of your global Python site-packages.

Install dependencies listed in `requirements.txt` using:

    python -m pip install -r requirements.txt

Once you're done working with this virtual environment, you can deactivate it:

    (venv) $ deactivate

If you interact with `python` or `pip` now, you'll interact with your globally configured Python environment.

More on Python virtual environments:

* https://realpython.com/python-virtual-environments-a-primer/
* https://cloud.google.com/appengine/docs/standard/python3/building-app/writing-web-service#testing_your_web_service

### Running Locally

Use `dev_appserver.py` from Google Cloud SDK to run the app locally, e.g.:

    python3 /usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/bin/dev_appserver.py --application=bseu-api --env_var APPLICATION_ID=dev~bseu-api app.yaml

OR

    python3 /opt/homebrew/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/bin/dev_appserver.py --application=bseu-api --env_var APPLICATION_ID=dev~bseu-api app.yaml

if using an Apple Silicon (arm64) mac.

NOTE the `--env_var APPLICATION_ID=dev~bseu-api` param – this is necessary to open the `Datastore Viewer` located on admin server at http://localhost:8000/datastore.

More on running a dev server locally:

* https://cloud.google.com/appengine/docs/standard/tools/using-local-server?tab=python
* https://cloud.google.com/appengine/docs/standard/testing-and-deploying-your-app?tab=python#running_the_local_development_server_3

### Setting Secrets

In order for the app to run properly, `client_id` and `client_secret` secrets need to be set.

To set them:

* start the app locally
* head over to the [`Datastore Viewer`](http://localhost:8000/datastore)
* find already created corresponding `GaeEnvSettings` records
* and replace their values with those for the only OAuth 2.0 Client ID on the [project's Google Cloud Credentials page](https://console.cloud.google.com/apis/credentials?project=bseu-api)

### Debugging

Should you need to debug anything, make sure to put this line where needed:

```python
import pdb; pdb.set_trace()
```

More on Python debugging:

* https://realpython.com/python-debugging-pdb/
* https://code.visualstudio.com/docs/python/debugging

## Deployment:

Use `gcloud` instead of the deprecated `appcfg` to deploy the project to the App Engine server:

    gcloud app deploy --project bseu-api -v 2-9-1

You might need to [download Cloud SDK](https://cloud.google.com/sdk/docs/install) and configure `gcloud` first:

    gcloud init
    gcloud auth login

### Update cron jobs

Any time a `cron.yaml` file gets modified and deployed, make sure to run the following command:

    gcloud app deploy cron.yaml

To list cron jobs and see their statuses, head over to the [`App Engine Cron Jobs` tab on `Cloud Scheduler`](https://console.cloud.google.com/cloudscheduler?project=bseu-api).

More info on cron jobs:

* https://cloud.google.com/appengine/docs/standard/scheduling-jobs-with-cron-yaml#uploading_cron_jobs
