#!flask/bin/python
from flask import Flask, jsonify, abort, make_response, request

app = Flask(__name__)

rules = [
    {
      'ruleid': 1,
      'enabled': u'true',
      'uri': u'v1.0/getRandomFact',
      'matchRules': {
        'method': u'GET',
        'roles': u'guest',
        'xauthz': u'api-v1.0'
      },
      'operation': {
        'url': u'http://numbersapi.com/random/year'
      }
    },
    {
      'ruleid': 2,
      'enabled': u'true',
      'uri': u'v1.0/getLocalIP',
      'matchRules': {
        'method': u'GET',
        'roles': u'guest netops',
        'xauthz': u'api-v1.0'
      },
      'operation': {
        'url': u'https://api.ipify.org/?format=json'
      }
    },
    {
      'ruleid': 3,
      'enabled': u'true',
      'uri': u'v2.0/testPost',
      'matchRules': {
        'method': u'POST',
        'roles': u'devops',
        'xauthz': u'api-v2.0'
      },
      'operation': {
        'url': u'https://jsonplaceholder.typicode.com/posts'
      }
    },
]

@app.route('/backend/fetchkey/<path:uri>', methods=['GET'])
def get_key(uri):
    rule = [rule for rule in rules if rule['uri'] == uri]
    if len(rule) == 0:
        abort(404)
    return jsonify({'rule': rule[0]})

@app.route('/backend/fetchallkeys', methods=['GET'])
def get_all_keys():
    return jsonify({'rules': rules})

@app.route('/jwks.json', methods=['GET'])
def get_jwks():
    return jsonify({"keys": [{ "k":"ZmFudGFzdGljand0", "kty":"oct", "kid":"0001" }]})

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
