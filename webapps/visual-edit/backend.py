def create_app():
    from webapp.launch_utils import run_create_app

    return run_create_app(app)  # type: ignore


create_app()
