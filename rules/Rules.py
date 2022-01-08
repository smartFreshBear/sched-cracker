from functools import reduce

from objects.Classes import Rule, DaysOfWeek, WeekendShiftsTypes, MidWeekShiftType


def get_overlapping_employees_with_shift(board, week, day, shift):
    intersected_shifts = shift.intersect_with(shift)
    dic = board.get_entity(week, day).from_shift_to_employee
    intersected_employees = [dic.get(key) for key in intersected_shifts]
    return intersected_employees


class NoTwoNewInOneShift(Rule):

    @staticmethod
    def get_id():
        return 1

    def check(self, employee, board, week=None, day=None, shift=None):

        if not employee.isNew:
            return True
        else:
            overlap_employees = get_overlapping_employees_with_shift(board, week, day, shift)

            new_employees_other_then_current = [employee for employee in overlap_employees
                                                if (employee is not None) and employee.isNew]

            return len(new_employees_other_then_current) == 0


class NoTwoMaleEmployeeDuringWeekend(Rule):

    @staticmethod
    def get_id():
        return 2

    @staticmethod
    def overlapping_employee_are_male(board, week, shift):
        return len([employee for employee in
                    get_overlapping_employees_with_shift(board, week, None, shift)
                    if employee is not None and employee.sex == "male"]) > 0

    def check(self, employee, board, week=None, day=None, shift=None):

        if employee.sex == 'male' and day is None and self.overlapping_employee_are_male(board, week, shift):
            return False
        else:
            return True


class CantDoShiftDayAfterAndBeforeWeekend(Rule):

    @staticmethod
    def get_id():
        return 3

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is None:
            return True

        day_from_enum = DaysOfWeek.from_int_to_day_zero_based(day)
        if not (day_from_enum is DaysOfWeek.Sunday or day_from_enum is DaysOfWeek.Thursday):
            return True  # ONLY RELEVANT FOR THIS DAYS!

        if day_from_enum is DaysOfWeek.Thursday:
            return employee not in [board.weekendMapping[week].from_shift_to_employee[WeekendShiftsTypes.Short],
                                    board.weekendMapping[week].from_shift_to_employee[WeekendShiftsTypes.Long]]

        if day_from_enum is DaysOfWeek.Sunday:
            if week == 0:
                # need to be discussed
                return True
            else:
                return employee not in [board.weekendMapping[week - 1].from_shift_to_employee[WeekendShiftsTypes.Short],
                                        board.weekendMapping[week - 1].from_shift_to_employee[WeekendShiftsTypes.Long]]
        else:
            return True


class CantWorkDayAfterNight(Rule):

    @staticmethod
    def get_id():
        return 4

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is None or day == 0 and week == 0:
            return True

        if day == 0 and week > 0:
            return employee not in \
                   [board.weekendMapping[week].from_shift_to_employee[WeekendShiftsTypes.Saturday],
                    board.weekendMapping[week].from_shift_to_employee[WeekendShiftsTypes.Long],
                    board.weekendMapping[week].from_shift_to_employee[WeekendShiftsTypes.Short]]
        else:
            return employee != board.midWeekMapping[week][day - 1].from_shift_to_employee[MidWeekShiftType.Night]


def get_all_employees_for_shift_in_for_previous_days(board, week=None, day=None, shift=None):
    if day == 0:
        return []
    all_days_before = board.midWeekMapping[week][0: day]
    all_employee_for_shift_in_previous_days = [day.from_shift_to_employee[shift] for day in all_days_before]
    return all_employee_for_shift_in_previous_days


def get_all_employees_for_shift_in_for_previous_weekends(board, week=None, day=None, shift=None):
    if week == 0:
        return []
    all_weekends_before = board.weekendMapping[0: week]
    all_employee_for_shift_in_previous_weekends = [weekend.from_shift_to_employee[shift] for weekend in
                                                   all_weekends_before]
    return all_employee_for_shift_in_previous_weekends


class IfEmployeeDidShortHeCantDoShort(Rule):

    @staticmethod
    def get_id():
        return 5

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is None:
            return True

        elif shift == MidWeekShiftType.Short:
            return employee not in get_all_employees_for_shift_in_for_previous_days(board, week, day,
                                                                                    MidWeekShiftType.Short)
        else:
            return True


class IfEmployeeDidLongHeCantDoShort(Rule):

    @staticmethod
    def get_id():
        return 6

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is None:
            return True

        elif shift == MidWeekShiftType.Short:
            return employee not in get_all_employees_for_shift_in_for_previous_days(board, week, day,
                                                                                    MidWeekShiftType.Long)
        else:
            return True


class IfEmployeeDidLongHeCantLong(Rule):

    @staticmethod
    def get_id():
        return 7

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is None:
            return True
        elif shift == MidWeekShiftType.Long:
            return employee not in get_all_employees_for_shift_in_for_previous_days(board, week, day,
                                                                                    MidWeekShiftType.Long)
        else:
            return True


class IfEmployeeDidLongHeCantNight(Rule):

    @staticmethod
    def get_id():
        return 8

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is None:
            return True

        elif shift == MidWeekShiftType.Night:
            return employee not in get_all_employees_for_shift_in_for_previous_days(board, week, day,
                                                                                    MidWeekShiftType.Long)
        else:
            return True


class IfEmployeeDidNightHeCantDoMoreNight(Rule):

    @staticmethod
    def get_id():
        return 9

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is None:
            return True

        elif shift == MidWeekShiftType.Night:
            return employee not in get_all_employees_for_shift_in_for_previous_days(board, week, day,
                                                                                    MidWeekShiftType.Night)
        else:
            return True


class IfEmployeeDidNightHeCantDoLong(Rule):

    @staticmethod
    def get_id():
        return 10

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is None:
            return True

        elif shift == MidWeekShiftType.Long:
            return employee not in get_all_employees_for_shift_in_for_previous_days(board, week, day,
                                                                                    MidWeekShiftType.Night)
        else:
            return True


class IfEmployeeDidShortInWeekendHeWontDoAnother(Rule):

    @staticmethod
    def get_id():
        return 11

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is not None:
            return True
        elif shift == WeekendShiftsTypes.Short:
            employees_that_did_shorts = get_all_employees_for_shift_in_for_previous_weekends(board, week, day,
                                                                                             WeekendShiftsTypes.Short)
            return employee not in employees_that_did_shorts
        else:
            return True


class IfEmployeeDidShortInWeekendHeWontDoLong(Rule):
    @staticmethod
    def get_id():
        return 12

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is not None:
            return True
        elif shift == WeekendShiftsTypes.Long:
            employees_that_did_shorts = get_all_employees_for_shift_in_for_previous_weekends(board, week, day,
                                                                                             WeekendShiftsTypes.Short)
            return employee not in employees_that_did_shorts
        else:
            return True


class IfEmployeeDidLongInWeekendHeWontDoShort(Rule):
    @staticmethod
    def get_id():
        return 13

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is not None:
            return True
        elif shift == WeekendShiftsTypes.Short:
            employees_that_did_shorts = get_all_employees_for_shift_in_for_previous_weekends(board, week, day,
                                                                                             WeekendShiftsTypes.Long)
            return employee not in employees_that_did_shorts
        else:
            return True


class IfEmployeeDidLongInWeekendHeWontDoAnother(Rule):
    @staticmethod
    def get_id():
        return 14

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is not None:
            return True
        elif shift == WeekendShiftsTypes.Long:
            employees_that_did_shorts = get_all_employees_for_shift_in_for_previous_weekends(board, week, day,
                                                                                             WeekendShiftsTypes.Long)
            return employee not in employees_that_did_shorts
        else:
            return True

class IfEmployeeDidFridayInWeekendHeWontDoFriday(Rule):
    @staticmethod
    def get_id():
        return 15

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is not None:
            return True
        elif shift == WeekendShiftsTypes.Friday:
            employees_that_did_fridays = get_all_employees_for_shift_in_for_previous_weekends(board, week, day,
                                                                                              WeekendShiftsTypes.Friday)
            return employee not in employees_that_did_fridays
        else:
            return True


class IfEmployeeDidFridayInWeekendHeWontDoSat(Rule):
    @staticmethod
    def get_id():
        return 16

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is not None:
            return True
        elif shift == WeekendShiftsTypes.Saturday:
            employees_that_did_fridays = get_all_employees_for_shift_in_for_previous_weekends(board, week, day,
                                                                                              WeekendShiftsTypes.Friday)
            return employee not in employees_that_did_fridays
        else:
            return True


class IfEmployeeDidSatInWeekendHeWontDoAnother(Rule):
    @staticmethod
    def get_id():
        return 17

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is not None:
            return True
        elif shift == WeekendShiftsTypes.Saturday:
            employees_that_did_sat = get_all_employees_for_shift_in_for_previous_weekends(board, week, day,
                                                                                          WeekendShiftsTypes.Saturday)
            return employee not in employees_that_did_sat
        else:
            return True


class IfEmployeeDidSatInWeekendHeWontDoFriday(Rule):
    @staticmethod
    def get_id():
        return 18

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is not None:
            return True
        elif shift == WeekendShiftsTypes.Friday:
            employees_that_did_sat = get_all_employees_for_shift_in_for_previous_weekends(board, week, day,
                                                                                          WeekendShiftsTypes.Saturday)
            return employee not in employees_that_did_sat
        else:
            return True


def check_for_list_of_rules(employee, board, week=None, day=None, shift=None, list_of_rules=None):
    if employee is None:
        return False

    rules_to_override_mappings = employee.mid_week_rule_override.mid_weeks_to_rules_mappings

    list_of_rules_id_list = [rule_id for rule_id in rules_to_override_mappings.get(week, {}).values()] \
        if rules_to_override_mappings is not None else []
    list_of_rules_id_list.extend(employee.weekend_rules_to_ignore)

    all_rules_id_to_ignore = [rule_id for list_of_rules in list_of_rules_id_list for rule_id in list_of_rules]

    filtered_rules = [rule for rule in list_of_rules if rule.get_id() not in all_rules_id_to_ignore]
    all_rules_are_valid = reduce(lambda a, b: a and b, [rule.check(employee, board, week, day, shift) for
                                                        rule in filtered_rules], True)
    return all_rules_are_valid


def get_all_rules():
    return [
        CantDoShiftDayAfterAndBeforeWeekend(),
        NoTwoMaleEmployeeDuringWeekend(),
        NoTwoNewInOneShift(),
        CantWorkDayAfterNight(),
        IfEmployeeDidShortHeCantDoShort(),
        IfEmployeeDidLongHeCantDoShort(),
        IfEmployeeDidLongHeCantLong(),
        IfEmployeeDidLongHeCantNight(),
        IfEmployeeDidNightHeCantDoMoreNight(),
        IfEmployeeDidNightHeCantDoLong(),
        IfEmployeeDidShortInWeekendHeWontDoAnother(),
        IfEmployeeDidShortInWeekendHeWontDoLong(),
        IfEmployeeDidLongInWeekendHeWontDoShort(),
        IfEmployeeDidLongInWeekendHeWontDoAnother(),
        IfEmployeeDidFridayInWeekendHeWontDoFriday(),
        IfEmployeeDidFridayInWeekendHeWontDoSat(),
        IfEmployeeDidSatInWeekendHeWontDoAnother(),
        IfEmployeeDidSatInWeekendHeWontDoFriday()
    ]


from_double_shift_request_to_list_of_rules = {
    MidWeekShiftType.Short: [IfEmployeeDidShortHeCantDoShort.get_id(), IfEmployeeDidLongHeCantDoShort.get_id()],
    MidWeekShiftType.Long: [IfEmployeeDidLongHeCantLong.get_id(), IfEmployeeDidNightHeCantDoLong.get_id()],
    MidWeekShiftType.Night: [IfEmployeeDidLongHeCantNight.get_id(), IfEmployeeDidNightHeCantDoMoreNight.get_id()]

}

from_double_shift_weekend_to_list_of_canceled_rules = {
    WeekendShiftsTypes.Short: [IfEmployeeDidShortInWeekendHeWontDoAnother.get_id(), IfEmployeeDidLongInWeekendHeWontDoShort.get_id()],
    WeekendShiftsTypes.Long: [IfEmployeeDidShortInWeekendHeWontDoLong.get_id(), IfEmployeeDidLongInWeekendHeWontDoAnother.get_id()],
    WeekendShiftsTypes.Friday: [IfEmployeeDidFridayInWeekendHeWontDoFriday.get_id(), IfEmployeeDidSatInWeekendHeWontDoFriday.get_id()],
    WeekendShiftsTypes.Saturday: [IfEmployeeDidSatInWeekendHeWontDoAnother.get_id(), IfEmployeeDidFridayInWeekendHeWontDoSat.get_id()]

}
