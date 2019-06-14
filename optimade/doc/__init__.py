import json
import shutil
from pathlib import Path
from flask import Flask

from optimade.doc.swagger_ui import Swagger_UI


def run_server(api_file, port=5000, verbose=False):
    file = Path(api_file)

    if not file.is_file():
        raise FileExistsError(f'The json file of the OpenAPI doesn\'t existing at {str(file)}')

    with open(file, 'rb') as fb:
        config = json.loads(fb.read())

    api = Swagger_UI(api_dict=config)
    app = Flask(__name__)
    app.register_blueprint(api.get_blueprint(), url_prefix='/')

    # Run Flask server
    app.run(extra_files=[api_file], port=port, debug=verbose, use_reloader=verbose)


def build_static(api_file=None, api_url=None, path=Path('_build')):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

    if api_file:
        file = Path(api_file)

        if not file.is_file():
            raise FileExistsError(f'The json file of the OpenAPI doesn\'t existing at {str(file)}')

        # copy the static files into the build directory
        shutil.copy(str(file), str(path / 'openapi.json'))

        api_url = 'openapi.json'

    api = Swagger_UI(api_url=api_url)

    app = Flask(__name__)
    app.register_blueprint(api.get_blueprint(), url_prefix='/')

    with app.app_context():
        api.build_static(path)


if __name__ == '__main__':
    api_file = Path('../../openapi.json')

    # Build the static page
    build_static(api_file)

    # Start a flask server
    run_server(api_file)

