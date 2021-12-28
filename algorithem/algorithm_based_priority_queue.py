import copy
import heapq
import random

from objects.Classes import *
from rules import Rules

from_shift_to_weight = {
    MidWeekShiftType.Short: 50,
    MidWeekShiftType.Night: 50,
    MidWeekShiftType.Long: 100
}


def get_relevant_employees_for_weekend_shift(weekend_index, employees, weekend_constraints, shift):
    random.shuffle(weekend_constraints)
    least_prioritised_employees = [weekend_constraint.employee for weekend_constraint in weekend_constraints if
                                   shift in weekend_constraint.get_constraints_for_shift(weekend_index)]
    return [employee for employee in employees if employee not in least_prioritised_employees]


def get_relevant_employees_for_mid_week_shift(week_index, day_index, employees, midweek_demands, shift):
    random.shuffle(midweek_demands)
    least_prioritised_employees_names = [midweek_constraint.employee for midweek_constraint in midweek_demands if
                                         shift in midweek_constraint.get_constraints_for_shift(week_index, day_index)]

    relevant_employee = [employee for employee in employees if (employee not in least_prioritised_employees_names)]

    return relevant_employee


def does_all_rule_applied(rules, employee, board, week, day, shift) -> bool:
    return Rules.check_for_list_of_rules(employee, board, week, day, shift, rules)



# try to merge the two functions
def solve_weekend(board: PlanningBoard,
                  employees: list[Employee],
                  weekend_demands: list[EmployeeConstraintsForWeekends],
                  should_force_shift: bool = True,
                  rules=None,
                  priority_treatment={}):
    if rules is None:
        rules = []
    week_index = 0

    for weekend in board.weekendMapping:

        print("extracting relevant people for {} weekend".format(week_index))

        employee_temp = copy.deepcopy(employees)
        for shift in WeekendShiftsTypes.get_literally_all():
            employees_for_week_i_shift = get_relevant_employees_for_weekend_shift(week_index, employee_temp,
                                                                                  weekend_demands, shift)
            # u already calculate rest of employee! above!

            rest_of_employees = [employee for employee in employee_temp if
                                 employee not in employees_for_week_i_shift]

            if should_force_shift:
                add_reduced_priority_employees(employees_for_week_i_shift, rest_of_employees)

            employee_candidate = get_first_prioritized_valid_employee(board, employees_for_week_i_shift,
                                                                      rules, week_index, None, shift)
            if employee_candidate is not None:

                weekend.from_shift_to_employee[shift] = employee_candidate

                employee_temp.remove(employee_candidate)

                # reduce availability for next allocation
                [employee for employee in employees if employee.name == employee_candidate.name].pop().priority -= 1

                print("employ {} successfully got allocated to weekend {} shift {}".format(employee_candidate.name,
                                                                                           week_index, shift))
            else:
                print(
                    "can not found any allocation for week {} shift {}".format(week_index, shift))

        week_index += 1


def add_reduced_priority_employees(employees_for_week_i_shift, rest_of_employees):
    reduce_likelyness_of_choice(rest_of_employees)
    employees_for_week_i_shift.extend(rest_of_employees)


def solve_mid_week(board: PlanningBoard,
                   employees: list[Employee],
                   week_days_demands: list[EmployeeConstraintsForWeekDays],
                   should_force_shift: bool = True,
                   rules: list[Rule] = None,
                   priority_treatment=None):
    week_index = 0

    for days_in_week in board.midWeekMapping:

        print("extracting relevant employees for mid week {}".format(week_index))

        for day_index, day in enumerate(days_in_week):
            employee_temp = copy.deepcopy(employees)
            for shift in MidWeekShiftType.get_literally_all():
                employees_for_week_i_shift = get_relevant_employees_for_mid_week_shift(week_index, day_index,
                                                                                       employee_temp,
                                                                                       week_days_demands, shift)
                rest_of_employees = [employee for employee in employee_temp if
                                     employee not in employees_for_week_i_shift]

                if should_force_shift:
                    add_reduced_priority_employees(employees_for_week_i_shift, rest_of_employees)
                # put re-arrange

                employee_candidate = get_first_prioritized_valid_employee(board, employees_for_week_i_shift,
                                                                          rules, week_index, day_index, shift)

                if employee_candidate is not None:
                    # allocate shift to worker
                    day.from_shift_to_employee[shift] = employee_candidate
                    # remove from day so it wont be allocated in other shift
                    employee_temp.remove(employee_candidate)
                    # reduce availability for next allocation
                    [employee for employee in employees if employee.name == employee_candidate.name].pop().priority -= from_shift_to_weight[shift]

                    print(
                        "employ {} successfully got allocated to week {} day {} shift {}".format(employee_candidate.name,
                                                                                                 week_index, day_index,
                                                                                                 shift))
                else:
                    print(
                        "can not found any allocation for week {} day {} shift {}".format(week_index, day_index, shift))

        week_index += 1


def get_first_prioritized_valid_employee(board, employees_for_week_i_shift, rules, week, day, shift):
    random.shuffle(employees_for_week_i_shift)
    heapq.heapify(employees_for_week_i_shift)
    employee_candidate = None
    while not does_all_rule_applied(rules, employee_candidate, board, week, day, shift):
        if len(employees_for_week_i_shift) == 0:
            return None
        employee_candidate = heapq.heappop(employees_for_week_i_shift)
    return employee_candidate


def reduce_likelyness_of_choice(rest_of_employees):
    for employee in rest_of_employees:
        employee.priority -= 20
