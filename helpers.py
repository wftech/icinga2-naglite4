from enum import Enum


class State(Enum):
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3


class StatePriority(Enum):
    OK = 4
    WARNING = 2
    CRITICAL = 1
    UNKNOWN = 3


class StateCssClass(Enum):
    OK = 'state-ok'
    WARNING = 'state-warning'
    CRITICAL = 'state-critical'
    UNKNOWN = 'state-unknown'
