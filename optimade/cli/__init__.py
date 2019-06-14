import logging
import argparse
from pathlib import Path

logger = logging.getLogger(__name__)


def main(args=None):
    """Helper function for make it easy to call it from the terminal"""
    return ArgumentParser()(args)


class ArgumentParser(argparse.ArgumentParser):

    def __init__(self):
        """Initialisation method for the parser class"""
        super().__init__(description='Command line tools for the OptiMaDe API')
        self.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode')

        # Subparsers for the separate commands:
        self.subparsers = self.add_subparsers(title='Commands', dest='command', parser_class=argparse.ArgumentParser)

        # self.generate_json_parser = self.subparsers.add_parser(
        #     'generate-json', help='Generate the OpenAPI json file based on th FastAPI python code')
        # self.generate_json_parser.set_defaults(callback_func=generate_json)
        # self.generate_json_parser.add_argument(dest='path', default='openapi.json',
        #                                        help='file or folder which contains the xyz files')
        # self.generate_json_parser.add_argument('-y', '--yes', action='store_true',
        #                                        help='Allows to overwrite existing files')
        self.server_parser = self.subparsers.add_parser(
            'server', help='Launches a local server using the FastAPI.')
        self.server_parser.set_defaults(callback_func=run_server)
        self.server_parser.add_argument('-p', '--port', help='port number', default=5000, type=int)

        self.generate_doc_parser = self.subparsers.add_parser(
            'generate-doc', help='Generate the static page based on the OpenAPI json file.')
        self.generate_doc_parser.set_defaults(callback_func=generate_doc)
        self.generate_doc_parser.add_argument('-file', '--api_file', dest='api_file', type=Path,
                                              help='The OpenAPI JSON file')
        self.generate_doc_parser.add_argument('-u', '--api_url', dest='api_url', help='The OpenAPI JSON url')
        self.generate_doc_parser.add_argument(dest='output_folder', default='_build/', type=Path,
                                              help='The Folder of the built static page')

        self.server_doc_parser = self.subparsers.add_parser(
            'server-doc', help='Launches a local server to serve the Swagger UI documentation of the API.')
        self.server_doc_parser.set_defaults(callback_func=run_server_doc)
        self.server_doc_parser.add_argument(dest='input_json_file', type=Path, help='The OpenAPI JSON file')
        self.server_doc_parser.add_argument('-p', '--port', help='port number', default=5000, type=int)
        self.server_doc_parser.add_argument('-r', '--reload', action='store_true',
                                            help='Allows to overwrite existing files')

        self.test_parser = self.subparsers.add_parser('test', help='Runs the standard python test on the package')
        self.test_parser.set_defaults(callback_func=test)

    def __call__(self, args=None):
        namespace = self.parse_args(args)

        if namespace.verbose:
            # Remove all handlers associated with the root logger object.
            # https://stackoverflow.com/questions/12158048/changing-loggings-basicconfig-which-is-already-set
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)

            logging.basicConfig(level=logging.INFO)
            logger.info('Verbose mode is active')

        if not namespace.command:
            print(self.format_help())
            return

        # return namespace.callback_func(**namespace.__dict__)
        return namespace.callback_func(namespace)


def generate_json(namespace):
    logger.info('generate-json args: \n{}'.format(namespace))


def generate_doc(namespace):
    logger.info('generate-doc args: \n{}'.format(namespace))
    from optimade.doc import build_static

    build_static(namespace.api_file, namespace.api_url, namespace.output_folder)


def run_server_doc(namespace):
    logger.info('server-doc args: \n{}'.format(namespace))
    from optimade.doc import run_server

    run_server(namespace.input_json_file, port=namespace.port)


def run_server(namespace):
    logger.info('server args: \n{}'.format(namespace))

    import uvicorn
    from optimade.server.main import app

    uvicorn.run(
        app,
        port=namespace.port,
        log_level='debug' if namespace.verbose else 'info'
    )


def test(namespace):
    logger.info(f'test args: \n{namespace}')
    import pytest
    import optimade

    path = optimade.__path__[0]
    pytest.main(['-x', path])
