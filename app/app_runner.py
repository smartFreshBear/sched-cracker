import pickle
import random
import sys
import time

from algorithem import algorithm_based_priority_queue
from algorithem.algorithm_based_priority_queue import *
from algorithem.board_weighter import board_weighter
from rules.Rules import *
from uxui.googlesheetinterface import SpreadsheetClient
from uxui.user_data_convertor_googlesheet import UserDataConvertorGoogleSheetBased

load_from_cache = False


class AppRunner:

    def __init__(self):
        self.board = PlanningBoard()

    @staticmethod
    def get_all_employee_ids():
        master_sheet_client = SpreadsheetClient(MASTER_SHEET)
        employees_sheet_ids = master_sheet_client.load_cells_given_from_to('B2', 'B100')
        return [cell.text for single_row in employees_sheet_ids for cell in single_row if cell.text != '']

    @staticmethod
    def get_result_sheet():
        master_sheet_client = SpreadsheetClient(MASTER_SHEET)
        result_table = master_sheet_client.load_constraints_given_pair('E1:E1')
        return result_table[0][0].text

    def get_employees_and_their_constraints_for_weekend(self):
        constraints = []
        employees = []
        for sheet_id in self.get_all_employee_ids():
            data_convertor = UserDataConvertorGoogleSheetBased(SpreadsheetClient(sheet_id))
            employee = data_convertor.get_employee_details()
            employees.append(employee)
            weekend_constraints = EmployeeConstraintsForWeekends(from_weekend_to_constraints={}, employee=employee)
            for weekend in WeekOfTheMonth:
                # need to enforce less calling to api
                print("weekend-flow: getting constraints for employee {} week {}".format(employee.name, weekend))
                time.sleep(3)
                data_convertor.get_constraint_for_weekend(weekend, weekend_constraints)
            constraints.append(weekend_constraints)
            time.sleep(4)
        return constraints, employees

    def get_employees_and_their_constraints_for_midweek(self):
        constraints = []
        employees = []
        for sheet_id in self.get_all_employee_ids():
            data_convertor = UserDataConvertorGoogleSheetBased(SpreadsheetClient(sheet_id))
            employee = data_convertor.get_employee_details()
            employees.append(employee)
            midweek_constraints = EmployeeConstraintsForWeekDays(from_day_to_constraint={}, employee=employee)
            for week in WeekOfTheMonth:
                # need to enforce less calls to api
                print("mid-week-flow: getting constraints for employee {} week {}".format(employee.name, week))
                time.sleep(3)
                data_convertor.get_constraint_for_midweek(week, midweek_constraints)
            constraints.append(midweek_constraints)
            time.sleep(4)
        return constraints, employees

    def get_all_rules(self):
        # TODO later on should be more sophisticated
        return Rules.get_all_rules()


    def get_result_sheet_convertor(self):
        result_sheet_id = self.get_result_sheet()
        convertor = UserDataConvertorGoogleSheetBased(SpreadsheetClient(result_sheet_id))
        return convertor

    def run_algorithm_for_weekend(self, employees, constraints):
        weight = 99999
        chosen_board = self.board
        for i in range(6000):
            if weight == 0:
                break
            board_for_test = copy.deepcopy(self.board)
            # employees.insert(0, employees.pop())
            random.shuffle(employees)
            random.shuffle(constraints)
            employee_fresh = copy.deepcopy(employees)

            algorithm_based_priority_queue.solve_weekend(board_for_test, employee_fresh, constraints, False,
                                                         self.get_all_rules())
            new_weight = board_weighter.weight_weekend(board_for_test)
            if new_weight < weight:
                weight = new_weight
                chosen_board = board_for_test

        self.board = chosen_board

        convertor = self.get_result_sheet_convertor()
        for weekend in WeekOfTheMonth:
            convertor.write_weekend(weekend, self.board)

    def run_algorithm_for_midweek(self, employees, constraints):
        weight = 99999
        chosen_board = self.board
        for i in range(4000):
            if weight == 0:
                break

            board_for_test = copy.deepcopy(self.board)
            # employees.insert(0, employees.pop())
            random.shuffle(employees)
            random.shuffle(employees)
            random.shuffle(constraints)
            employee_fresh = copy.deepcopy(employees)
            algorithm_based_priority_queue.solve_mid_week(board_for_test, employee_fresh, constraints, False,
                                                          self.get_all_rules())

            new_weight = board_weighter.weight_midweek(board_for_test)
            if new_weight < weight:
                weight = new_weight
                chosen_board = board_for_test

        self.board = chosen_board
        convertor = self.get_result_sheet_convertor()
        for week in WeekOfTheMonth:
            convertor.write_mid_week(week, self.board)

    def load_constraints_weekend_from_cache(self):
        with open('constraints_employees_file', 'rb') as constraints_employees_file:
            constraints_cached, employees_cached = pickle.load(constraints_employees_file)
            return constraints_cached, employees_cached

    def cache_employee_weekend_constraints(self, constraints_to_cache, employees_to_cache):
        with open('constraints_employees_file', 'wb') as constraints_employees_file:
            pickle.dump((constraints_to_cache, employees_to_cache), constraints_employees_file)

    def load_constraints_mid_week_from_cache(self):
        with open('constraints_midweek_file', 'rb') as constraints_midweek_file:
            midweek_constrains = pickle.load(constraints_midweek_file)
            return midweek_constrains

    def cache_employee_mid_week_constraints(self, constraints_to_cache):
        with open('constraints_midweek_file', 'wb') as constraints_midweek_file:
            pickle.dump(constraints_to_cache, constraints_midweek_file)


def main(argv):

    global MASTER_SHEET

    MASTER_SHEET = argv[0]

    app_runner = AppRunner()
    if load_from_cache:
        weekend_constraints, employees = app_runner.load_constraints_weekend_from_cache()
    else:
        weekend_constraints, employees = app_runner.get_employees_and_their_constraints_for_weekend()
        app_runner.cache_employee_weekend_constraints(weekend_constraints, employees)
    app_runner.run_algorithm_for_weekend(employees, weekend_constraints)

    if load_from_cache:
        mid_week_constraints = app_runner.load_constraints_mid_week_from_cache()
    else:
        mid_week_constraints, employees = app_runner.get_employees_and_their_constraints_for_midweek()
        app_runner.cache_employee_mid_week_constraints(mid_week_constraints)
    app_runner.run_algorithm_for_midweek(employees, mid_week_constraints)


if __name__ == "__main__":
    main(sys.argv[1:])
