import logging
import sys

import gevent
from flask import Flask
from flask import request
from geventwebsocket.handler import WebSocketHandler
from threading import Thread
logging.basicConfig(level=logging.INFO)


from app.app_runner import AppRunner

MASTER_SHEET_ID = sys.argv[1:][0]
app = Flask(__name__)
list_of_app_runner = []


@app.route('/sched_solver_status/', methods=['POST'])
def sched_solver_status():
    if 'almog_tania_aviad_3981' != request.form['key']:
            return 'not process has started'
    else:
        if len(list_of_app_runner) == 0:
            return 'nothing is happening!'
        if len(list_of_app_runner) == 1:
            return list_of_app_runner[0].message


@app.route('/trigger_sched_solver_weekend/', methods=['POST'])
def trigger_sched_solver_weekend():
    if 'almog_tania_aviad_3981' != request.form['key']:
        return 'key_was_not_provided'
    else:
        if len(list_of_app_runner) == 0:
            logging.info("preparation for running algo")
            app_runner = AppRunner()
            thread = Thread(target=AppRunner.weekend_flow, args=(app_runner, MASTER_SHEET_ID))
            thread.start()
            list_of_app_runner.append(app_runner)
            return 'algorithm_triggered'
        else:
            return 'there are still active session stop weekend to delete and start again'


@app.route('/trigger_sched_solver_midweek/', methods=['POST'])
def trigger_sched_solver_midweek():
    if 'almog_tania_aviad_3981' != request.form['key']:
        return 'key_was_not_provided'

    if len(list_of_app_runner) == 0:
        return 'please start with weekend flow'

    if len(list_of_app_runner) == 1 and not list_of_app_runner[0].did_weekend_finished:
        return 'weekend wasn\'t finished'

    else:
        if len(list_of_app_runner) == 1 and not list_of_app_runner[0].did_midweek_started:
            logging.info("preparation for running algo")
            #MAKE SURE GIVE LIST OF APP_RUNNER IN ORDER TO STOP
            thread = Thread(target=AppRunner.mid_week_flow, args=(list_of_app_runner[0], list_of_app_runner, MASTER_SHEET_ID))
            thread.start()
            return 'algorithm_triggered'
        else:
            return 'there are still active session Or u didn\'t active weekend'


@app.route('/stop_sched_solver_weekend/', methods=['POST'])
def stop_sched_solver_weekend():
    if 'almog_tania_aviad_3981' != request.form['key']:
        return 'key_was_not_provided'
    else:
        for app_runner in list_of_app_runner:
            app_runner.kill_process = True
        list_of_app_runner.clear()
        return 'stopped algorithm'


@app.route('/stop_sched_solver_mid_week/', methods=['POST'])
def stop_sched_solver_mid_week():
    if 'almog_tania_aviad_3981' != request.form['key']:
        return 'key_was_not_provided'
    else:
        for app_runner in list_of_app_runner:
            app_runner.kill_process = True
        return 'stopped algorithm'


if __name__ == '__main__':
    server = gevent.pywsgi.WSGIServer( (u'0.0.0.0', 5042), app, handler_class=WebSocketHandler)
    logging.info("server is up and running")
    server.serve_forever()

