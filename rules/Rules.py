from objects.classes import Rule, DaysOfWeek, WeekendShiftsTypes, MidWeekShiftType


def get_overlapping_employees_with_shift(board, week, day, shift):
    intersected_shifts = shift.intersect_with(shift)
    dic = board.get_entity(week, day).from_shift_to_employee
    intersected_employees = [dic.get(key) for key in intersected_shifts]
    return intersected_employees


class NoTwoNewInOneShift(Rule):

    def check(self, employee, board, week=None, day=None, shift=None):

        if not employee.isNew:
            return True
        else:
            overlap_employees = get_overlapping_employees_with_shift(board, week, day, shift)

            new_employees_other_then_current = [employee for employee in overlap_employees
                                                if (employee is not None) and employee.isNew]

            return len(new_employees_other_then_current) == 0


class TwoMaleEmployeeDuringWeekend(Rule):

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

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is None:
            return True

        day_from_enum = DaysOfWeek.from_int_zero(day)
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


# class EmployeeCanDoShortOrLongInWeekendOnceAMonth:
#
#     def check(self, employee, board, week=None, day=None, shift=None):

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


class IfEmployeeDidShortHeWontDoItAgainOrWillNotDoNight:
    def check(self, employee, board, week=None, day=None, shift=None):
        if day is None:
            return True
        else:
            if shift == MidWeekShiftType.Short:
                employees_that_did_shorts = get_all_employees_for_shift_in_for_previous_days(board, week, day,
                                                                                             MidWeekShiftType.Short)
                employees_that_did_longs = get_all_employees_for_shift_in_for_previous_days(board, week, day,
                                                                                            MidWeekShiftType.Long)
                return (employee not in employees_that_did_shorts) and (employee not in employees_that_did_longs)

            if shift == MidWeekShiftType.Long:
                employees_that_did_shorts = get_all_employees_for_shift_in_for_previous_days(board, week, day,
                                                                                             MidWeekShiftType.Short)
                employees_that_did_nights = get_all_employees_for_shift_in_for_previous_days(board, week, day,
                                                                                             MidWeekShiftType.Night)
                employees_that_did_long = get_all_employees_for_shift_in_for_previous_days(board, week, day,
                                                                                           MidWeekShiftType.Long)
                return (employee not in employees_that_did_shorts) and (employee not in employees_that_did_nights) and (
                            employee not in employees_that_did_long)
            else:
                return True


class EmployeeCanDoShortOrLongInWeekendOnceAMonth:

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is not None:
            return True
        else:
            if shift == WeekendShiftsTypes.Short or shift == WeekendShiftsTypes.Long:
                employees_that_did_shorts = get_all_employees_for_shift_in_for_previous_weekends(board, week, day,
                                                                                                 WeekendShiftsTypes.Short)
                employees_that_did_longs = get_all_employees_for_shift_in_for_previous_weekends(board, week, day,
                                                                                                WeekendShiftsTypes.Long)
                return (employee not in employees_that_did_shorts) and (employee not in employees_that_did_longs)
            else:
                return True


class EmployeeCanDoFridayNightOrSaturdayNightOnceAMonth:

    def check(self, employee, board, week=None, day=None, shift=None):
        if day is not None:
            return True
        else:
            if shift == WeekendShiftsTypes.Friday or shift == WeekendShiftsTypes.Saturday:
                employees_that_did_friday = get_all_employees_for_shift_in_for_previous_weekends(board, week, day,
                                                                                                 WeekendShiftsTypes.Friday)
                employees_that_did_sats = get_all_employees_for_shift_in_for_previous_weekends(board, week, day,
                                                                                                WeekendShiftsTypes.Saturday)
                return (employee not in employees_that_did_friday) and (employee not in employees_that_did_sats)
            else:
                return True

