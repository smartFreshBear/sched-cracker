from objects.Classes import *


class board_weighter:

    @staticmethod
    def weight_weekend(board: PlanningBoard):
        sum_of_weights = 0
        for weekend in board.weekendMapping:
            sum_of_weights += len([slot for slot in weekend.from_shift_to_employee.values() if slot is None])

        return sum_of_weights

    @staticmethod
    def weight_midweek(board: PlanningBoard):
        sum_of_weights = 0
        for days in board.midWeekMapping:
            for day in days:
                sum_of_weights += len([slot for slot in day.from_shift_to_employee.values() if slot is None])

        return sum_of_weights