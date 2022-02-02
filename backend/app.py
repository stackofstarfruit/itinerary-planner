##import googlemaps

from flask import Flask, send_from_directory
from flask_restful import Api
from flask_cors import CORS, cross_origin #comment this on deployment
from api.api_handler import api_handler
import sys

app = Flask(__name__, static_url_path='', static_folder='frontend/build')
CORS(app) #comment this on deployment
api = Api(app)
app.config['CORS_HEADERS'] = 'Content-Type'
@cross_origin()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and sys.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    app.run(debug=True)

api.add_resource(api_handler, '/flask/yelp')