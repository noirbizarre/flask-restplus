from flask_restplus import Namespace, Resource, fields

api = Namespace('dogs', description='Dogs related operations')

dog = api.model('Dog', {
    'id': fields.Integer(required=True, description='The dog identifier'),
    'name': fields.String(required=True, description='The dog name'),
})

DOGS = [
    {'id': 1, 'name': 'Chase'},
    {'id': 2, 'name': 'Marshal'},
    {'id': 3, 'name': 'Skye'},
    {'id': 4, 'name': 'Rocky'},
    {'id': 5, 'name': 'Rubble'},
    {'id': 6, 'name': 'Zuma'},
    {'id': 7, 'name': 'Everest'},
]


@api.route('/')
class DogList(Resource):
    @api.doc('list_dogs')
    @api.marshal_list_with(dog)
    def get(self):
        '''List all dogs'''
        return DOGS


@api.route('/<id>')
@api.param('id', 'The dog identifier')
@api.response(404, 'Dog not found')
class Dog(Resource):
    @api.doc('get_dog')
    @api.marshal_with(dog)
    def get(self, id):
        '''Fetch a dog given its identifier'''
        for dog in DOGS:
            if dog['id'] == id:
                return dog
        api.abort(404)
