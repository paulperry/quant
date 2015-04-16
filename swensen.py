'''
    This algorithm defines a long-only portfolio of 6 ETF's and rebalances all of 
    them when any one of them is off the target by a threshold of 5%.
    It is based on David Swensen's rationale for portfolio construction as defined in
    his book: "Unconventional Success: A Fundamental Approach to Personal Investment":
    http://www.amazon.com/Unconventional-Success-Fundamental-Approach-Investment/dp/0743228383 .
    The representative ETF's are defined here:
    http://seekingalpha.com/article/531591-swensens-6-etf-portfolio
    The target percents are defined here:
    https://www.yalealumnimagazine.com/articles/2398/david-swensen-s-guide-to-sleeping-soundly
    The rebalancing strategy is defined in the book and here:
    http://socialize.morningstar.com/NewSocialize/forums/p/102207/102207.aspx

    This is effectively a passive managment strategy or Lazy portfolio:
    http://en.wikipedia.org/wiki/Passive_management
    http://www.bogleheads.org/wiki/Lazy_portfolios

    Taxes are not modelled.
    
    NOTE: This algo can run in minute-mode simulation and is compatible with LIVE TRADING.
'''

from __future__ import division
import datetime
import pytz
import pandas as pd
from zipline.api import order_target_percent

def initialize(context):
    
    set_long_only()
    set_symbol_lookup_date('2005-01-01') # because EEM has multiple sid's. 
 
    context.secs = symbols('TIP', 'TLT', 'VNQ', 'EEM', 'EFA', 'VTI')  # Securities
    context.pcts =        [ 0.15,  0.15,   0.15,  0.1,  0.15,  0.3 ]  # Percentages
    context.ETFs = zip(context.secs, context.pcts)                    # list of tuples
    
    # Change this variable if you want to rebalance less frequently
    context.rebalance_days = 20    # 1 = can rebalance any day, 20 = every month

    # Set the trade time, if in minute mode, we trade between 10am and 3pm.
    context.rebalance_date = None
    context.rebalance_hour_start = 10
    context.rebalance_hour_end = 15

def handle_data(context, data):

    # Get the current exchange time, in the exchange timezone 
    exchange_time = pd.Timestamp(get_datetime()).tz_convert('US/Eastern')

    # If it's a rebalance day (defined in intialize()) then rebalance:
    if  context.rebalance_date == None or \
        exchange_time >= context.rebalance_date + datetime.timedelta(days=context.rebalance_days):

        # Do nothing if there are open orders:
        if has_orders(context):
            print('has open orders - doing nothing!')
            return

        rebalance(context, data, exchange_time)
    
def rebalance(context, data, exchange_time, threshold = 0.05):  
    """
    For every stock or cash position, if the target percent is off by the threshold
    amount (5% as a default), then place orders to adjust all positions to the target   
    percent of the current portfolio value.
    """
    
    #  if the backtest is in minute mode
    if get_environment('data_frequency') == 'minute':
        # rebalance if we are in the user specified rebalance time-of-day window
        if exchange_time.hour < context.rebalance_hour_start or \
            exchange_time.hour > context.rebalance_hour_end:
                return

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
    # What we should do is first sell the overs and then buy the unders.
    if need_full_rebalance:
        for sid, target in context.ETFs:
            order_target_percent(sid, target)
        log.info("Rebalanced at %s" %  str(exchange_time))
        context.rebalance_date = exchange_time


def has_orders(context):
    # Return true if there are pending orders.
    has_orders = False
    for sec in context.secs:
        orders = get_open_orders(sec)
        if orders:
            for oo in orders:                  
                message = 'Open order for {amount} shares in {stock}'  
                message = message.format(amount=oo.amount, stock=sec)  
                log.info(message)

            has_orders = True
    return has_orders
