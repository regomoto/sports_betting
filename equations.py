import numpy as np

def amer_odds_to_prob (odds):
    if odds < 0:
        return (-1*(odds)) / (-1*(odds) + 100) 
    elif odds > 0:
        return 100 / (odds + 100)
    elif (odds == 0.0) | (odds==np.nan):
        return 0
    else:
        raise TypeError('Not able to process input');
        
        

def amer_odds_to_decimal (odds):
    if odds < 0:
        return (100 / abs(odds)) + 1
    elif odds > 0:
        return (odds / 100) +1
    elif odds == 0:
        return 0
    else:
        raise TypeError('Not able to process input')
        

'''
input: 
- a list that contains the american decimal for the parlay. each list
item represents the moneyline amercan decimal for a game. for example, [200, 150] is a 2 leg parlay where the first gameis +200 and the 
second game is +150.

output:
- multiplier to your bet

'''
def parlay_multiplier (odds_list):
    # use input list and convert each item to decimal odds
    parlay_decimal_odds_list = [amer_odds_to_decimal(i) \
                                for i in odds_list]
    # muiltiply all decimal odds together to get a 
    # multiplier to use with your wager and return the multiplier
    # rounding down to int so payout not overstated
    return int(np.prod(parlay_decimal_odds_list))
