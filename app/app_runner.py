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

LOAD_CONSTRAINTS_FROM_CACHE = False
SHOULD_CACHE = False

RESULT_SHEET_LOCATION = 'I1:I1'
EMPLOYEE_SHEET_ID_LOCATION = 'B2:B100'
RULES_LOCATION = 'D2:F17'


class AppRunner:

    def __init__(self):
        self.board = PlanningBoard()
        self.kill_process = False

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

    def get_employees_and_their_constraints_for_weekend(self):
        constraints = []
        employees = []
        for sheet_id in self.get_all_employee_ids():
            self.kill_process_if_needed()
            data_convertor = UserDataConvertorGoogleSheetBased(SpreadsheetClient(sheet_id))
            employee = data_convertor.get_employee_details()
            employees.append(employee)
            weekend_constraints = EmployeeConstraintsForWeekends(from_weekend_to_constraints={}, employee=employee)
            for weekend in WeekOfTheMonth:
                self.kill_process_if_needed()
                # need to enforce less calling to api
                logging.info("weekend-flow: getting constraints for employee {} week {}".format(employee.name, weekend))
                time.sleep(6)
                data_convertor.get_constraint_for_weekend(weekend, weekend_constraints)
            constraints.append(weekend_constraints)
            time.sleep(10)
        return constraints, employees

    def get_employees_and_their_constraints_for_midweek(self):
        constraints = []
        employees = []
        for sheet_id in self.get_all_employee_ids():
            self.kill_process_if_needed()
            data_convertor = UserDataConvertorGoogleSheetBased(SpreadsheetClient(sheet_id))
            employee = data_convertor.get_employee_details()
            employees.append(employee)
            midweek_constraints = EmployeeConstraintsForWeekDays(from_day_to_constraint={}, employee=employee)
            for week in WeekOfTheMonth:
                # need to enforce less calls to api
                logging.info("mid-week-flow: getting constraints for employee {} week {}".format(employee.name, week))
                time.sleep(6)
                self.kill_process_if_needed()
                data_convertor.get_constraint_for_midweek(week, midweek_constraints)
            constraints.append(midweek_constraints)
            time.sleep(10)
        return constraints, employees

    def get_all_rules(self):
        rules_info = SpreadsheetClient(MASTER_SHEET).load_cells_given_pair(RULES_LOCATION)
        disabled_rules = [int(rule[0].text) for rule in rules_info if rule[2].text == 'False']
        return [rule for rule in Rules.get_all_rules() if rule.get_id() not in disabled_rules]



    def get_result_sheet_convertor(self):
        result_sheet_id = self.get_result_sheet()
        convertor = UserDataConvertorGoogleSheetBased(SpreadsheetClient(result_sheet_id))
        return convertor

    def run_algorithm_for_weekend(self, employees, constraints):
        weight = 99999
        chosen_board = self.board
        logging.info("weekend: going over on 6000 randomized options")
        for i in range(6000):
            self.kill_process_if_needed()
            if weight == 0:
                break
            board_for_test = copy.deepcopy(self.board)
            random.shuffle(employees)
            random.shuffle(constraints)
            employee_fresh = copy.deepcopy(employees)

            algorithm_based_priority_queue.solve_weekend(board_for_test, employee_fresh, constraints, False,
                                                         self.get_all_rules())
            new_weight = board_weighter.weight_weekend(board_for_test)
            if new_weight < weight:
                weight = new_weight
                chosen_board = board_for_test
            else:
                del board_for_test
                gc.collect()

        self.board = chosen_board

        convertor = self.get_result_sheet_convertor()
        for weekend in WeekOfTheMonth:
            time.sleep(6)
            convertor.write_weekend(weekend, self.board)

    def run_algorithm_for_midweek(self, employees, constraints):
        weight = 99999
        chosen_board = self.board
        logging.info("midweek: going over on 4000 randomized options")
        for i in range(4000):
            self.kill_process_if_needed()
            if weight == 0:
                break

            board_for_test = copy.deepcopy(self.board)
            random.shuffle(employees)
            random.shuffle(constraints)
            employee_fresh = copy.deepcopy(employees)
            algorithm_based_priority_queue.solve_mid_week(board_for_test, employee_fresh, constraints, False,
                                                          self.get_all_rules())

            new_weight = board_weighter.weight_midweek(board_for_test)
            if new_weight < weight:
                weight = new_weight
                chosen_board = board_for_test
            else:
                del board_for_test
                gc.collect()

        self.board = chosen_board
        convertor = self.get_result_sheet_convertor()
        for week in WeekOfTheMonth:
            time.sleep(6)
            convertor.write_mid_week(week, self.board)

    def load_constraints_weekend_from_cache(self):
        with open('constraints_employees_file', 'rb') as constraints_employees_file:
            constraints_cached, employees_cached = pickle.load(constraints_employees_file)
            return constraints_cached, employees_cached

    def cache_employee_weekend_constraints(self, constraints_to_cache, employees_to_cache):
        with open('constraints_employees_file', 'wb') as constraints_employees_file:
            logging.info("caching config is: {}".format(SHOULD_CACHE))
            if SHOULD_CACHE:
                pickle.dump((constraints_to_cache, employees_to_cache), constraints_employees_file)

    def load_constraints_mid_week_from_cache(self):
        with open('constraints_midweek_file', 'rb') as constraints_midweek_file:
            midweek_constrains = pickle.load(constraints_midweek_file)
            return midweek_constrains

    def cache_employee_mid_week_constraints(self, constraints_to_cache):
        with open('constraints_midweek_file', 'wb') as constraints_midweek_file:
            logging.info("caching config is: {}".format(SHOULD_CACHE))
            if SHOULD_CACHE:
                pickle.dump(constraints_to_cache, constraints_midweek_file)

    @staticmethod
    def trigger_flow(master_sheet_id, app_runner):
        global MASTER_SHEET

        MASTER_SHEET = master_sheet_id
        app_runner = app_runner

        if LOAD_CONSTRAINTS_FROM_CACHE:
            logging.info("loading constraints from cache")
            weekend_constraints, employees = app_runner.load_constraints_weekend_from_cache()
        else:
            logging.info("loading weekend constraints from google sheets")
            weekend_constraints, employees = app_runner.get_employees_and_their_constraints_for_weekend()
            app_runner.cache_employee_weekend_constraints(weekend_constraints, employees)
        app_runner.run_algorithm_for_weekend(employees, weekend_constraints)
        del weekend_constraints
        gc.collect()
        if LOAD_CONSTRAINTS_FROM_CACHE:
            mid_week_constraints = app_runner.load_constraints_mid_week_from_cache()
        else:
            logging.info("loading midweek constraints from google sheets")
            mid_week_constraints, employees = app_runner.get_employees_and_their_constraints_for_midweek()
            app_runner.cache_employee_mid_week_constraints(mid_week_constraints)
        app_runner.run_algorithm_for_midweek(employees, mid_week_constraints)
        del mid_week_constraints, employees
        gc.collect()


    def kill_process_if_needed(self):
        if self.kill_process:
            raise Exception("stop for user request")
