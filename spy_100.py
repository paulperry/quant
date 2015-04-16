'''
    A benchmark comparison to buying and holding SPY at 100%.

    NOTE: This algo can run in minute-mode simulation and is compatible with LIVE TRADING.
'''

import pandas as pd
from zipline.api import order_target_percent

def initialize(context):
    set_long_only()
    set_symbol_lookup_date('2008-01-01') 
    schedule_function(trade,                      
                      date_rule=date_rules.every_day(),
                      time_rule=time_rules.market_open())

    context.secs = [symbol('SPY')]
    context.pcts = [1.0]
    context.ETFs = zip(context.secs, context.pcts) # list of tuples
 
def handle_data(context, data):
    pass

def trade(context, data):  
    """
    Make sure the porfolio is fully invested every day.
    """
    threshold = 0.05
    
    need_full_rebalance = False
    # rebalance if we have too much cash
    if context.portfolio.cash / context.portfolio.portfolio_value > threshold:
        need_full_rebalance = True
    
    # What we should do is first sell the overs and then buy the unders.
    if need_full_rebalance:
        # Get the current exchange time, in the exchange timezone 
        exchange_time = pd.Timestamp(get_datetime()).tz_convert('US/Eastern')
        # perform the full rebalance if we flagged the need to do so
        for sid, target in context.ETFs:
            order_target_percent(sid, target)
        log.info("Rebalanced at %s" %  str(exchange_time))

