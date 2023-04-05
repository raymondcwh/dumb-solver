import os
from private.paths import *
from .hand import Hand


def GetAllSites():
    sites = os.listdir(RAW_HAND_HISTORY_FOLDER)
    return sites


def GetAllCGLevel(site):
    levels = os.listdir(os.path.join(RAW_HAND_HISTORY_FOLDER, site))
    return levels


def GetAllPeriods(level, site):
    periods = list(filter(lambda dir: os.path.isdir(os.path.join(RAW_HAND_HISTORY_FOLDER,
                   site, level, dir)),  os.listdir(os.path.join(RAW_HAND_HISTORY_FOLDER, site, level))))
    return periods


def GetAllSessions(period, level, site):
    sessions = os.listdir(os.path.join(
        RAW_HAND_HISTORY_FOLDER, site, level, period))
    return list(map(lambda session: os.path.join(RAW_HAND_HISTORY_FOLDER, site, level, period, session), sessions))


def GetHandReview(sessions):
    processed_hands = {}
    solver_flops = {}
    for session in sessions:
        with open(session, "r") as f:
            hand_histories = f.read().strip()
        hands = list(
            map(lambda history: history.strip(), hand_histories.split("\n\n")))
        for hand in hands:
            handObj = Hand(hand)
            if handObj.hero_involved:
                category = handObj.GetHandClassification()
                categoryKey = "\\".join(category)
                if categoryKey not in processed_hands.keys():
                    processed_hands[categoryKey] = []
                processed_hands[categoryKey].append(hand)
                if (len(category) == 3) and (category[0] == "standard") and (not category[1].startswith("limp")) and (category[2].find("vs") != -1):
                    if categoryKey not in solver_flops.keys():
                        solver_flops[categoryKey] = set()
                    boards = handObj.GetStandardBoardHands(True)
                    for board in boards:
                        solver_flops[categoryKey].add(board[0])
    return [processed_hands, solver_flops]


def GetExistingSolverFlops(folder):
    flop_files = os.listdir(folder)
    file_num = 0
    old_flops = set()
    for file in flop_files:
        with open(os.path.join(folder, file), "r") as f:
            flops = f.read().strip()
        old_flops.union(set(map(lambda flop: flop.strip(), flops.split("\n"))))
        file_num += 1
    return [old_flops, str(file_num).zfill(4)]

def UpdateDatabase():
    solver_flops_new = {}
    sites = GetAllSites()
    for site in sites:
        levels = GetAllCGLevel(site)
        for level in levels:
            periods = GetAllPeriods(level, site)
            last_update_file = os.path.join(
                RAW_HAND_HISTORY_FOLDER, site, level, "last_update.txt")
            if os.path.exists(last_update_file):
                with open(last_update_file, "r") as f:
                    last_update = f.readline()
                periods = periods[(periods.index(last_update)+1):]
            if periods:
                for period in periods:
                    sessions = GetAllSessions(period, level, site)
                    review_hands, solver_flops = GetHandReview(sessions)
                    for category, hands in review_hands.items():
                        folder = os.path.join(
                            PROCESSED_HAND_HISTORY_FOLDER, category)
                        if not os.path.exists(folder):
                            os.makedirs(folder)
                        with open(os.path.join(folder, f"{site}_{level}_{period}.txt"), "w") as f:
                            f.write("\n\n\n".join(hands))
                    for category, flops in solver_flops.items():
                        if category in solver_flops_new.keys():
                            solver_flops_new[category] = solver_flops_new[category].union(flops)
                        else:
                            solver_flops_new[category] = flops
                with open(last_update_file, "w") as f:
                    f.write(period)
    for category, flops in solver_flops_new.items():
        folder = os.path.join(SOLVER_FLOP_FOLDER, category)
        if not os.path.exists(folder):
            os.makedirs(folder)
        old_flops, file_num = GetExistingSolverFlops(folder)
        with open(os.path.join(folder, f"{file_num}.txt"), "w") as f:
            f.write("\n".join(list(flops.difference(old_flops))))
        gto_folder = os.path.join(SOLVER_FILE_FOLDER, category)
        if not os.path.exists(gto_folder):
            os.makedirs(gto_folder)
        with open(os.path.join(gto_folder, f"{file_num}.gto"), "x") as f:
            pass
    return
