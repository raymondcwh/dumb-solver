import os
from private.paths import *

def GetAllCGLevel():
    levels = os.listdir(HAND_HISTORY_FOLDER)
    return levels

def GetAllPeriods(level):
    periods = os.listdir(os.path.join(HAND_HISTORY_FOLDER, level))
    return periods

def GetAllSessions(period, level):
    sessions = os.listdir(os.path.join(HAND_HISTORY_FOLDER, level, period))
    return sessions