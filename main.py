import sys

import gevent
from flask import Flask
from flask import request
from geventwebsocket.handler import WebSocketHandler


from app.app_runner import AppRunner


MASTER_SHEET_ID = sys.argv[1:][0]
app = Flask(__name__)


@app.route('/trigger_sched_solver/', methods=['POST'])
def check_if_text_is_recipe():
    if 'almog_tania_aviad_3981' != request.form['key']:
        return 'key_was_not_provided'
    else:
        AppRunner.trigger_flow(MASTER_SHEET_ID)
        return 'triggered the algorithm'



if __name__ == '__main__':
    server = gevent.pywsgi.WSGIServer( (u'0.0.0.0', 5000), app, handler_class=WebSocketHandler )
    server.serve_forever()