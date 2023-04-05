def GetPositionsList(n):
    assert n > 1
    positions = ["SB", "BB", "UTG", "UTG+1",
        "UTG+2", "UTG+3", "LJ", "HJ", "CO", "BTN"]
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
    assert all(map(lambda c: c in rank, cards[::2])) and all(
        map(lambda s: s in suit, cards[1::2])), "Cards not exist"
    return "".join(sorted([cards[i:i+2] for i in range(0, len(cards), 2)], key=lambda card: rank.index(card[0])))


# def StandardizeBoardHand(flop, turn="", river="", hand=""):
    assert len(flop) == 6, "Invalid flop input"
    standard = "sdc"
    flop = ReorderCards(flop)
    flop_suit = list(flop)[1::2]
    flop_standard = list(flop)
    turn_standard = ReorderCards(turn)
    river_standard = ReorderCards(river)
    hand = ReorderCards(hand)
    hand_standard = list(hand)
    if len(set(flop_suit)) == 3:
        flop_standard[1::2] = standard
        turn_standard = turn.replace(turn[1], (standard[flop_suit.index(
            turn[1])] if turn[1] in flop_suit else "h")) if turn else turn
        river_standard = river.replace(river[1], (standard[flop_suit.index(
            river[1])] if river[1] in flop_suit else "h")) if river else river
    elif len(set(flop_suit)) == 2:
        flop_standard[1::2] = "".join([standard[0] if suit == flop_suit[0] else standard[1] for suit in flop_suit])
        turn_standard = turn.replace(turn[1], ((standard[0] if turn[1] == flop_suit[0] else standard[1]) if turn[1] in set(flop_suit) else "c")) if turn else turn
        # river_standard = river.replace(river[1], ((standard[0] if river[1] == flop_suit[0] else standard[1]) if river[1] in set(flop_suit) else (turn_standard[1] if river[1] == turn[1] else "h"))) if river else river
        river_standard = river.replace(river[1], ((standard[0] if river[1] == flop_suit[0] else standard[1]) if river[1] in set(flop_suit) else (turn_standard[1] if river[1] == turn[1] else ("c" if turn[1] in set(flop_suit) else "h")))) if river else river
    else:
        flop_standard[1::2] = standard[0]*3
        turn_standard = turn.replace(turn[1], (standard[0] if turn[1] in set(flop_suit) else standard[1])) if turn else turn
        # river_standard = river.replace(river[1], (standard[0] if river[1] in set(flop_suit) else (standard[1] if river[1] == turn[1] else standard[2]))) if river else river
        river_standard = river.replace(river[1], (standard[0] if river[1] in set(flop_suit) else (standard[1] if river[1] == turn[1] else (standard[1] if turn[1] in set(flop_suit) else standard[2])))) if river else river
    if hand:
        original_board = flop + turn + river
        standard_board = "".join(flop_standard) + turn_standard + river_standard
        original_suit = original_board[1::2]
        standard_suit = standard_board[1::2]
        n_suit = len(set(original_suit))
        if n_suit > 2:
            hand_standard[1::2] = "".join(list(map(lambda suit: standard_suit[original_suit.index(suit)] if suit in original_suit else "h", hand[1::2])))
        else:
            hand_suit = list(map(lambda suit: suit in set(original_suit), hand[1::2]))
            if all(hand_suit):
                hand_standard[1::2] = list(map(lambda suit: standard_suit[original_suit.index(suit)], hand[1::2]))
            else:
                if n_suit == 2:
                    hand_standard[1::2] = [standard_suit[original_suit.index(suit)] if hand_suit[i] else "c" for i, suit in enumerate(hand[1::2])] if any(hand_suit) else ("cc" if len(set(hand[1::2])) == 1 else "ch")
                else:
                    hand_standard[1::2] = [standard_suit[original_suit.index(suit)] if hand_suit[i] else "d" for i, suit in enumerate(hand[1::2])] if any(hand_suit) else ("dd" if len(set(hand[1::2])) == 1 else "dc")
    return ["".join(flop_standard), turn_standard, river_standard, "".join(hand_standard)]


def StandardizeBoardHand(flop, turn="", river="", hand=""):
    standard = "sdch"
    assert len(flop) == 6, "Invalid flop input"
    assert len(hand) == 4 or len(hand) == 0, "Invalid hand input"
    flop = ReorderCards(flop)
    flop_standard = list(flop)
    turn_standard = ReorderCards(turn)
    river_standard = ReorderCards(river)
    hand = ReorderCards(hand)
    hand_standard = list(hand)
    board_suit = list(flop)[1::2]
    board_suit_order = sorted(set(board_suit), key=board_suit.index)
    all_cards = flop+turn+river+hand
    all_cards = [all_cards[i:i+2] for i in range(0, len(all_cards), 2)]
    assert len(all_cards) == len(set(all_cards)), "Repeated Cards"
    flop_standard[1::2] = list(map(lambda suit: standard[board_suit_order.index(suit)], board_suit))
    if hand:
        board_suit_order.extend(filter(lambda suit: suit not in board_suit_order, hand[1::2]))
        hand_standard[1::2] = list(map(lambda suit: standard[board_suit_order.index(suit)], hand[1::2]))
    if turn:
        board_suit_order.extend(filter(lambda suit: suit not in board_suit_order, turn[1]))
        turn_standard = turn.replace(turn[1], standard[board_suit_order.index(turn[1])])
    if river:
        board_suit_order.extend(filter(lambda suit: suit not in board_suit_order, river[1]))
        river_standard = river.replace(river[1], standard[board_suit_order.index(river[1])])
    return ["".join(flop_standard), turn_standard, river_standard, "".join(hand_standard)]
