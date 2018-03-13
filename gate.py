from bottle import route, run
from api_methods.v1 import *
import config
import logging


# URL: http://config.server_host:config.server_port/<api_version>/<api_method>?<arg1>=...&<arg2>=...
@route('/<api_version:re:v\d+>/<api_method:re:([a-z]+_?)+>')
def meta_method(api_version, api_method):
    """ Meta-method
            Constructs method name from given api_version and api_method, and calls it if can.
            If not - returns error with status 400.
    """
    method_name = api_version + '_' + api_method + '()'
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
    try:
        logging.info("({})API method called: {}".format(client_ip, method_name))
        method_result = eval(method_name)
        logging.info("({}){} response status: {}".format(client_ip, method_name, json.loads(method_result)['status']))
        return method_result
    except NameError:
        logging.info("But, there is no such method. 400.")
        response.status = 400
        return json.dumps({'status': '400', 'error': 'Wrong API version or method name.'})


logging.basicConfig(
    filename='api.log',
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%d.%m.%y|%H:%M:%S"
)

# Create directory for profile photos if it doesn't exist
if not os.path.isdir('content'):
    os.mkdir('content')
    logging.info('Created content directory.')

run(host=config.server_host, port=config.server_port, debug=config.server_debug)
