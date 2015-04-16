'''
A Basic Markowitz portfolio of Stocks and Bonds.  
Change it from 50/50 to 60/40 or 70/30.
'''

from __future__ import division
import datetime
import pytz
import pandas as pd
from zipline.api import order_target_percent

def initialize(context):
    set_long_only()
    set_symbol_lookup_date('2005-01-01') 
 
    context.secs = symbols( 'VTI', 'AGG')  # Securities
    context.pcts =        [ 0.7,  0.3 ]   # Percentages
    context.ETFs = zip(context.secs, context.pcts)
    # Check to rebalance every month, but only do it in December
    schedule_function(rebalance,
        date_rules.month_end(days_offset=5), # trade before EOY settlment dates
        time_rules.market_open(minutes=45)) # trade after 10:15am
    return

def rebalance(context, data):
    threshold = 0.05   # trigger a rebalance if we are off by this threshold (5%)
    # Get the current exchange time, in the exchange timezone 
    exchange_time = pd.Timestamp(get_datetime()).tz_convert('US/Eastern')
    if exchange_time.month < 12:
        return # bail if it's not December
    
    need_full_rebalance = False
    portfolio_value = context.portfolio.portfolio_value
    
    # rebalance if we have too much cash
    if context.portfolio.cash / portfolio_value > threshold:
        need_full_rebalance = True
    
    # or rebalance if an ETF is off by the given threshold
    for sid, target in context.ETFs:
        pos = context.portfolio.positions[sid]
        position_pct = (pos.amount * pos.last_sale_price) / portfolio_value
        # if any position is out of range then rebalance the whole portfolio
        if abs(position_pct - target) > threshold:
            need_full_rebalance = True
            break # don't bother checking the rest
    # perform the full rebalance if we flagged the need to do so
    if need_full_rebalance:
        for sid, target in context.ETFs:
            order_target_percent(sid, target)
        log.info("Rebalanced at %s" %  str(exchange_time))
        context.rebalance_date = exchange_time

def handle_data(context, data):
    pass


