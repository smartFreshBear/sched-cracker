definitions:
weekend = Friday-Saturday

# -3 types of shifts during midweek:
#     1- long-shift
#     2- short-shift
#     3- night-shift
# #
# LONG [==============]
# SHORT[======]
# NIGHT		[=======]
#

# - 4 types of shifts during weekend:
#     1- long
#     2- short
#     3- friday evening
#     4- Saturday's eve

# - 4 types of shifts during weekend:
#     1- long  [==============          =============]
#     2- short [============================]
#     3- friday evening       [======]
#     4- Saturday's eve                 [===========]

- each day all the shifts needed to be filled

Rules:
A- once a week employee suppose to do 2+3 OR 1 -
B- if employee was working in a "Weekend" of type 1/2 so he cant work in Sunday or Thursday V
C- minimum options that each employee can ask is 2 un-consecutive days -
D- if employee did 3 he cant 1 or 2.
E- during weekend two Male employee can't work with each other.
F- during any shift two fresh employee cant work with each other.V

future suggestion
form verifier


Employee sending their time request in the follow fashion:
    1- sending their weekend requests(which is many weekend options) and getting back 1 of them hopefully.
    2- and sending  <name-of-employee, List-of-time-constraints>
________________________________________________________________________________________________________________________

EmployeeReqForWeekends:
    name: the name of employee
    list_of_weekends_demand: all the options of the employee to work at a weekend this month
    Sex: Male/Female
    IsNew: True/False

EmployeeReqForWeekDays:
    name: the name of employee
    list_of_shit_during_week: all the shift options of employee during the week.
    IsNew: True/False


Abstract Algorithm:
1- get List of EmployeeReqForWeekends and allocate weekends base on demands And Rules.
2- get List of EmployeeReqForWeekDays and allocate shifts base on demands and Rules.

#TODO for next time:
1- create the classes: EmployeeReqForWeekends, EmployeeReqForWeekDays, model and create Rule
2- connect to google sheet