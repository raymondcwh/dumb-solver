def GetPositionsList(n):
    assert n > 1
    positions = ["SB", "BB", "UTG", "UTG+1", "UTG+2", "UTG+3", "LJ", "HJ", "CO", "BTN"]
    while n < len(positions):
        if len(positions) > 7:
            positions.pop(-5)
        elif len(positions) > 3:
            positions.pop(2)
        else:
            positions.pop(0)
    return positions


def ReorderCards(cards):
    suit = "dchs"
    rank = "AKQJT98765432"
    assert all(map(lambda c: c in rank, cards[::2])) and all(map(lambda s: s in suit, cards[1::2])), "Cards not exist"
    return "".join(sorted([cards[i:i+2] for i in range(0, len(cards), 2)], key=lambda card: rank.index(card[0])))


def StandardizeBoard(flop, turn="", river=""):
    standard = "sdc"
    flop = ReorderCards(flop)
    flop_suit = list(flop)[1::2]
    flop_standard = list(flop)
    if len(set(flop_suit)) == 3:
        flop_standard[1::2] = standard
        turn_standard = turn.replace(turn[1], (standard[flop_suit.index(turn[1])] if turn[1] in flop_suit else "h")) if turn else turn
        river_standard = river.replace(river[1], (standard[flop_suit.index(river[1])] if river[1] not in flop_suit else "h")) if river else river
    elif len(set(flop_suit)) == 2:
        flop_standard[1::2] = "".join([standard[0] if suit == flop_suit[0] else standard[1] for suit in flop_suit])
        turn_standard = turn.replace(turn[1], ((standard[0] if turn[1] == flop_suit[0] else standard[1]) if turn[1] in set(flop_suit) else "c")) if turn else turn
        river_standard = river.replace(river[1], ((standard[0] if river[1] == flop_suit[0] else standard[1]) if river[1] in set(flop_suit) else (turn_standard[1] if river[1] == turn[1] else "h"))) if river else river
    else:
        flop_standard[1::2] = standard[0]*3
        turn_standard = turn.replace(turn[1], (standard[0] if turn[1] in set(flop_suit) else standard[1])) if turn else turn
        river_standard = river.replace(river[1], (standard[0] if river[1] in set(flop_suit) else (standard[1] if river[1] == turn[1] else standard[2]))) if river else river
    return ["".join(flop_standard), turn_standard, river_standard]