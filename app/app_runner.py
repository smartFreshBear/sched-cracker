import gc
import logging
import pickle
import time

from algorithem import algorithm_based_priority_queue
from algorithem.algorithm_based_priority_queue import *
from algorithem.board_weighter import board_weighter
from uxui.googlesheetinterface import SpreadsheetClient
from uxui.user_data_convertor_googlesheet import UserDataConvertorGoogleSheetBased

logging.basicConfig(level=logging.INFO)

global LOAD_CONSTRAINTS_FROM_CACHE
LOAD_CONSTRAINTS_FROM_CACHE = False
SHOULD_CACHE = True

RESULT_SHEET_LOCATION = 'F5:F5'
EMPLOYEE_SHEET_ID_LOCATION = 'C9:C104'
RULES_LOCATION = 'E9:G45'
SHOULD_USE_CACHE_LOCATION = 'B6:B7'

SLEEP_BETWEEN_SPREADSHEET_CALL = 1


def get_all_rules():
    rules_table = SpreadsheetClient(MASTER_SHEET).load_cells_given_pair(RULES_LOCATION)
    disabled_rules = [int(rule[0].text) for rule in rules_table if len(rule) == 3 and rule[2].text == 'False']
    return [rule for rule in Rules.get_all_rules() if rule.get_id() not in disabled_rules]


def cache_employee_mid_week_constraints(constraints_to_cache):
    with open('constraints_midweek_file', 'wb') as constraints_midweek_file:
        logging.info("caching config is: {}".format(SHOULD_CACHE))
        if SHOULD_CACHE:
            pickle.dump(constraints_to_cache, constraints_midweek_file)


def load_constraints_mid_week_from_cache():
    with open('constraints_midweek_file', 'rb') as constraints_midweek_file:
        midweek_constrains = pickle.load(constraints_midweek_file)
        return midweek_constrains


def cache_employee_weekend_constraints(constraints_to_cache, employees_to_cache):
    with open('constraints_employees_file', 'wb') as constraints_employees_file:
        logging.info("caching config is: {}".format(SHOULD_CACHE))
        if SHOULD_CACHE:
            pickle.dump((constraints_to_cache, employees_to_cache), constraints_employees_file)


def load_constraints_weekend_from_cache():
    with open('constraints_employees_file', 'rb') as constraints_employees_file:
        constraints_cached, employees_cached = pickle.load(constraints_employees_file)
        return constraints_cached, employees_cached


class AppRunner:

    def __init__(self):
        self.board = PlanningBoard()
        self.kill_process = False
        self.loading_bar = 0
        self.message = ''
        self.employees = []
        self.did_weekend_finished = False
        self.did_midweek_started = False
        self.use_cached_constraints = False

    @staticmethod
    def should_load_constraint_from_cached():
        master_sheet_client = SpreadsheetClient(MASTER_SHEET)
        global LOAD_CONSTRAINTS_FROM_CACHE
        LOAD_CONSTRAINTS_FROM_CACHE = master_sheet_client.load_cells_given_pair(SHOULD_USE_CACHE_LOCATION)[0][
                                          0].text == 'True'

    @staticmethod
    def get_all_employee_ids():
        master_sheet_client = SpreadsheetClient(MASTER_SHEET)
        employees_sheet_ids = master_sheet_client.load_cells_given_pair(EMPLOYEE_SHEET_ID_LOCATION)
        return [cell.text for single_row in employees_sheet_ids for cell in single_row if cell.text != '']

    @staticmethod
    def get_result_sheet():
        master_sheet_client = SpreadsheetClient(MASTER_SHEET)
        result_table = master_sheet_client.load_cells_given_pair(RESULT_SHEET_LOCATION)
        return result_table[0][0].text

    def update_status_message(self, num_str, flow):
        self.message = 'flow: {}, percentage: {}'.format(flow, num_str)

    def get_employees_and_their_constraints_for_weekend(self):
        self.loading_bar = 0
        constraints = []
        employees = []
        ids_from_sheet = self.get_all_employee_ids()
        base = len(ids_from_sheet)
        for sheet_id in ids_from_sheet:
            self.kill_process_if_needed()
            data_convertor = UserDataConvertorGoogleSheetBased(SpreadsheetClient(sheet_id))
            employee = data_convertor.get_employee_details()
            employees.append(employee)
            weekend_constraints = EmployeeConstraintsForWeekends(from_weekend_to_constraints={}, employee=employee)
            for weekend in WeekOfTheMonth:
                self.kill_process_if_needed()
                logging.info("weekend-flow: getting constraints for employee {} week {}".format(employee.name, weekend))
                data_convertor.get_constraint_for_weekend(weekend, weekend_constraints)
            constraints.append(weekend_constraints)
            time.sleep(SLEEP_BETWEEN_SPREADSHEET_CALL)
            self.loading_bar = self.loading_bar + 1
            self.update_status_message(str((self.loading_bar / base) * 100) + '%', 'weekend')
        self.employees = employees
        return constraints, employees

    def get_employees_and_their_constraints_for_midweek(self):
        self.loading_bar = 0
        constraints = []
        employees = []
        ids_from_sheet = self.get_all_employee_ids()
        base = len(ids_from_sheet)
        for sheet_id in ids_from_sheet:
            self.kill_process_if_needed()
            data_convertor = UserDataConvertorGoogleSheetBased(SpreadsheetClient(sheet_id))
            employee = data_convertor.get_employee_details()
            employees.append(employee)
            midweek_constraints = EmployeeConstraintsForWeekDays(from_day_to_constraint={}, employee=employee)
            for week in WeekOfTheMonth:
                logging.info("mid-week-flow: getting constraints for employee {} week {}".format(employee.name, week))
                self.kill_process_if_needed()
                data_convertor.get_constraint_for_midweek(week, midweek_constraints)
            constraints.append(midweek_constraints)
            time.sleep(SLEEP_BETWEEN_SPREADSHEET_CALL)
            self.loading_bar = self.loading_bar + 1
            self.update_status_message(str((self.loading_bar / base) * 100) + '%', 'mid-week')

        return constraints, employees

    def get_result_sheet_convertor(self):
        result_sheet_id = self.get_result_sheet()
        convertor = UserDataConvertorGoogleSheetBased(SpreadsheetClient(result_sheet_id))
        return convertor

    def run_algorithm_for_weekend(self, constraints):
        self.loading_bar = 0
        employees = self.employees
        weight = 99999
        chosen_board = self.board
        base = 1000
        logging.info("weekend: going over on {} randomized options".format(base))
        rules = get_all_rules()

        for i in range(base):
            self.kill_process_if_needed()
            if weight == 0:
                break
            board_for_test = copy.deepcopy(self.board)
            random.shuffle(employees)
            random.shuffle(constraints)
            employee_fresh = copy.deepcopy(employees)

            algorithm_based_priority_queue.solve_weekend(board_for_test, employee_fresh, constraints, False,
                                                         rules)
            new_weight = board_weighter.weight_weekend(board_for_test)
            if new_weight < weight:
                weight = new_weight
                chosen_board = board_for_test
            else:
                del board_for_test, employee_fresh
                gc.collect()
                self.loading_bar = self.loading_bar + 1
            if i % 30 == 0:
                gc.collect()
                self.update_status_message(str((self.loading_bar / base) * 100) + '%', 'weekend-algo')

        self.update_status_message(str(100) + '%', 'weekend-algo')
        self.board = chosen_board

        convertor = self.get_result_sheet_convertor()
        for weekend in WeekOfTheMonth:
            self.kill_process_if_needed()
            time.sleep(SLEEP_BETWEEN_SPREADSHEET_CALL)
            convertor.write_weekend(weekend, self.board)
        self.update_status_message('DONE', 'weekend-algo')

    def run_algorithm_for_midweek(self, constraints):
        self.loading_bar = 0
        employees = self.employees
        weight = 99999
        chosen_board = self.board
        base = 2000
        logging.info("midweek: going over on {} randomized options".format(base))
        rules = get_all_rules()
        for i in range(base):
            self.kill_process_if_needed()
            if weight == 0:
                break

            board_for_test = copy.deepcopy(self.board)
            random.shuffle(employees)
            random.shuffle(constraints)
            employee_fresh = copy.deepcopy(employees)
            algorithm_based_priority_queue.solve_mid_week(board_for_test, employee_fresh, constraints, False,
                                                          rules)

            new_weight = board_weighter.weight_midweek(board_for_test)
            if new_weight < weight:
                weight = new_weight
                chosen_board = board_for_test
            else:
                del board_for_test, employee_fresh
            self.loading_bar = self.loading_bar + 1
            if i % 30 == 0:
                gc.collect()
                self.update_status_message(str((self.loading_bar / base) * 100) + '%', 'mid-week-algo')

        self.update_status_message(str(100) + '%', 'weekend-algo')
        self.board = chosen_board
        convertor = self.get_result_sheet_convertor()
        for week in WeekOfTheMonth:
            self.kill_process_if_needed()
            time.sleep(SLEEP_BETWEEN_SPREADSHEET_CALL)
            convertor.write_mid_week(week, self.board)
        self.update_status_message('DONE', 'midweek-algo')

    @staticmethod
    def mid_week_flow(app_runner, app_runners, master_sheet_id):
        app_runner.did_midweek_started = True
        global MASTER_SHEET
        MASTER_SHEET = master_sheet_id

        if LOAD_CONSTRAINTS_FROM_CACHE:
            mid_week_constraints = load_constraints_mid_week_from_cache()
        else:
            logging.info("loading midweek constraints from google sheets")
            mid_week_constraints, employees = app_runner.get_employees_and_their_constraints_for_midweek()
            cache_employee_mid_week_constraints(mid_week_constraints)
        app_runner.run_algorithm_for_midweek(mid_week_constraints)
        del mid_week_constraints
        gc.collect()
        app_runners.clear()
        app_runner.did_weekend_finished = False
        app_runner.did_midweek_started = False

    @staticmethod
    def weekend_flow(app_runner, master_sheet_id):
        global MASTER_SHEET
        MASTER_SHEET = master_sheet_id
        app_runner.should_load_constraint_from_cached()
        if LOAD_CONSTRAINTS_FROM_CACHE:
            logging.info("loading constraints from cache")
            weekend_constraints, employees = load_constraints_weekend_from_cache()
            app_runner.employees = employees
        else:
            logging.info("loading weekend constraints from google sheets")
            weekend_constraints, employees = app_runner.get_employees_and_their_constraints_for_weekend()
            cache_employee_weekend_constraints(weekend_constraints, employees)
        app_runner.run_algorithm_for_weekend(weekend_constraints)
        del weekend_constraints
        gc.collect()
        app_runner.did_weekend_finished = True
        return employees

    def kill_process_if_needed(self):
        if self.kill_process:
            raise Exception("stop for user request")
