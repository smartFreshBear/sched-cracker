from unittest import TestCase

from objects.Classes import *
from rules import Rules
from rules.Rules import *
from ..algorithm_based_priority_queue import solve_weekend, solve_mid_week
import copy


class AlgorithmTest(TestCase):

    def test_simple_flow_no_rules_only_employee1_can_not_on_sunday(self):
        employees, aviad, tania, almog, maniak, gandalf, frodo, mother_theresa = get_employess()

        board = PlanningBoard()

        aviad_cant_on_sunday_at_all = EmployeeConstraintsForWeekDays(
            employee=aviad,
            from_day_to_constraint={
                (WeekOfTheMonth.First, DaysOfWeek.Sunday): [MidWeekShiftType.All],
                (WeekOfTheMonth.Second, DaysOfWeek.Sunday): [MidWeekShiftType.All],
                (WeekOfTheMonth.Third, DaysOfWeek.Sunday): [MidWeekShiftType.All],
                (WeekOfTheMonth.Forth, DaysOfWeek.Sunday): [MidWeekShiftType.All],
                (WeekOfTheMonth.Fifth, DaysOfWeek.Sunday): [MidWeekShiftType.All]
            }
        )

        tanya_cant_do_night_shift_on_Wednesday = EmployeeConstraintsForWeekDays(
            employee=tania,
            from_day_to_constraint={
                (WeekOfTheMonth.First, DaysOfWeek.Wednesday): [MidWeekShiftType.Night],
                (WeekOfTheMonth.Second, DaysOfWeek.Wednesday): [MidWeekShiftType.Night],
                (WeekOfTheMonth.Third, DaysOfWeek.Wednesday): [MidWeekShiftType.Night],
                (WeekOfTheMonth.Forth, DaysOfWeek.Wednesday): [MidWeekShiftType.Night],
                (WeekOfTheMonth.Fifth, DaysOfWeek.Wednesday): [MidWeekShiftType.Night]
            }
        )

        solve_weekend(board, copy.deepcopy(employees), [], [], {})

        solve_mid_week(board, copy.deepcopy(employees),
                       [aviad_cant_on_sunday_at_all, tanya_cant_do_night_shift_on_Wednesday], [], {})

        lst_of_sunday_shift_employee = [list(week[0].from_shift_to_employee.values()) for week in board.midWeekMapping]

        all_sundays = [employee for sunday_shift in lst_of_sunday_shift_employee for employee in sunday_shift]

        wednesday_nights = [week[3].from_shift_to_employee[MidWeekShiftType.Night] for week in board.midWeekMapping]

        assert aviad not in all_sundays
        assert tania not in wednesday_nights

    def test_almog_not_doing_fridays_aviad_not_doing_two_first_weekends(self):
        employees, aviad, tania, almog, maniak, gandalf, frodo, mother_theresa = get_employess()
        board = PlanningBoard()

        almog_cant_do_fridays = EmployeeConstraintsForWeekends(from_weekend_to_constraints={
            WeekOfTheMonth.First: [WeekendShiftsTypes.Friday],
            WeekOfTheMonth.Second: [WeekendShiftsTypes.Friday],
            WeekOfTheMonth.Third: [WeekendShiftsTypes.Friday],
            WeekOfTheMonth.Forth: [WeekendShiftsTypes.Friday],
            WeekOfTheMonth.Fifth: [WeekendShiftsTypes.Friday]
        }, employee=almog)

        aviad_not_doing_weekends_half_of_the_month = EmployeeConstraintsForWeekends(from_weekend_to_constraints={
            WeekOfTheMonth.First: [WeekendShiftsTypes.All],
            WeekOfTheMonth.Second: [WeekendShiftsTypes.All]
        }, employee=aviad)

        solve_weekend(board=board,
                      employees=copy.deepcopy(employees),
                      weekend_demands=[almog_cant_do_fridays, aviad_not_doing_weekends_half_of_the_month],
                      rules=[],
                      priority_treatment={})

        first_two_weekend_lst_lst = [list(week.from_shift_to_employee.values()) for week in [board.weekendMapping[0],
                                                                                             board.weekendMapping[1]]]

        first_two_weekend_employees = [employee for weekend_employees_lst in first_two_weekend_lst_lst for employee in
                                       weekend_employees_lst]

        assert aviad not in first_two_weekend_employees

        all_friday_shift_employees = [weekend.from_shift_to_employee[WeekendShiftsTypes.Friday]
                                      for weekend in board.weekendMapping]

        assert almog not in all_friday_shift_employees

    def test_new_employees_can_not_be_in_same_time(self):
        employees, aviad, tania, almog, maniak, gandalf, frodo, mother_theresa = get_employess()
        board = PlanningBoard()

        solve_weekend(board=board,
                      employees=employees,
                      weekend_demands=[],
                      rules=[NoTwoNewInOneShift()],
                      priority_treatment={})

        solve_mid_week(board=board,
                       employees=employees,
                       week_days_demands=[],
                       rules=[NoTwoNewInOneShift()],
                       priority_treatment={})

        all_days = [day for week in board.midWeekMapping for day in week]
        for day in all_days:
            for shift in day.from_shift_to_employee.keys():
                overlapping = MidWeekShiftType.intersect_with(shift)
                employees_overlapping = [day.from_shift_to_employee[shift] for shift in overlapping]
                for emp in employees_overlapping:
                    assert not emp.isNew or not day.from_shift_to_employee[shift].isNew

        all_weekends = [weekend for weekend in board.weekendMapping]
        for weekend in all_weekends:
            for shift in weekend.from_shift_to_employee.keys():
                overlapping = WeekendShiftsTypes.intersect_with(shift)
                employees_overlapping = [weekend.from_shift_to_employee[shift] for shift in overlapping]
                for emp in employees_overlapping:
                    assert not emp.isNew or not weekend.from_shift_to_employee[shift].isNew

    def test_during_weekend_male_employee_cant_be_together(self):
        employees, aviad, tania, almog, maniak, gandalf, frodo, mother_theresa = get_employess()
        board = PlanningBoard()

        solve_weekend(board=board,
                      employees=employees,
                      weekend_demands=[],
                      rules=[NoTwoMaleEmployeeDuringWeekend()],
                      priority_treatment={})

        solve_mid_week(board=board,
                       employees=employees,
                       week_days_demands=[],
                       rules=[NoTwoNewInOneShift()],
                       priority_treatment={})

        all_weekends = [weekend for weekend in board.weekendMapping]
        for weekend in all_weekends:
            for shift in weekend.from_shift_to_employee.keys():
                overlapping = WeekendShiftsTypes.intersect_with(shift)
                employees_overlapping = [weekend.from_shift_to_employee[shift] for shift in overlapping]
                for emp in employees_overlapping:
                    assert emp.sex is not "male" or weekend.from_shift_to_employee[shift].sex is not "male"

    def test_if_some_one_did_weekend_he_wont_do_before_or_after(self):
        employees, aviad, tania, almog, maniak, gandalf, frodo, mother_theresa = get_employess()
        board = PlanningBoard()

        result = CantDoShiftDayAfterAndBeforeWeekend().check(aviad, board, 0, 0, MidWeekShiftType.Night)
        assert result

        board.weekendMapping[0].from_shift_to_employee[WeekendShiftsTypes.Short] = aviad
        result = CantDoShiftDayAfterAndBeforeWeekend().check(aviad, board, 1, 0, MidWeekShiftType.Night)
        assert not result

        board.weekendMapping[2].from_shift_to_employee[WeekendShiftsTypes.Long] = aviad
        result = CantDoShiftDayAfterAndBeforeWeekend().check(aviad, board, 2, 4, MidWeekShiftType.Night)
        assert not result

    def test_double_shift_extra_short(self):

        employees, aviad, tania, almog, maniak, gandalf, frodo, mother_theresa = get_employess()
        board = PlanningBoard()
        req = EmployeeDoubleShiftRequirement(
            weeks_to_ignored_rules_mappings={
                WeekOfTheMonth.First: {MidWeekShiftType.Short: [IfEmployeeDidShortHeCantDoShort.get_id(),
                                                                IfEmployeeDidLongHeCantDoShort.get_id()],
                                       MidWeekShiftType.Night: [Rules.CantWorkDayAfterNight.get_id()]
                                       }
            },
            weekend_rules_to_ignore=None)
        aviad.employee_double_request = req
        board.midWeekMapping[0][1].from_shift_to_employee[MidWeekShiftType.Short] = aviad
        result = Rules.check_for_list_of_rules(aviad, board, 0, 3, MidWeekShiftType.Short, Rules.get_all_rules())
        assert result

        aviad.employee_double_request = EmployeeDoubleShiftRequirement()
        board.midWeekMapping[0][1].from_shift_to_employee[MidWeekShiftType.Short] = aviad
        result = Rules.check_for_list_of_rules(aviad, board, 0, 3, MidWeekShiftType.Short, Rules.get_all_rules())
        assert not result

    def test_during_weekend_live_empty_in_case_no_one_can_feature(self):
        _, aviad, tania, almog, _, _, _, _ = get_employess()
        board = PlanningBoard()

        small_list = [aviad, tania, almog]

        almog_cant_do_first_weekend = EmployeeConstraintsForWeekends(from_weekend_to_constraints={
            WeekOfTheMonth.First: [WeekendShiftsTypes.All]
        }, employee=almog)

        aviad_cant_do_first_weekend = EmployeeConstraintsForWeekends(from_weekend_to_constraints={
            WeekOfTheMonth.First: [WeekendShiftsTypes.All]
        }, employee=aviad)
        tania_cant_do_first_weekend = EmployeeConstraintsForWeekends(from_weekend_to_constraints={
            WeekOfTheMonth.First: [WeekendShiftsTypes.All]
        }, employee=tania)

        aviad_cant_on_first_and_last_sunday = EmployeeConstraintsForWeekDays(
            employee=aviad,
            from_day_to_constraint={
                (WeekOfTheMonth.First, DaysOfWeek.Sunday): [MidWeekShiftType.All],
                (WeekOfTheMonth.Fifth, DaysOfWeek.Sunday): [MidWeekShiftType.All]
            }
        )

        almog_cant_on_first_and_last_sunday = EmployeeConstraintsForWeekDays(
            employee=almog,
            from_day_to_constraint={
                (WeekOfTheMonth.First, DaysOfWeek.Sunday): [MidWeekShiftType.All],
                (WeekOfTheMonth.Fifth, DaysOfWeek.Sunday): [MidWeekShiftType.All]
            }
        )

        tania_cant_on_first_and_last_sunday = EmployeeConstraintsForWeekDays(
            employee=tania,
            from_day_to_constraint={
                (WeekOfTheMonth.First, DaysOfWeek.Sunday): [MidWeekShiftType.All],
                (WeekOfTheMonth.Fifth, DaysOfWeek.Sunday): [MidWeekShiftType.All]
            }
        )

        solve_weekend(board=board,
                      employees=small_list,
                      weekend_demands=[almog_cant_do_first_weekend, aviad_cant_do_first_weekend,
                                       tania_cant_do_first_weekend],
                      should_force_shift=False,
                      rules=[],
                      priority_treatment={})

        solve_mid_week(board=board,
                       employees=small_list,
                       should_force_shift=False,
                       week_days_demands=[tania_cant_on_first_and_last_sunday, aviad_cant_on_first_and_last_sunday,
                                          almog_cant_on_first_and_last_sunday],
                       rules=[],
                       priority_treatment={})

        assert len([employee for employee in board.weekendMapping[0].from_shift_to_employee.values() if
                    employee is not None]) == 0
        assert len([employee for employee in board.midWeekMapping[0][0].from_shift_to_employee.values() if
                    employee is not None]) == 0


def get_employess():
    aviad = Employee(name="Aviad S", sex="male", new=False, priority=100)
    tania = Employee(name="Tanya V", sex="female", new=False, priority=100)
    almog = Employee(name="Almog O", sex="male", new=False, priority=99)
    maniak = Employee(name="Maniaka K", sex="female", new=False, priority=110)
    maniak2 = Employee(name="Maniak K2", sex="male", new=False, priority=103)
    gandalf = Employee(name="Gandalf G", sex="male", new=True, priority=110)
    frodo = Employee(name="Frodo B", sex="male", new=True, priority=110)
    mother_theresa = Employee(name="Mother T", sex="female", new=True, priority=110)

    return [aviad, tania, almog, maniak, gandalf, frodo,
            mother_theresa, maniak2], aviad, tania, almog, maniak, gandalf, frodo, mother_theresa
