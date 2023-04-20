# Sample project: AI Feedback App

<iframe src="https://www.loom.com/embed/e8ae0b8e60ca460e989f4ebc619403cb " frameborder="0" webkitallowfullscreen="" mozallowfullscreen="" allowfullscreen="" style="height: 400px; width: 600px"></iframe>

<iframe src="https://www.loom.com/embed/a0844e91dfa342fab5ed9375e4de2a06 " frameborder="0" webkitallowfullscreen="" mozallowfullscreen="" allowfullscreen="" style="height: 400px; width: 600px"></iframe>

How to replicate:

* [Install the Data Editing plugin](install-plugin).
* [Download project bundle](dss-bundle-ML_FEEDBACK_LOOP.zip) and import on your instance. Note: the project uses the managed Amazon S3 data connection provided on Dataiku Online — you may have to remap to one of your own data connections.
* Build dataset `test_scored` (recursive build).
* Go to Webapps and start "Editing predictions".
* Go to Dashboards and to "Review":
  * Make some edits
  * Click on the _Update model_ button, which will trigger the _Retrain model_ scenario.
* Use the _Reset edits_ scenario to reset all edits.
