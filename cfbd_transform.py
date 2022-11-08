import pandas as pd
import numpy as np
# cfbd imports
import time
import cfbd
from cfbd.rest import ApiException
from equations import amer_odds_to_prob, amer_odds_to_decimal

# pass in configuration, week number, year, and season type (default is 'regular')
# api key is alread env variable
# and get a pandas dataframe as output
def betting_api_dataframe (configuration, week, year, season_type = 'regular'):
    betting_api = cfbd.BettingApi(cfbd.ApiClient(configuration))
    
    # call API using configurations setup by user
    try:
        # Betting lines
        api_response = betting_api.get_lines(year=year, season_type=season_type, week=week)
    except ApiException as e:
        print("Exception when calling BettingApi->get_lines: %s\n" % e)
    
    # convert from JSON output to dataframe
    betting_df = pd.DataFrame.from_records([t.to_dict() for t in api_response])
    
    # api output has a 'lines column that is contained in a list that contains a dict'
    # this will deconstruct that object into columns to add to the dataframe
    lines_df = betting_df['lines'].apply(pd.Series, dtype = 'object')[0].apply(pd.Series)
    
    # concatenate the betting information to the game info for a complete pandas dataframe
    final_df = pd.concat([betting_df, lines_df], axis = 1).drop(columns=['lines',0])
    
    # sort by dates ascending
    final_df = final_df.sort_values('start_date')
    
    # filter for FBS
    # import FBS dataset do don't need API (API integration later)
    # getting FBS team information
    teams_api = cfbd.TeamsApi(cfbd.ApiClient(configuration))
    # use the get_fbs_teams() function to only pull in FBS terams
    fbs_teams = teams_api.get_fbs_teams()
    # convert from JSON to dataframe
    fbs_teams_df = pd.DataFrame.from_records([t.to_dict() for t in fbs_teams])
    # deconstruct dicitonary in location column into its own columns
    # add exploded location columns to dataframne and drop old location column
    fbs_teams_df = pd.concat([fbs_teams_df.drop(['location'], axis = 1), \
                           fbs_teams_df['location'].apply(pd.Series)], axis = 1)
    
    # get FBS conferences to filter the betting dataset
    fbs_conf_set = set(fbs_teams_df['conference'].to_list())
    # if any team in the matchup is in FBS
    # will keep matchups where FBS plays FCS school
    final_df = final_df[final_df['home_conference'].isin(fbs_conf_set) | \
          final_df['away_conference'].isin(fbs_conf_set)]
    
    #print(0)
    #print(sum(final_df['home_team']=='Iowa State')) 
    #print()
       
    # adjust timestamp for the 'start_date' col
    # convert column to timestamp
    # convert start_date column into timestamp
    final_df['start_date'] = pd.to_datetime(final_df['start_date'])
    final_df['start_date'] = final_df['start_date'] - pd.Timedelta(hours = 7)
    
    #print(1)
    #print(sum(final_df['home_team']=='Iowa State'))
    #print()
    
    # get home and away probabilities   
    # need to apply to each row that doesn't have a null for money lines
    temp_df = final_df
    temp_df['home_moneyline']= temp_df['home_moneyline'].fillna(value=0)
    temp_df['away_moneyline']= temp_df['away_moneyline'].fillna(value=0)
    home_win_prob = temp_df['home_moneyline'].apply(amer_odds_to_prob).round(7)
    away_win_prob = temp_df['away_moneyline'].apply(amer_odds_to_prob).round(7)
    
    #print(2)
    #print(sum(final_df['home_team']=='Iowa State'))
    #print() 
    
    # merge probabilities with the dataset on indexes
    final_df = final_df.merge(home_win_prob.rename('home_win_prob'), left_index=True, right_index=True)
    
    #print('a')
    #print(sum(final_df['home_team']=='Iowa State'))
    #print() 
    
    final_df = final_df.merge(away_win_prob.rename('away_win_prob'), left_index=True, right_index=True)
    
    #print('b')
    #print(sum(final_df['home_team']=='Iowa State'))
    #print() 
    
    # calculate vig/juice for each game
    # https://www.actionnetwork.com/education/juice
    # Team A Implied Probability / (Team A IP + Team B IP)
    final_df['vig'] = final_df['home_win_prob'] + final_df['away_win_prob'] - 1
    
    
    '''
    print('c')
    print(sum(final_df['home_team']=='Iowa State'))
    print() 
    
    print(3)
    print(sum(final_df['home_team']=='Iowa State'))
    print()
    '''
    
    # implied probabilities less vig see:
    # https://www.actionnetwork.com/education/juice
    # Team A Implied Probability / (Team A IP + Team B IP)
    final_df['home_win_prob_no_vig'] = final_df['home_win_prob'] / (final_df['home_win_prob'] + \
                                                                        final_df['away_win_prob'])
    final_df['away_win_prob_no_vig'] = final_df['away_win_prob'] / (final_df['away_win_prob'] + \
                                                                        final_df['home_win_prob'])
    
    #print(4)
    #print(sum(final_df['home_team']=='Iowa State'))
    #print()
    
    # make probabilities pretty (could make a function)
    final_df['home_win_prob_pretty'] = final_df['home_win_prob']\
    .astype(float).map(lambda n: '{:.2%}'.format(n))
    final_df['home_win_prob_no_vig_pretty'] = final_df['home_win_prob_no_vig']\
    .astype(float).map(lambda n: '{:.2%}'.format(n))
    final_df['away_win_prob_pretty'] = final_df['away_win_prob']\
    .astype(float).map(lambda n: '{:.2%}'.format(n))
    final_df['away_win_prob_no_vig_pretty'] = final_df['away_win_prob_no_vig']\
    .astype(float).map(lambda n: '{:.2%}'.format(n))
    
    
    # add a estimated end date column. can help with hedging on last  leg of parlays 
    final_df['end_time_est'] = final_df['start_date'] + pd.Timedelta(hours = 4)
    
    # drop row if 'provider' is blank
    # when spread is blank, it messes up the bet maker since the column is no longer a float
    final_df['provider'].replace('', np.nan, inplace = True)
    final_df.dropna(subset=['spread'], inplace = True)
    #print(sum(final_df['home_team']=='Iowa State'))
    
    # return the finished pandas dataframe
    return final_df