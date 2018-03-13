from bottle import route, run, Bottle
from api_methods.v1 import *
import config
# TODO: add logging


# URL: http://config.server_host:config.server_port/<api_version>/<api_method>?<arg1>=...&<arg2>=...
@route('/<api_version:re:v\d+>/<api_method:re:([a-z]+_?)+>')
def meta_method(api_version, api_method):
    """ Meta-method
            Constructs method name from given api_version and api_method, and calls it if can.
            If not - returns error with status 400.
    """
    method_name = api_version + '_' + api_method + '()'
    try:
        method_result = eval(method_name)
        return method_result
    except NameError:
        response.status = 400
        return json.dumps({'status': '400', 'error': 'Wrong API version or method name.'})


run(host=config.server_host, port=config.server_port, debug=config.server_debug)
