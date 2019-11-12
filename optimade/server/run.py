import uvicorn
from optimade.server.main import app

if __name__ == '__main__':
    # uvicorn.run("main:app", port=5000, reload=True)
    uvicorn.run(app=app, port=5000)
