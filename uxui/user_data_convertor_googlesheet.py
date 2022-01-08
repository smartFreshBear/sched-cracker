from rules.Rules import from_double_shift_request_to_list_of_rules
from objects.Classes import WeekOfTheMonth, DaysOfWeek, EmployeeConstraintsForWeekDays, \
    MidWeekShiftType, EmployeeConstraintsForWeekends, WeekendShiftsTypes, PlanningBoard, Employee, \
    EmployeeDoubleShiftRequirement

from uxui.uiobjects.Cell import Cell

NAME_LOCATION_FROM = 'A8'
NAME_LOCATION_TO = 'B10'
RED_CELL = 'J5'
DOUBLE_SHIFT_MID_WEEK_RANGE = 'J7:K31'


class UserDataConvertorGoogleSheetBased:

    def __init__(self, googleclient):
        self.googleclient = googleclient

    @staticmethod
    def get_from_cell_midweek_number_given_week(week):
        return 'E' + str(8 + (week.value * 5))

    @staticmethod
    def get_to_midweek_cell_number_given_week(week):
        return 'I' + str(10 + (week.value * 5))

    @staticmethod
    def get_weekend_cells_given_week(week):
        off_set = week
        return \
            {
                WeekendShiftsTypes.Short: 'N{0}:Q{0}'.format(str(off_set * 5 + 8)),
                WeekendShiftsTypes.Long: 'N{0}:O{0}'.format(str(off_set * 5 + 9)),
                WeekendShiftsTypes.Friday: 'P{0}:P{0}'.format(str(off_set * 5 + 10)),
                WeekendShiftsTypes.Saturday: 'Q{0}:R{0}'.format(str(off_set * 5 + 11))
            }

    def get_constraint_for_midweek(self, week: WeekOfTheMonth,
                                   employee_constraints: EmployeeConstraintsForWeekDays = None):
        if employee_constraints is None:
            employee_details = self.get_employee_details()
            employee_constraints = EmployeeConstraintsForWeekDays(employee=employee_details,
                                                                  from_day_to_constraint={})

        to_cell = self.get_to_midweek_cell_number_given_week(week)
        from_cell = self.get_from_cell_midweek_number_given_week(week)
        cell_rows = self.googleclient.load_cells_given_from_to(from_cell, to_cell)
        for day in range(len(DaysOfWeek)):
            for shift in range(len(MidWeekShiftType) - 1):
                if self.is_red_cell(cell_rows[shift][day]):
                    self.handle_constraints(day, employee_constraints, shift, week)
        return employee_constraints

    def write_mid_week(self, week: WeekOfTheMonth, board: PlanningBoard):

        to_cell = self.get_to_midweek_cell_number_given_week(week)
        from_cell = self.get_from_cell_midweek_number_given_week(week)
        days_of_week = board.midWeekMapping[week.value]

        table_to_write = []
        for shift in MidWeekShiftType.get_literally_all():
            new_row = []
            for day in range(len(DaysOfWeek)):
                employee_in_shift = days_of_week[day].from_shift_to_employee[shift]
                new_row.append(Cell() if employee_in_shift is None else Cell(text=employee_in_shift.name))
            table_to_write.append(new_row)

        self.googleclient.update_cells_given_from_to_and_cells(from_cell, to_cell, table_to_write)
        return True

    def get_constraint_for_weekend(self, week: WeekOfTheMonth,
                                   employee_constraints: EmployeeConstraintsForWeekends = None):
        if employee_constraints is None:
            employee_details = self.get_employee_details()
            employee_constraints = EmployeeConstraintsForWeekends(employee=employee_details,
                                                                  from_weekend_to_constraints={})

        from_weekend_to_relevant_cells = self.get_weekend_cells_given_week(week)

        for key, value in from_weekend_to_relevant_cells.items():
            weekend_cell = self.googleclient.load_cells_given_pair(value)[0][0]
            if self.is_red_cell(weekend_cell):
                if week not in employee_constraints.from_day_to_constraint:
                    employee_constraints.from_day_to_constraint[week] = []
                employee_constraints.from_day_to_constraint[week].append(key)

        return employee_constraints

    def write_weekend(self, week: WeekOfTheMonth, board: PlanningBoard):

        week_zero_based_value = week.value - 1
        weekend_shift = board.weekendMapping[week_zero_based_value]
        from_weekend_to_relevant_cells = self.get_weekend_cells_given_week(week)

        for key, value in from_weekend_to_relevant_cells.items():
            employee_in_shift = weekend_shift.from_shift_to_employee[key]
            cell_to_write = Cell() if employee_in_shift is None else Cell(text=employee_in_shift.name)

            self.googleclient.update_cells_given_from_to_and_cells(value.split(':')[0], value.split(':')[1],
                                                                   [[cell_to_write]])

        return True

    @staticmethod
    def is_red_cell(cell):
        return cell.text.lower() == 'true'

    @staticmethod
    def handle_constraints(day, employee_constraints, shift, week):
        hashing = (week, DaysOfWeek.from_int_to_day_zero_based(day))
        if hashing not in employee_constraints.from_day_to_constraint:
            employee_constraints.from_day_to_constraint[hashing] = []
        employee_constraints.from_day_to_constraint[hashing].append(MidWeekShiftType(shift))

    def get_employee_details(self):
        employee_double_shift_req = EmployeeDoubleShiftRequirement()
        self.handle_mid_week_double_shift(employee_double_shift_req)

        table = self.googleclient.load_cells_given_from_to(NAME_LOCATION_FROM, NAME_LOCATION_TO)

        employee = Employee(sex=table[2][1].text,
                            name=table[0][1].text,
                            new=table[1][1].text.lower() == 'yes',
                            mid_week_rule_override=employee_double_shift_req)
        if not employee.name:
            raise Exception("you cant provide empty name in id {}".format(self.googleclient.sheet_id))

        if not employee.sex:
            raise Exception("you cant provide empty sex in sheet id {}".format(self.googleclient.sheet_id))
        return employee

    def handle_mid_week_double_shift(self, employee_double_shift_req):

        week_rows_amount_in_ui = len(MidWeekShiftType.get_literally_all()) + 2
        for week_index, double_for_week in enumerate(self.batchify(self.get_double_shift_for_employee(),
                                                                   week_rows_amount_in_ui)):
            for shift_index, double_shift_cells in enumerate(double_for_week[1:4]):
                if double_shift_cells[0].text == 'True':
                    if week_index not in employee_double_shift_req.weeks_to_rules_mappings:
                        employee_double_shift_req.weeks_to_rules_mappings[week_index] = {}
                    employee_double_shift_req.weeks_to_rules_mappings[week_index][shift_index] = \
                        from_double_shift_request_to_list_of_rules[MidWeekShiftType(shift_index)]

    def get_double_shift_for_employee(self):
        return self.googleclient.load_cells_given_pair(DOUBLE_SHIFT_MID_WEEK_RANGE)

    @staticmethod
    def batchify(iterable, batch_size=1):
        length_of_iterable = len(iterable)
        for ndx in range(0, length_of_iterable, batch_size):
            yield iterable[ndx:ndx + batch_size]
