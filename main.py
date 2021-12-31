import logging
import sys

import gevent
from flask import Flask
from flask import request
from geventwebsocket.handler import WebSocketHandler
from threading import Thread

from app.app_runner import AppRunner

MASTER_SHEET_ID = sys.argv[1:][0]
app = Flask(__name__)
list_of_app_runner = []

@app.route('/trigger_sched_solver/', methods=['POST'])
def trigger_algorithm():
    if 'almog_tania_aviad_3981' != request.form['key']:
        return 'key_was_not_provided'
    else:
        if len(list_of_app_runner) == 0:
            logging.info("preparation for running algo")
            app_runner = AppRunner()
            thread = Thread(target=AppRunner.trigger_flow, args=(MASTER_SHEET_ID, app_runner, ))
            thread.start()
            list_of_app_runner.append(app_runner)
            return 'algorithm_triggered'
        else:
            return 'there are still active session'


@app.route('/stop_sched_solver/', methods=['POST'])
def stop_algorithm():
    if 'almog_tania_aviad_3981' != request.form['key']:
        return 'key_was_not_provided'
    else:
        for app_runner in list_of_app_runner:
            app_runner.kill_process = True
        list_of_app_runner.clear()
        return 'stopped algorithm'


if __name__ == '__main__':
    server = gevent.pywsgi.WSGIServer( (u'0.0.0.0', 5042), app, handler_class=WebSocketHandler)
    logging.info("server is up and running")
    server.serve_forever()


# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5042, debug=False)
