import logging

from flask import Flask
from flask.json.provider import DefaultJSONProvider

from webapp.launch_utils import run_create_app


# Specific to local dev environment.
def create_app() -> Flask:
    # temp logging config before proper setup
    logging.basicConfig(level=logging.INFO)

    app = Flask(__name__)
    json_provider = DefaultJSONProvider(app)
    json_provider.compact = True
    json_provider.sort_keys = False
    app.json = json_provider

    return run_create_app(app)


if __name__ == "__main__":
    app = create_app()

    app.run(host="127.0.0.1", port=5000, debug=True)
