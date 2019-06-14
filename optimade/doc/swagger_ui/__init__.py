import json
import shutil
from pathlib import Path

from flask.blueprints import Blueprint
from flask import jsonify, render_template, send_from_directory

PATH = Path(__path__[0])


class Swagger_UI(object):
    def __init__(self, api_dict=None, api_url='openapi.json', title='API documentation'):
        super().__init__()

        self.api_url = api_url
        self.api_dict = api_dict
        self.title = title

    def get_blueprint(self):
        bp = Blueprint(
            'swaggerui',
            __name__,
            template_folder='templates',
            static_folder='swagger',
            static_url_path='swagger'
        )

        @bp.route(r'/')
        def get_doc():
            return self.render_index()

        if self.api_dict:
            @bp.route(f'{self.api_url}')
            def config_handler():
                return jsonify(self.api_dict)

        return bp

    def render_index(self):
        return render_template('index.html', title=self.title, api_url=self.api_url)

    def build_static(self, path):
        static_folder = path / 'swagger'
        static_folder.mkdir(parents=True, exist_ok=True)

        with open(path / 'index.html', 'w') as f:
            f.write(self.render_index())

        # copy the static files into the build directory
        for file in (PATH / 'swagger').glob('*'):
            shutil.copy(str(file), str(static_folder))

        if self.api_dict:
            with open(path / self.api_url, 'w', encoding='utf-8') as file:
                json.dump(self.api_dict, file, ensure_ascii=False, indent=2)
