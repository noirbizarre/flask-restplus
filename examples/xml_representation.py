# needs: pip install python-simplexml
from simplexml import dumps
from flask import make_response, Flask
from flask_restplus import Api, Resource, fields


def output_xml(data, code, headers=None):
    """Makes a Flask response with a XML encoded body"""
    resp = make_response(dumps({'response': data}), code)
    resp.headers.extend(headers or {})
    return resp

app = Flask(__name__)
api = Api(app, default_mediatype='application/xml')
api.representations['application/xml'] = output_xml

hello_fields = api.model('Hello', {'entry': fields.String})


@api.route('/<string:entry>')
class Hello(Resource):
    """
        # you need requests
        >>> from requests import get
        >>> get('http://localhost:5000/me').content # default_mediatype
        '<?xml version="1.0" ?><response><hello>me</hello></response>'
        >>> get('http://localhost:5000/me', headers={"accept":"application/json"}).content
        '{"hello": "me"}'
        >>> get('http://localhost:5000/me', headers={"accept":"application/xml"}).content
        '<?xml version="1.0" ?><response><hello>me</hello></response>'
    """
    @api.doc(model=hello_fields, params={'entry': 'The entry to wrap'})
    def get(self, entry):
        '''Get a wrapped entry'''
        return {'hello': entry}


if __name__ == '__main__':
    app.run(debug=True)
