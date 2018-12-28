from enum import Enum


class State(Enum):
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3


class StateCssClass(Enum):
    OK = 'has-background-success'
    WARNING = 'has-background-warning'
    CRITICAL = 'has-background-danger'
    UNKNOWN = 'has-background-grey-light'
