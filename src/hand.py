from .term import *
import numpy as np
import re

class Hand:
    def __init__(self, info):
        self.pot = 0
        self.preflop_open = -1  # -1 - non-open, 0 - limp as first action, 1 - raise as first action
        self.limp = False
        self.postflop = False
        self.multiway = False
        self.street_info = {}
        self.one_blind = False
        self.N8Parser(info)
        pass

    def N8Parser(self, info):
        lines = info.splitlines()
        description = re.match(r".*#(?P<handID>\w+).*\$(?P<sb>[\d\.]+)\/\$(?P<bb>[\d\.]+).*\- (?P<dt>.+)$", lines.pop(0))
        btn_pos = int(re.match(r".*#(?P<btnPos>\d+).*", lines.pop(0)).group("btnPos"))
        split_index = [i for i, line in enumerate(lines) if line.startswith("***")]
        sections = list(map(lambda arr: arr.tolist(), np.split(lines, split_index)))
        positions = sections.pop(0)
        preflop = sections.pop(0)
        summary = sections.pop()
        flop_list = list(filter(lambda section: section[0].startswith("***") and (section[0].lower().find("flop") != -1), sections)).copy()
        turn_list = list(filter(lambda section: section[0].startswith("***") and (section[0].lower().find("turn") != -1), sections)).copy()
        river_list = list(filter(lambda section: section[0].startswith("***") and (section[0].lower().find("river") != -1), sections)).copy()
        showdown_list = list(filter(lambda section: section[0].startswith("***") and (section[0].lower().find("showdown") != -1), sections)).copy()

        # while (len(sections) < 7):
            # sections.insert(-2, None)
        
        # positions, preflop, flop, turn, river, showdown, summary = sections

        self.handID, self.sb, self.bb, self.dt = description.group("handID"), float(description.group("sb")), float(description.group("bb")), description.group("dt")
        players = [re.match(r".*\s(?P<seatN>\d+).*\s(?P<player>\w+).*\$(?P<stack>[\d\.]+).*", playerInfo).groupdict() for playerInfo in filter(lambda line: line.startswith("Seat"), positions)]
        
        if len(positions[len(players):]) < 2:
            self.one_blind = True
            exit()
        
        btn_pos = list(map(lambda player: int(player["seatN"]), players)).index(btn_pos)
        seating = GetPositionsList(len(players))
        while seating[btn_pos] != "BTN":
            seating.append(seating.pop(0))
        self.players = {player["player"]: {"seatN": player["seatN"], "position": seating[i], "stack": float(player["stack"])} for i, player in enumerate(players)}
        self.street_info["dead_money"] = self.ReadActions(positions[len(players):], dead=True)
        self.players["Hero"]["cards"] = self.DealCards(preflop, False)
        self.street_info["preflop"] = self.ReadActions(preflop)
        self.flop_board = list(map(lambda flop: self.DealCards(flop), flop_list))
        self.street_info["flop"] = list(map(lambda flop: self.ReadActions(flop), flop_list))
        self.turn_card = list(map(lambda turn: self.DealCards(turn), turn_list))
        self.street_info["turn"] = list(map(lambda turn: self.ReadActions(turn), turn_list))
        self.river_card = list(map(lambda river: self.DealCards(river), river_list))
        self.street_info["river"] = list(map(lambda river: self.ReadActions(river), river_list))
        self.street_run = [len(self.flop_board), len(self.turn_card), len(self.river_card)]
        pot_calculation = self.AnalyzeHand()
        showdown_list = list(map(lambda showdown: self.ReadActions(showdown, showdown=True), showdown_list))   # return list of list of dict
        showdown_list = list(map(lambda showdown: {res["player"]: res["money"] for res in showdown}, showdown_list))
        showdown = {player: sum(map(lambda showdown: float(showdown.get(player, 0)), showdown_list)) for player in set().union(*showdown_list)}
        self.pot_record, self.rake, self.jackpot, self.bingo, self.fortune = map(float, re.findall(r"\$([\d\.]+)", summary[1]))
        assert (self.pot_record == round(pot_calculation, 4)) or ((sum(showdown.values()) + self.rake + self.jackpot + self.bingo + self.fortune) == round(pot_calculation, 4)), f"Correct pot: {self.pot_record}"
        return

    def DealCards(self, street, board=True):
        assert isinstance(street, list)
        start_str = "***" if board else "Dealt to Hero"
        return ReorderCards(re.match(r".*\[(?P<cards>.*)\]$", list(filter(lambda line: line.startswith(start_str), street))[0], flags=re.I).group("cards").replace(" ", ""))
    
    def ReadActions(self, street, dead=False, showdown=False):
        filter_str = "collected" if showdown else ":"
        actions = list(filter(lambda line: line.find(filter_str) != -1, street))
        if dead:
            re_str = r"(?P<player>\w+).*?(?P<type>\w+)?\s(?P<action>\w+)\s\$(?P<money_cards>[\d\.]+).*?(?P<allin>all\-in)?$"
        elif showdown:
            re_str = r"(?P<player>\w+).*?(?P<money>[\d\.]+).*$"
        else:
            re_str = r"(?P<player>\w+): (?P<action>\w+).*?(?P<money_cards>[\d\.]+|[\w\s]+)?(?:[\]\)].*|[a-z\-\s]*?)(?P<allin>all\-in)?$"
        # re_str = r"(?P<player>\w+): (?P<action>\w+).*?(?P<money_cards>[\d\.]+|[\w\s]+)?(?:[\]\)].*|[a-z\-\s]*?)(?P<allin>all\-in)?$" if not dead else r"(?P<player>\w+).*?(?P<type>\w+)?\s(?P<action>\w+)\s\$(?P<money_cards>[\d\.]+).*?(?P<allin>all\-in)?$"
        return list(map(lambda action: re.match(re_str, action).groupdict(), actions))

    def GetGameFlow(self):
        gameflow = ["dead_money", "preflop"]
        postflop = ["flop", "turn", "river"]
        n_run = max(self.street_run)
        if n_run > 1:
            normal_street = postflop[:self.street_run.index(n_run)]
            allin_street = postflop[self.street_run.index(n_run):]
            gameflow.extend(normal_street)
            for i in range(n_run):
                gameflow.extend(list(map(lambda street: f"{street}{i}", allin_street)))
        else:
            gameflow.extend(postflop)
        return gameflow

    def AnalyzeHand(self):
        details = {}
        # limp = False
        # postflop = False
        pot = 0
        gameflow = self.GetGameFlow()
        for i, street in enumerate(gameflow):
            street_type, n_run = re.match(r"([a-z_]+).*?(\d)?$", street).groups()
            n_run = int(n_run) if n_run else 0
            actions = self.street_info[street_type]
            n_bet = 0
            if street_type in ["flop", "turn", "river"]:
                actions = actions[n_run] if actions else actions
            if street_type != "preflop":
                bet = {}
            if not actions:
                continue
            key_actions = []
            if bet:
                order = GetPositionsList(len(self.players))
                position_order = {order.index(self.players[player]["position"]): player for player, money in bet.items() if money == max(bet.values())}
                aggressor = position_order.get(max(position_order.keys()))
            else:
                aggressor = None
            caller = []
            details[street] = {}
            if i > 1:
                self.postflop = True
            n_way = len(set(map(lambda action: action["player"], actions))) if self.postflop else None
            if n_way and n_way > 2:
                self.multiway = True
            for action in actions:
                action["action"] = action["action"].rstrip("s")
                if action["action"][0].isupper():
                    if action["action"].casefold() == "bet":
                        if action["money_cards"].find("fold") != -1:
                            action["money_cards"] = None
                            action["action"] = "fold"
                        else:
                            action["action"] = action["action"].casefold()
                    else:
                        if re.search(r"[\d\.]+", action["money_cards"]):
                            self.cashout_fee = float(action["money_cards"])
                        continue
                if street_type == "dead_money":
                    if action["type"] == "missed":
                        pot += float(action["money_cards"])
                        continue
                    elif action["action"] == "straddle":
                        self.players[action["player"]]["straddle"] = float(action["money_cards"])
                if action["action"] not in ["fold", "check"]:
                    if action["action"] == "call":
                        bet[action["player"]] = ((bet[action["player"]]+float(action["money_cards"])) if action["player"] in bet.keys() else float(action["money_cards"])) if action["allin"] else max(bet.values())
                        # bet[action["player"]] = max(bet.values()) if action["allin"] else max(bet.values())
                        if (self.preflop_open == -1) and (street_type == "preflop"):
                            self.preflop_open = 0
                        if action["player"] not in caller:
                            caller.append(action["player"])
                    elif action["action"] == "show":
                        action["money_cards"] = ReorderCards(action["money_cards"].replace(" ", ""))
                    else:
                        bet[action["player"]] = float(action["money_cards"])
                        if street_type != "dead_money":
                            if street_type == "preflop":
                                if (self.preflop_open == -1):
                                    self.preflop_open = 1
                                else:
                                    ...
                            n_bet += 1
                            aggressor = action["player"]
                            caller.clear()
                if (street_type == "preflop") and (action["player"] not in map(lambda s: s["player"], key_actions)) and (action["action"] == "fold"):
                    continue
                action["allin"] = action["allin"] is not None
                key_actions.append(action)
            if bet:
                max_bet = max(bet.values())
                # n_equal_bets = len(list(filter(lambda b: b == max_bet, bet.values())))
                if street_type == "preflop":
                    self.limp = (self.preflop_open == 0) and (max_bet == self.bb)
                    # if n_equal_bets > 1:
                    #     self.limp = (max_bet == self.bb) and (self.preflop_open != -1)
                    self.preflop_allin = len(list(filter(lambda action: action["allin"], key_actions))) > 1
                if (street_type != "dead_money") and len(list(filter(lambda b: b == max_bet, bet.values()))) > 1:
                    pot += sum(bet.values())
                elif aggressor:
                    bet.pop(aggressor)
                    pot += (max(bet.values()) + sum(bet.values())) if bet else 0
            details[street].update({"actions": key_actions, "pot": (pot + sum(bet.values())) if street_type == "dead_money" else pot, "aggressor": aggressor, "n_way": n_way, "n_bet": n_bet})
        
        # print(bet)
        self.street_info = details
        print(self.handID, self.dt)
        print(self.street_info)
        print(self.preflop_open)
        print(self.limp)
        print(self.preflop_allin)
        print(self.postflop)
        return pot

    def GetStandardBoardHands(self, standard=False):
        pass

    def Translate(self, bb=True, position=True):
        street_actions = [list(map(lambda action: self.players[action["player"]]["position"], info["actions"])) for street, info in self.street_info.items() if info]
        print(street_actions)
        hero = self.players["Hero"]
        summary = f"""
        {len(self.players)} players
        Hero {hero["position"]} {hero["cards"]} ({round(hero["stack"]/self.bb,2)} BB)

        Preflop ({round(self.street_info["dead_money"]["pot"]/self.bb,2)} BB)

        """
        return summary

