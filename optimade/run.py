from optimade.server.main import app
from optimade.server.config import CONFIG

if __name__ == "__main__":
    import uvicorn

    CONFIG.debug = True

    uvicorn.run(app, host="0.0.0.0", port=5000)
