from flask import Flask
from flask import request
app = Flask(__name__)
app.config['TESTING'] = True

@app.route('/')
def index():
    return 'index'

@app.route('/optimade/0.9.6/structures/')
def find():
    args = dict(request.args)
    return str(args)


if __name__ == '__main__':
    app.run(debug=True)
