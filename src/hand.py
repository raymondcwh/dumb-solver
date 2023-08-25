from .term import *
import numpy as np
import re

class Hand:
    def __init__(self, info, n8=True):
        self.pot = 0
        self.straddle = 0
        self.preflop_open = False
        self.postflop = False
        self.street_info = {}
        self.n8 = n8
        self.N8Parser(info)
        pass

    def N8Parser(self, info):
        self.h2n = info
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
        self.handID, self.sb, self.bb, self.dt = description.group("handID"), float(description.group("sb")), float(description.group("bb")), description.group("dt")
        players = [re.match(r".*\s(?P<seatN>\d+).*\s(?P<player>\w+).*\$(?P<stack>[\d\.]+).*", playerInfo).groupdict() for playerInfo in filter(lambda line: line.startswith("Seat"), positions)]
        
        btn_pos = list(map(lambda player: int(player["seatN"]), players)).index(btn_pos)
        seating = GetPositionsList(len(players))
        while seating[btn_pos] != "BTN":
            seating.append(seating.pop(0))
        self.players = {player["player"]: {"seatN": int(player["seatN"]), "position": seating[i], "stack": float(player["stack"])} for i, player in enumerate(players)}
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
        showdown_list = list(map(lambda showdown: self.ReadActions(showdown, showdown=True), showdown_list))
        # showdown_list = list(map(lambda showdown: {res["player"]: float(res["money"]) for res in showdown}, showdown_list))
        tmp_showdown_list = []
        for showdown in showdown_list:
            tmp_showdown = {}
            for res in showdown:
                if res["player"] not in tmp_showdown.keys():
                    tmp_showdown[res["player"]] = float(res["money"])
                else:
                    tmp_showdown[res["player"]] += float(res["money"])
            tmp_showdown_list.append(tmp_showdown)
        showdown_list = tmp_showdown_list
        self.showdown = {player: sum(map(lambda showdown: showdown.get(player, 0), showdown_list)) for player in set().union(*showdown_list)}
        self.other_fees = []
        self.pot_record, self.rake, *self.other_fees = map(float, re.findall(r"\$([\d\.]+)", summary[1]))
        pre_rake_pot = (sum(self.showdown.values()) + self.rake + sum(self.other_fees))
        if (self.pot_record - self.rake - sum(self.other_fees)) != sum(self.showdown.values()):
            if (self.rake / self.pot_record) <= 0.05:
                assert (abs(pot_calculation - pre_rake_pot) < self.bb) or (abs(pot_calculation - (pre_rake_pot - sum(self.other_fees))) < self.bb), f"Pot record: {pre_rake_pot}, Pot calculated: {pot_calculation}"
            else:
                self.rake = self.pot_record - sum(self.showdown.values())
        else:
            assert (self.pot_record == round(pot_calculation, 4)) or ((sum(self.showdown.values()) + self.rake + sum(self.other_fees)) == round(pot_calculation, 4)), f"Correct pot: {self.pot_record}, Pot calculated: {pot_calculation}"
        # if self.hero_involved:
            # self.GetHandClassification()5
        # print(self.GetHandClassification())
        # boards = self.GetStandardBoardHands()
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
        self.limp = {}
        # postflop = False
        pot = 0
        gameflow = self.GetGameFlow()
        players = set(self.players.keys())
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
            if i > 1 and not self.preflop_allin:
                self.postflop = True
            n_way = len(players) if self.postflop else None
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
                    if action["action"] == "blind":
                        if action["type"] == "small":
                            if self.sb <= (self.bb/2):
                                if (float(action["money_cards"]) != self.sb):
                                    action["money_cards"] = str(self.sb)
                            else:
                                self.sb = float(action["money_cards"])
                        elif action["type"] == "big":
                            action["money_cards"] = action["money_cards"] if float(action["money_cards"]) == self.bb else str(self.bb)
                    if action["type"] == "missed":
                        pot += float(action["money_cards"])
                        continue
                    elif action["action"] == "straddle":
                        self.players[action["player"]]["straddle"] = float(action["money_cards"])
                        self.straddle += 1
                if action["action"] not in ["fold", "check"]:
                    if action["action"] == "call":
                        bet[action["player"]] = ((bet[action["player"]]+float(action["money_cards"])) if action["player"] in bet.keys() else float(action["money_cards"])) if action["allin"] else max(bet.values())
                        if (not self.preflop_open) and (street_type == "preflop"):
                            self.limp[action["player"]] = 0
                        if action["player"] not in caller:
                            caller.append(action["player"])
                    elif action["action"] == "show":
                        action["money_cards"] = ReorderCards(action["money_cards"].replace(" ", ""))
                    else:
                        bet[action["player"]] = float(action["money_cards"])
                        if street_type != "dead_money":
                            if street_type == "preflop":
                                if not self.preflop_open:
                                    self.preflop_open = True
                                elif action["player"] in self.limp.keys():
                                    self.limp[action["player"]] = 1
                            n_bet += 1
                            aggressor = action["player"]
                            caller.clear()
                elif action["action"] == "fold":
                    players.discard(action["player"])
                if (street_type == "preflop") and (action["player"] not in map(lambda s: s["player"], key_actions)) and (action["action"] == "fold"):
                    continue
                action["allin"] = action["allin"] is not None
                key_actions.append(action)
            if bet:
                max_bet = max(bet.values())
                # if street_type == "dead_money":
                #     self.straddle_pot = max_bet > self.bb
                # elif street_type == "preflop":
                if street_type == "preflop":
                    # self.hero_involved = any([player == "Hero" for player, bet_value in bet.items() if bet_value == max_bet]) or any(map(lambda action: (action["player"] == "Hero") and (action["allin"]), key_actions))
                    # self.hero_involved = any(map(lambda action: action["player"] == "Hero", key_actions))
                    allin_n = len(list(filter(lambda action: action["allin"], key_actions))) + len(list(filter(lambda action: action["allin"], details["dead_money"]["actions"])))
                    self.preflop_allin = allin_n and ((len(players) - allin_n) <= 1) and (len(players) > 1)
                    n_way = players.copy()
                if (street_type != "dead_money") and len(list(filter(lambda b: b == max_bet, bet.values()))) > 1:
                    pot += sum(bet.values())
                elif aggressor:
                    bet.pop(aggressor)
                    pot += (max(bet.values()) + sum(bet.values())) if bet else 0   
            details[street].update({"actions": key_actions, "pot": (pot + sum(bet.values())) if street_type == "dead_money" else pot, "aggressor": aggressor, "n_way": n_way, "n_bet": n_bet})
    
        # print(bet)
        self.hero_involved = self.postflop and ("Hero" in details["preflop"]["n_way"])
        self.street_info = details
        # print(self.handID, self.dt)
        # print(self.street_info)
        # print(self.preflop_open)
        # print(self.limp)
        # print(self.preflop_allin)
        # print(f"Hero involved: {self.hero_involved}")
        # print(self.postflop)
        return pot
    
    def GetHandClassification(self):
        category = []
        straddle_allin = len(list(filter(lambda action: action['allin'], self.street_info['dead_money']['actions'])))
        if self.straddle:
            category.append(f"straddle{'_allin' if straddle_allin else ''}")
        else:
            category.append("standard")
        n_bet = self.street_info["preflop"]["n_bet"]
        if self.postflop:
            limper = [limp for player, limp in self.limp.items() if player in self.street_info["preflop"]["n_way"]]
            if self.preflop_open:
                if n_bet == 1:
                    category.append(f"{'limp-call_' if limper else ''}SRP")
                else:
                    category.append(f"{'limp-raise_' if any(limper) else ''}{(n_bet+1)}-bet")
                if len(self.street_info["preflop"]["n_way"]) == 2:
                    aggressor = self.street_info["preflop"]["aggressor"]
                    caller = self.street_info["preflop"]["n_way"].difference({aggressor}).pop()
                    # print(aggressor)
                    # print(caller)
                    category.append(f"{self.players[aggressor]['position']}_vs_{self.players[caller]['position']}")
                else:
                    category.append(f"multiway")
            else:
                category.append(f"{'limp' if limper else 'unopened'}")
                category.append(f"{'multiway' if len(self.street_info['preflop']['n_way']) > 2 else 'HU'}")
        elif self.preflop_allin:
            if straddle_allin:
                allin = f"{'isolated' if len(self.street_info['preflop']['n_way']) == 2 else 'multiway'}"
            else:
                allin = f"{f'{(n_bet+1)}-bet' if (n_bet > 1) else 'raise'}_allin"
            category.append(allin)
        else:
            takepot = f"{f'{(n_bet+1)}-bet' if (n_bet > 1) else ('raise' if (n_bet == 1) else 'all')}_fold"
            category.append(takepot)
        return category

    def GetStandardBoardHands(self, standard=False):
        boards = [self.flop_board, self.turn_card, self.river_card]
        n_run = max(self.street_run)
        if n_run:
            n_run_idx = self.street_run.index(n_run)
            boards = list(map(lambda i: sum(boards[:n_run_idx], []) + list(map(lambda street: street[i] if street else "", boards[n_run_idx:])) + [self.players["Hero"]["cards"]], range(n_run)))
            if standard:
                boards = list(map(lambda run: StandardizeBoardHand(*run), boards))
            return boards
        else:
            return None

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
    
    # def ConvertH2N(self, lines):
    #     if self.n8:
    #         lines[0] = lines[0].replace("Poker", "Pokerstars").replace("#HD", "#20")
    #         lines = list(filter(lambda line: (line.casefold().find("dealt to") == -1) or (line.casefold().find("hero") != -1) , lines))
    #         summary_idx = [i for i, line in enumerate(lines) if line.startswith("***")][-1]
    #         lines[summary_idx:] = list(map(lambda line: line.replace("won", "collected"), lines[summary_idx:]))
    #     return "\n".join(lines)