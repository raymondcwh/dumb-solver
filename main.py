from src.database import *
from src.terms import *
from src.hand import Hand
import numpy as np
import re

if __name__ == "__main__":
    level = GetAllCGLevel()[0]
    history = GetAllPeriods(level)[0]
    session = GetAllSessions(history, level)[0]
    print(session)
    with open(os.path.join(HAND_HISTORY_FOLDER, level, history, session), "r") as f:
        hand_histories = f.read()
    hands = hand_histories.split("\n\n\n")
    info = hands[0]
    hand0 = Hand(info)
    # print(info)
    # lines = info.splitlines()
    # description = re.match(r".*#(?P<handID>\w+).*\$(?P<sb>[\d\.]+)\/\$(?P<bb>[\d\.]+).*\- (?P<dt>.+)$", lines.pop(0))
    # btn_pos = int(re.match(r".*#(?P<btnPos>\d+).*", lines.pop(0)).group("btnPos"))
    # split_index = [i for i, line in enumerate(lines) if line.startswith("***")]
    # sections = list(map(lambda arr: arr.tolist(), np.split(lines, split_index)))
    # while (len(sections) < 7):
    #     sections.insert(-2, None)
    # positions, preflop, flop, turn, river, showdown, summary = sections
    # handID, sb, bb, dt = description.group("handID"), float(description.group("sb")), float(description.group("bb")), description.group("dt")
    # players = [re.match(r".*\s(?P<seat>\d+).*\s(?P<playerID>\w+).*\$(?P<stack>[\d\.]+).*", playerInfo) for playerInfo in filter(lambda line: line.startswith("Seat"), positions)]
    # existPos = GetPositionsList(len(players))
    # while existPos[(btn_pos-1)] != "BTN":
    #     existPos.append(existPos.pop(0))
    # players = {player.group("playerID"): {"seat": player.group("seat"), "position": existPos[i], "stack": float(player.group("stack"))} for i, player in enumerate(players)}
    
    
    # actions = {}
    # actions["dead_money"] = list(map(lambda action: re.match(r"(?P<player>\w+).*\s(?P<action>\w+)\s\$(?P<money>[\d\.]+).*", action).groups() , positions[len(players):]))
    # hole_cards = re.match(r".*\[(?P<holeCards>.*)\]", list(filter(lambda line: line.startswith("Dealt to Hero"), preflop))[0]).group("holeCards").replace(" ", "")
    # players["Hero"]["cards"] = ReorderCards(re.match(r".*\[(?P<holeCards>.*)\]", list(filter(lambda line: line.startswith("Dealt to Hero"), preflop))[0]).group("holeCards").replace(" ", ""))
    # actions["preflop"] = list(map(lambda action: re.match(r"(?P<player>\w+): (?P<action>\w+)s.*?(?P<money>[\d\.]+)?$", action).groups(), list(filter(lambda line: line.find(":") != -1, preflop))))
    # actions["flop"] = list(map(lambda action: re.match(r"(?P<player>\w+): (?P<action>\w+)s.*?(?P<money>[\d\.]+)?$", action).groups(), list(filter(lambda line: line.find(":") != -1, flop)))) if flop else None
    
    # actions["turn"] = list(map(lambda action: re.match(r"(?P<player>\w+): (?P<action>\w+)s.*?(?P<money>[\d\.]+)?$", action).groupdict(), list(filter(lambda line: line.find(":") != -1, turn)))) if turn else None
    # actions["river"] = list(map(lambda action: re.match(r"(?P<player>\w+): (?P<action>\w+)s.*?(?P<money>[\d\.]+)?$", action).groupdict(), list(filter(lambda line: line.find(":") != -1, river)))) if river else None
    # print(actions)