from enum import Enum, IntEnum


class Employee:
    def __init__(self, name, sex, new=False, priority=100, rule_override=None):

        if rule_override is None:
            rule_override = []

        self.name = name
        self.sex = sex
        self.isNew = new
        # Employee not suppose to be aware of priority
        self.priority = priority
        self.rule_override = rule_override

    def __lt__(self, other):
        return other.priority < self.priority

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if other is None:
            return False
        return self.name == other.name and self.sex == other.sex

    def __contains__(self, *elem, **k):
        return self.name + self.sex


class DaysOfWeek(IntEnum):
    Sunday = 1,
    Monday = 2,
    Tuesday = 3,
    Wednesday = 4,
    Thursday = 5,

    def from_int_zero(index: int):
        return {
            0: DaysOfWeek.Sunday,
            1: DaysOfWeek.Monday,
            2: DaysOfWeek.Tuesday,
            3: DaysOfWeek.Wednesday,
            4: DaysOfWeek.Thursday,

        }[index]


class WeekOfTheMonth(IntEnum):
    First = 1,
    Second = 2,
    Third = 3,
    Forth = 4,
    Fifth = 5,

    @classmethod
    def from_int_zero(cls, index: int):
        return {
            0: WeekOfTheMonth.First,
            1: WeekOfTheMonth.Second,
            2: WeekOfTheMonth.Third,
            3: WeekOfTheMonth.Forth,
            4: WeekOfTheMonth.Fifth,

        }[index]


class ShiftTypes(IntEnum):
    @classmethod
    def intersect_with(cls, index):
        pass


class WeekendShiftsTypes(IntEnum):
    Short = 0,
    Long = 1,
    Friday = 2,
    Saturday = 3
    All = 4

    @classmethod
    def intersect_with(cls, index):
        return {
            cls.Long: [cls.Short, cls.Saturday],
            cls.Short: [cls.Long, cls.Friday, cls.Saturday],
            cls.Friday: [cls.Short],
            cls.Saturday: [cls.Short, cls.Long]

        }[index]

    @classmethod
    def get_literally_all(cls):
        return [cls.Short, cls.Long, cls.Friday, cls.Saturday]


class MidWeekShiftType(IntEnum):
    Short = 0,
    Long = 1,
    Night = 2,
    All = 4

    @classmethod
    def get_literally_all(cls):
        return [cls.Short, cls.Long, cls.Night]

    @classmethod
    def intersect_with(cls, index):
        return {
            cls.Long: [cls.Short, cls.Night],
            cls.Short: [cls.Long],
            cls.Night: [cls.Long]
        }[index]


class EmployeeConstraintsForWeekends:
    def __init__(self, from_weekend_to_constraints: dict[WeekOfTheMonth, list[WeekendShiftsTypes]] = None, employee: Employee = None):
        self.employee = employee
        self.from_day_to_constraint = from_weekend_to_constraints

    def __str__(self):
        return "{} : {} ".format(self.employee, self.from_day_to_constraint)

    def get_constraints_for_shift(self, week: int):
        constraints_for_weekend = self.from_day_to_constraint.get(WeekOfTheMonth.from_int_zero(index=week), [])
        if WeekendShiftsTypes.All in constraints_for_weekend:
            return WeekendShiftsTypes.get_literally_all()
        return constraints_for_weekend


class EmployeeConstraintsForWeekDays:
    def __init__(self, from_day_to_constraint: dict[(WeekOfTheMonth, DaysOfWeek), list[MidWeekShiftType]],
                 employee: Employee):
        self.from_day_to_constraint = from_day_to_constraint
        self.employee = employee

    def __str__(self):
        return "{} : {} ".format(self.employee, self.from_day_to_constraint)

    def get_constraints_for_shift(self, week: int, day: int):
        constraint_for_day_in_week = self.from_day_to_constraint.get((WeekOfTheMonth.from_int_zero(index=week),
                                                                      DaysOfWeek.from_int_zero(index=day)), [])
        if MidWeekShiftType.All in constraint_for_day_in_week:
            return MidWeekShiftType.get_literally_all()
        return constraint_for_day_in_week


class Day:
    def __init__(self):
        self.from_shift_to_employee = {
            MidWeekShiftType.Short: None,
            MidWeekShiftType.Long: None,
            MidWeekShiftType.Night: None,
        }

    def __str__(self):
        self.from_shift_to_employee.__str__()


class Weekend:
    def __init__(self):
        self.from_shift_to_employee = {
            WeekendShiftsTypes.Short: None,
            WeekendShiftsTypes.Long: None,
            WeekendShiftsTypes.Friday: None,
            WeekendShiftsTypes.Saturday: None
        }


class PlanningBoard:
    def __init__(self):
        self.weekendMapping = [Weekend(),
                               Weekend(),
                               Weekend(),
                               Weekend(),
                               Weekend()]

        self.midWeekMapping = [
            [Day(), Day(), Day(), Day(), Day()],
            [Day(), Day(), Day(), Day(), Day()],
            [Day(), Day(), Day(), Day(), Day()],
            [Day(), Day(), Day(), Day(), Day()],
            [Day(), Day(), Day(), Day(), Day()]
        ]

    def get_entity(self, week, day=None):
        if day is None:
            return self.weekendMapping[week]
        else:
            return self.midWeekMapping[week][day]


class Rule:
    def check(self, employee: Employee, board: PlanningBoard, week: int = None, day: int = None,
              shift: ShiftTypes = None) -> bool:
        pass
