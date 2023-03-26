from src.database import *
from src.hand import *
from functools import reduce
# import numpy as np
import re

def main():
    pass

if __name__ == "__main__":
    # l = [1,2,3,4,5,7]
    # d1 = {1:3, 2:7, 8:4}
    # d2 = {4:3, 2:9, 8:4}
    # d3 = {5:3, 6:0, 10:4}
    # # print(len(filter(lambda i: i % 2 == 1, l)))
    # l_d = [d1, d2, d3]
    # tmp = dict(reduce(lambda prev, next: prev | next, l_d))
    # # print(set().union(*l_d))
    # print(tmp)


    level = GetAllCGLevel()[0]
    history = GetAllPeriods(level)[0]
    sessions = GetAllSessions(history, level)
    break_loop = False
    for session in sessions:
        with open(os.path.join(HAND_HISTORY_FOLDER, level, history, session), "r") as f:
            hand_histories = f.read().strip()
        hands = list(map(lambda history: history.strip(), hand_histories.split("\n\n")))
        for i, hand in enumerate(hands):
            x = Hand(hand)
            if len(x.GetGameFlow()) > 7:
                break
            if x.one_blind:
                break_loop = True
                break
        if break_loop:
            break


    # print(hand)
    
    # info = hands[0]
    # print(info)
    # hand0 = Hand(info)
    # print(hand0.street_info)
    # hand0.Translate()
    # actions = hand0.street_info
    # debugMsg = [1,2,3,4,6,7]

