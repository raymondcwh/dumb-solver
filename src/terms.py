

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