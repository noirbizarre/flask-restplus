from flask_restplus import Namespace, Resource, fields

api = Namespace('cats', description='Cats related operations')

cat = api.model('Cat', {
    'id': fields.Integer(required=True, description='The cat identifier'),
    'name': fields.String(required=True, description='The cat name'),
})

CATS = [
    {'id': 1, 'name': 'Felix'},
    {'id': 2, 'name': 'Garfield'},
    {'id': 3, 'name': 'Oliver'},
    {'id': 4, 'name': 'Rocky'},
]


@api.route('/')
class CatList(Resource):
    @api.doc('list_cats')
    @api.marshal_list_with(cat)
    def get(self):
        '''List all cats'''
        return CATS


@api.route('/<id>')
@api.param('id', 'The cat identifier')
@api.response(404, 'Cat not found')
class Cat(Resource):
    @api.doc('get_cat')
    @api.marshal_with(cat)
    def get(self, id):
        '''Fetch a cat given its identifier'''
        for cat in CATS:
            if cat['id'] == id:
                return cat
        api.abort(404)
