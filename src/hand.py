from terms import *
import numpy as np
import re

class Hand:
    def __init__(self, info):
        self.pot = 0
        self.actions = {}
        self.flop_board = None
        self.turn_card = None
        self.river_card = None
        self.N8Parser(info)
        pass

    def N8Parser(self, info):
        lines = info.splitlines()
        description = re.match(r".*#(?P<handID>\w+).*\$(?P<sb>[\d\.]+)\/\$(?P<bb>[\d\.]+).*\- (?P<dt>.+)$", lines.pop(0))
        btn_pos = int(re.match(r".*#(?P<btnPos>\d+).*", lines.pop(0)).group("btnPos"))
        split_index = [i for i, line in enumerate(lines) if line.startswith("***")]
        sections = list(map(lambda arr: arr.tolist(), np.split(lines, split_index)))
        while (len(sections) < 7):
            sections.insert(-2, None)
        positions, preflop, flop, turn, river, showdown, summary = sections
        self.handID, self.sb, self.bb, self.dt = description.group("handID"), float(description.group("sb")), float(description.group("bb")), description.group("dt")
        players = [re.match(r".*\s(?P<seat>\d+).*\s(?P<playerID>\w+).*\$(?P<stack>[\d\.]+).*", playerInfo) for playerInfo in filter(lambda line: line.startswith("Seat"), positions)]
        seating = GetPositionsList(len(players))
        while seating[(btn_pos-1)] != "BTN":
            seating.append(seating.pop(0))
        self.players = {player.group("playerID"): {"seat": player.group("seat"), "position": seating[i], "stack": float(player.group("stack"))} for i, player in enumerate(players)}
        self.actions["dead_money"] = self.ReadActions(positions[len(players):])
        self.players["Hero"]["cards"] = self.DealCards(preflop, False)
        self.actions["preflop"] = self.ReadActions(preflop)
        self.flop_board = self.DealCards(flop) if flop else None
        self.actions["flop"] = self.ReadActions(flop) if flop else None
        self.turn_card = self.DealCards(turn) if turn else None
        self.actions["turn"] = self.ReadActions(turn) if turn else None
        self.river_card = self.DealCards(river) if river else None
        self.actions["river"] = self.ReadActions(river) if river else None
        pass

    def DealCards(self, street, board=True):
        assert isinstance(street, list)
        start_str = "***" if board else "Dealt"
        return ReorderCards(re.match(r".*\[(?P<cards>.*)\]$", list(filter(lambda line: line.startswith(start_str), street))[0]).group("cards").replace(" ", ""))
    
    def ReadActions(self, street):
        actions = list(filter(lambda line: line.find(":") != -1, street))
        return list(map(lambda action: re.match(r"(?P<player>\w+): (?P<action>\w+)s.*?(?P<money>[\d\.]+)?$", action).groupdict(), actions))

    def GetFlop(self):
        pass

    def translate(self):
        pass

