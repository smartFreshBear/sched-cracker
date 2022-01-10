from unittest import TestCase

from objects.Classes import *
from uxui.googlesheetinterface import SpreadsheetClient
from uxui.user_data_convertor_googlesheet import UserDataConvertorGoogleSheetBased

sheet_id_for_test_employee_request = '1f705Ej9p5xnR3-eWrf44Cmqmtzgr_R-wCcuFL9uQJn8'
sheet_id_for_summary = '1JeBn8pq886KbtaQaV3B8-P7FP_ynLUhcNIUINRNdt2g'


class TestUserDataConvertorGoogleSheetBased(TestCase):

    def test_get_employee_details_from_sheet(self):
        user_data_convertor_googlesheet = UserDataConvertorGoogleSheetBased(SpreadsheetClient(sheet_id_for_test_employee_request))
        details = user_data_convertor_googlesheet.get_employee_details()
        assert details.name == 'Aviad'
        assert details.isNew == False
        assert details.sex == 'male'

    def test_get_constraints_for_user_given_mid_week(self):
        user_data_convertor_googlesheet = UserDataConvertorGoogleSheetBased(SpreadsheetClient(sheet_id_for_test_employee_request))
        constraints_of_aviad = user_data_convertor_googlesheet.get_constraint_for_midweek(WeekOfTheMonth.Forth)
        sunday_constraints = constraints_of_aviad.from_day_to_constraint[(WeekOfTheMonth.Forth, DaysOfWeek.Sunday)]
        thu_constraints = constraints_of_aviad.from_day_to_constraint[(WeekOfTheMonth.Forth, DaysOfWeek.Thursday)]

        assert MidWeekShiftType.Short in sunday_constraints

        tuesday_constraints = constraints_of_aviad.from_day_to_constraint[(WeekOfTheMonth.Forth, DaysOfWeek.Tuesday)]
        assert MidWeekShiftType.Long in tuesday_constraints
        assert MidWeekShiftType.Night in tuesday_constraints
        assert MidWeekShiftType.Night in thu_constraints

    def test_get_constraints_for_user_given_weekend(self):
        user_data_convertor_googlesheet = UserDataConvertorGoogleSheetBased(SpreadsheetClient(sheet_id_for_test_employee_request))
        employee_constraints = user_data_convertor_googlesheet.get_constraint_for_weekend(WeekOfTheMonth.First)
        constraints = employee_constraints.from_day_to_constraint[WeekOfTheMonth.First]
        assert WeekendShiftsTypes.Short in constraints

        employee_constraints = user_data_convertor_googlesheet.get_constraint_for_weekend(WeekOfTheMonth.Fifth)
        constraints = employee_constraints.from_day_to_constraint[WeekOfTheMonth.Fifth]
        assert WeekendShiftsTypes.Short not in constraints
        assert WeekendShiftsTypes.Friday in constraints
        assert WeekendShiftsTypes.Saturday in constraints

    def test_write_midweek(self):
        user_data_convertor_googlesheet = UserDataConvertorGoogleSheetBased(SpreadsheetClient(sheet_id_for_summary))
        board = PlanningBoard()
        board.midWeekMapping[0][0].from_shift_to_employee[MidWeekShiftType.Short] = Employee('Aviad', 'male')
        board.midWeekMapping[0][1].from_shift_to_employee[MidWeekShiftType.Short] = Employee('Duba', 'female')
        board.midWeekMapping[0][2].from_shift_to_employee[MidWeekShiftType.Short] = Employee('Duba', 'female')
        board.midWeekMapping[0][3].from_shift_to_employee[MidWeekShiftType.Short] = Employee('Aviad', 'male')
        board.midWeekMapping[0][4].from_shift_to_employee[MidWeekShiftType.Short] = Employee('Duba', 'female')
        board.midWeekMapping[0][0].from_shift_to_employee[MidWeekShiftType.Night] = Employee('Aviad', 'male')
        board.midWeekMapping[0][1].from_shift_to_employee[MidWeekShiftType.Night] = Employee('Duba', 'female')
        board.midWeekMapping[0][2].from_shift_to_employee[MidWeekShiftType.Night] = Employee('Aviad', 'male')
        board.midWeekMapping[0][3].from_shift_to_employee[MidWeekShiftType.Night] = Employee('Duba', 'female')
        board.midWeekMapping[0][4].from_shift_to_employee[MidWeekShiftType.Night] = Employee('Aviad', 'male')

        user_data_convertor_googlesheet.write_mid_week(WeekOfTheMonth.First, board)

        result = user_data_convertor_googlesheet.googleclient.load_cells_given_from_to('E8', 'I10')
        assert result[0][0].text == 'Aviad'
        assert result[0][1].text == 'Duba'

        user_data_convertor_googlesheet = UserDataConvertorGoogleSheetBased(SpreadsheetClient(sheet_id_for_summary))

        board.midWeekMapping[4][0].from_shift_to_employee[MidWeekShiftType.Short] = Employee('Aviad', 'male')
        board.midWeekMapping[4][1].from_shift_to_employee[MidWeekShiftType.Short] = Employee('Duba', 'female')
        board.midWeekMapping[4][2].from_shift_to_employee[MidWeekShiftType.Short] = Employee('Duba', 'female')
        board.midWeekMapping[4][3].from_shift_to_employee[MidWeekShiftType.Short] = Employee('Aviad', 'male')
        board.midWeekMapping[4][4].from_shift_to_employee[MidWeekShiftType.Short] = Employee('Duba', 'female')
        board.midWeekMapping[4][0].from_shift_to_employee[MidWeekShiftType.Night] = Employee('Aviad', 'male')
        board.midWeekMapping[4][1].from_shift_to_employee[MidWeekShiftType.Night] = Employee('Duba', 'female')
        board.midWeekMapping[4][2].from_shift_to_employee[MidWeekShiftType.Night] = Employee('Aviad', 'male')
        board.midWeekMapping[4][3].from_shift_to_employee[MidWeekShiftType.Night] = Employee('Duba', 'female')
        board.midWeekMapping[4][4].from_shift_to_employee[MidWeekShiftType.Night] = Employee('Aviad', 'male')

        user_data_convertor_googlesheet.write_mid_week(WeekOfTheMonth.Fifth, board)
        result = user_data_convertor_googlesheet.googleclient.load_cells_given_from_to('E28', 'I30')
        assert result[0][0].text == 'Aviad'
        assert result[0][1].text == 'Duba'




    def test_get_mid_week_double_shift(self):
        user_data_convertor_googlesheet = UserDataConvertorGoogleSheetBased(SpreadsheetClient(sheet_id_for_test_employee_request))
        list_of_double_shift_request = user_data_convertor_googlesheet.get_double_shift_for_employee_mid_week()
        assert list_of_double_shift_request[1][0].text == 'True'
        assert list_of_double_shift_request[2][0].text == 'False'
        print(list_of_double_shift_request)

    def test_get_weekend_double_shift(self):
        user_data_convertor_googlesheet = UserDataConvertorGoogleSheetBased(SpreadsheetClient(sheet_id_for_test_employee_request))
        list_of_double_shift_request = user_data_convertor_googlesheet.get_double_shift_for_employee_weekend()

        assert list_of_double_shift_request[0][0].text == 'True'
        assert list_of_double_shift_request[1][0].text == 'False'
        assert list_of_double_shift_request[2][0].text == 'True'
        assert list_of_double_shift_request[3][0].text == 'False'
        print(list_of_double_shift_request)


    def test_get_employee_with_rules_override(self):
        user_data_convertor_googlesheet = UserDataConvertorGoogleSheetBased(SpreadsheetClient(sheet_id_for_test_employee_request))
        employee = user_data_convertor_googlesheet.get_employee_details()

        assert employee.employee_double_request is not None
        assert len(employee.employee_double_request.mid_weeks_to_rules_mappings[0][0]) > 0
        assert len(employee.employee_double_request.mid_weeks_to_rules_mappings[0][2]) > 0
        assert len(employee.employee_double_request.mid_weeks_to_rules_mappings[3][1]) > 0
        assert len(employee.employee_double_request.weekend_rules_to_ignore) > 0





