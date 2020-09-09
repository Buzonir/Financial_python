# -*- coding: utf-8 -*-
"""
Created on Wed Aug 26 21:36:06 2020

@author: Buzoni
"""

from datetime import datetime, timedelta
from bizdays import Calendar

#Holidays calendar from ANBIMA.
FERIADOS = open('C:/Users/buzon/Documents/Python/Arquivos base/Anbima.txt', 'r')
HOLIDAYS = []
for row in FERIADOS:
    HOLIDAYS.append(row.strip())
FERIADOS.close()

#Holidays and settlement day.
cal = Calendar(HOLIDAYS, ['Sunday', 'Saturday'])
dt_today = datetime.today()
dt_settlement = cal.adjust_previous(datetime.today()+timedelta(-1))

#Constants.
FORMAT = '%d%m%Y'
COD_BBG = 'OD'
COD_BMF = 'DI1'

#Maturities of BM&F.
bmef = {'F':'01', 'G':'02', 'H':'03', 'J':'04', 'K':'05', 'M':'06',
        'N':'07', 'Q':'08', 'U':'09', 'V':'10', 'X':'11', 'Z':'12'}

#CDI
CDI = 0.019 #b252
CARRY = (1 + CDI)**(1/252)


def get_maturity(stm_date):
    """Getting the maturity. Format: ddmmaaaa"""
    if stm_date[:2].upper() == COD_BBG:
        stm_date = '01' + bmef[stm_date[2].upper()] + "20" + stm_date[3:]
    elif stm_date[:3].upper() == COD_BMF:
        stm_date = '01' + bmef[stm_date[3].upper()] + "20" + stm_date[4:]
    return cal.adjust_next(datetime.strptime(stm_date, FORMAT))

def between_dates(maturity, base, stm_date=dt_settlement):
    """Number of days - working days or not"""
    if base == 252:
        return_date = cal.bizdays(stm_date, maturity) #b252
    elif base == 360:
        return_date = (maturity - stm_date).days #b360
    else:
        print('Invalid Base!')
        return False
    return return_date

def carry_unit_price(value, intraday=False):
    """Considering the carry"""
    if not intraday:
        value *= CARRY
    return value

def pv_di(cls_yield, working_days):
    """Calculating the present value"""
    cls_yield /= 100
    return 100000/((1+cls_yield)**((working_days)/252))

def shft_yield(cls_yield, bps=1):
    """Return the yield plus 1bps"""
    cls_yield += bps/100
    return cls_yield

def pnl_di(maturity, quantity, clsd2_yield, cls_yield, intra=False):
    """Getting the PnL of the DI1 future"""
    maturity = get_maturity(maturity)
    btwn_days = between_dates(maturity, 252)
    btwn_days_d1 = btwn_days + 1
    if intra:
        btwn_days_d1 = btwn_days
    #Present Values
    pv_1 = pv_di(cls_yield, btwn_days)
    pv_2 = carry_unit_price(pv_di(clsd2_yield, btwn_days_d1), intra)
    #PnL
    pnl = -(pv_1 - pv_2) * quantity
    #Output
    return round(pnl, 2)

def dv_di(maturity, quantity, cls_yield):
    """Getting the DV01"""
    yield_sh = shft_yield(cls_yield)
    maturity = get_maturity(maturity)
    working_days = between_dates(maturity, 252, dt_today)
    p_value = pv_di(cls_yield, working_days)
    p_value_sh = pv_di(yield_sh, working_days)
    dv01 = -(p_value_sh - p_value) / CARRY * quantity
    return round(dv01, 2)
