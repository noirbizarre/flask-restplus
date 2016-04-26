#!/usr/bin/env python3

from flask import Flask
from zoo import api

app = Flask(__name__)
api.init_app(app)

if __name__ == '__main__':
    app.run(debug=True)
