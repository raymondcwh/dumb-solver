import os
import numpy as np
import json
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
    h2n_hands = []
    for session in sessions:
        with open(session, "r") as f:
            hand_histories = f.read().strip()
        hands = list(
            map(lambda history: history.strip(), hand_histories.split("\n\n")))
        for hand in hands:
            handObj = Hand(hand)
            h2n_hands.append(handObj.h2n)
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
        print(session, h2n_hands.__len__())
    return [processed_hands, solver_flops, "\n\n".join(h2n_hands)]


def ConvertH2N(sessions):
    all_hands = []
    for session in sessions:
        with open(session, "r") as f:
            hand_histories = f.read().strip()
        hands = list(
            map(lambda history: history.strip(), hand_histories.split("\n\n")))
        for hand in hands:
            lines = hand.splitlines()
            lines[0] = lines[0].replace("Poker", "Pokerstars").replace("#HD", "#20")
            lines = list(filter(lambda line: (line.casefold().find("dealt to") == -1) or (line.casefold().find("hero") != -1) , lines))
            summary_idx = [i for i, line in enumerate(lines) if line.startswith("***")][-1]
            lines[summary_idx:] = list(map(lambda line: line.replace("won", "collected"), lines[summary_idx:]))
            all_hands.append("\n".join(lines))
    print(all_hands.__len__())
    return "\n\n".join(all_hands)


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

def UpdateDatabase(h2n_convert=True):
    solver_flops_new = {}
    sites = GetAllSites()
    for site in sites:
        levels = GetAllCGLevel(site)
        for level in levels:
            periods = GetAllPeriods(level, site)
            last_update_file = os.path.join(RAW_HAND_HISTORY_FOLDER, site, level, "last_update.txt")
            if os.path.exists(last_update_file):
                with open(last_update_file, "r") as f:
                    last_update = json.loads(f.read())
                solver_update = periods.index(last_update["solver"])
                h2n_update = periods.index(last_update["h2n"])
                update_start = min(solver_update, h2n_update)
                periods = periods[(update_start+1):]
            else:
                solver_update = h2n_update = update_start = 0
                last_update = {}
            if periods:
                for period in periods:
                    sessions = GetAllSessions(period, level, site)
                    review_hands, solver_flops, h2n_hands = GetHandReview(sessions)
                    if update_start >= solver_update:
                        for category, hands in review_hands.items():
                            folder = os.path.join(PROCESSED_HAND_HISTORY_FOLDER, category)
                            if not os.path.exists(folder):
                                os.makedirs(folder)
                            with open(os.path.join(folder, f"{site}_{level}_{period}.txt"), "w") as f:
                                f.write("\n\n\n".join(hands))
                        for category, flops in solver_flops.items():
                            if category in solver_flops_new.keys():
                                solver_flops_new[category] = solver_flops_new[category].union(flops)
                            else:
                                solver_flops_new[category] = flops
                        last_update["solver"] = period
                    if update_start >= h2n_update:
                        if h2n_convert:
                            h2n_path = os.path.join(H2N_HAND_HISTORY_FOLDER, site)
                            if not os.path.exists(h2n_path):
                                os.makedirs(h2n_path)
                            with open(os.path.join(h2n_path, f"{level}_{period}.txt"), "w") as f:
                                f.write(h2n_hands)
                            last_update["h2n"] = period
                    update_start += 1
                with open(last_update_file, "w") as f:
                    f.write(json.dumps(last_update))
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
