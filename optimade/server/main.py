"""The OPTIMADE server

This is an example implementation with example data.
To implement your own server see the documentation at https://optimade.org/optimade-python-tools.
"""

from optimade.server.config import ServerConfig
from optimade.server.create_app import create_app

app = create_app(ServerConfig())
