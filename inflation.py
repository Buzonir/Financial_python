# -*- coding: utf-8 -*-
"""
Created on Thu Aug 27 15:37:49 2020

@author: Buzoni

This code can calculate de PnL, the DV01 and the Unit Price of
braziliaz Inflation-Linked Bonds

"""
from datetime import datetime, timedelta, date
from bizdays import Calendar

#Getting brazilians holidays from a txt.
FERIADOS = open('C:/Users/buzon/Documents/Python/Arquivos base/Anbima.txt', 'r')
HOLIDAYS = []
for linha in FERIADOS:
    HOLIDAYS.append(linha.strip())
FERIADOS.close()

#Holidays and dates.
cal = Calendar(HOLIDAYS, ['Sunday', 'Saturday'])
dt_today = date.today()
dt_settlement = cal.adjust_previous(date.today()+timedelta(-1))

#Constants.
FORMAT = '%d%m%Y'
CDI = 0.019 #b252 ao ano
CARRY = (1 + CDI)**(1/252)
INDEX_IPCA_INT = 1614.62 #july2000
CUPOM = (1 + 0.06)**(1/2) - 1
CUPOM_31 = (1 + 0.12)**(1/2) - 1

#INPUTS
INDEX_IPCA_RELEASED = 5344.63 #july2020
PREVIEW_IPCA = 0.21
#INPUTS (IF NECESSARY)
INDEX_IPCA_PRIOR = 5344.63
PREVIEW_IPCA_PRIOR = 0.21 #ao mês

def truncate(number, decimal):
    """Truncate a number."""
    num = str(number)
    return float(num[:num.find('.') + decimal + 1])

def get_prior_date(dt_stm=dt_settlement):
    """Get the last day 15."""
    if dt_stm.day >= 15:
        rtn_date = date(dt_stm.year, dt_stm.month, 15)
    else:
        rtn_date = cal.offset(dt_stm, -21).replace(day=15)
    return rtn_date

def get_next_date(dt_stm=dt_settlement):
    """Get the next day 15."""
    if dt_stm.day >= 15:
        rtn_date = cal.offset(dt_stm, 20).replace(day=15)
    else:
        rtn_date = date(dt_stm.year, dt_stm.month, 15)
    return rtn_date

def project_index(coef=INDEX_IPCA_RELEASED, preview=PREVIEW_IPCA, dt_stm=dt_settlement):
    """Project the inflation index."""
    date_prior = cal.adjust_next(get_prior_date(dt_stm))
    date_next = cal.adjust_next(get_next_date(dt_stm))
    bd_gone = cal.bizdays(date_prior, dt_stm)
    bd_between_months = cal.bizdays(date_prior, date_next)
    return coef * (1 + preview/100)**(bd_gone/bd_between_months)

def ratio_ipca(coef=INDEX_IPCA_RELEASED, preview=PREVIEW_IPCA, dt_stm=dt_settlement):
    """Inflation rate projected by preview inflation."""
    return project_index(coef, preview, dt_stm) / INDEX_IPCA_INT

def get_vna(ratio):
    """Get the VNA."""
    return truncate(ratio * 1000, 6)

def get_maturity(asset):
    """Get the maturity of the asset"""
    if asset[:1].upper() == 'B':
        if int(asset[1:3]) % 2 == 0:
            maturity = '150820' + asset[1:3]
        else:
            maturity = '150520' + asset[1:3]
    elif asset[:1].upper() == 'C':
        if int(asset[1:3]) % 2 == 21:
            maturity = '010420' + asset[1:3]
        else:
            maturity = '010120' + asset[1:3]
    else:
        print('Non valid Asset!')
        return None
    return datetime.strptime(maturity, FORMAT)

def create_cash_flow(asset, dt_stm=dt_settlement):
    """Create the cash flow of a NTN-B"""
    cash_flow = []
    maturity = get_maturity(asset)
    maturity = date(maturity.year, maturity.month, maturity.day)
    while maturity > dt_stm:
        cash_flow.append(maturity)
        maturity = cal.adjust_next(cal.offset(maturity, -126).replace(day=15))
    return cash_flow

def quotation_rate(asset, cls_yield, dt_stm=dt_settlement):
    """Get the quotation index."""
    if asset == 'C31':
        cupom = CUPOM_31
    else:
        cupom = CUPOM
    quot_rate = 0
    cls_yield /= 100
    cash_flow = create_cash_flow(asset)
    payments = []
    for maturity_flow in cash_flow:
        bussiness_day = cal.bizdays(dt_stm, maturity_flow)
        if maturity_flow == cash_flow[0]:
            pv_cupom = (1 + cupom) / ((1+cls_yield)**((bussiness_day)/252))
        else:
            pv_cupom = (cupom) / ((1+cls_yield)**((bussiness_day)/252))
        payments.append(pv_cupom)
    for pmt_value in payments:
        quot_rate += pmt_value
    return quot_rate


def unit_price(asset, cls_yield, dt_stm=dt_settlement, preview=PREVIEW_IPCA,
               coef=INDEX_IPCA_RELEASED):
    """Get the PU of the asset."""
    quot_rate = quotation_rate(asset, cls_yield, dt_stm)
    return truncate(get_vna(ratio_ipca(coef=coef, preview=preview, dt_stm=dt_stm)) *
                    quot_rate, 6)

def pnl_b(asset, clsd2_yield, cls_yield, intra=False, dt_stm=dt_settlement):
    """Calculate the PnL of the asset."""
    quantity = int(input('Quantas qtdes foram operadas: '))
    dt_d1 = cal.adjust_previous(dt_stm + timedelta(-1))
    up_d2 = unit_price(asset, clsd2_yield, dt_d1, PREVIEW_IPCA_PRIOR, INDEX_IPCA_PRIOR)
    up_d1 = unit_price(asset, cls_yield, dt_stm)
    if not intra:
        up_d2 *= CARRY
    return (up_d1 - up_d2) * quantity

def dv_b(asset, cls_yield, intra=False, dt_stm=dt_settlement):
    """Calculate the DV01"""
    yield_sh = cls_yield + 0.01
    expo = pnl_b(asset, cls_yield, yield_sh, intra, dt_stm)
    return expo

#Here, I can compare the Unit Price that I calculate and the oficial unit price released
#by ANBIMA.
RND = 2
SETTLEMENT_DAY = dt_today
B21 = round(unit_price('b21', -1.5470, SETTLEMENT_DAY) - 3547.971638, RND)
B22 = round(unit_price('b22', -0.1254, SETTLEMENT_DAY) - 3716.020575, RND)
B23 = round(unit_price('b23', 0.2873, SETTLEMENT_DAY) - 3875.761221, RND)
B24 = round(unit_price('b24', 1.2948, SETTLEMENT_DAY) - 3914.786317, RND)
B25 = round(unit_price('b25', 1.7800, SETTLEMENT_DAY) - 3992.909446, RND)
B26 = round(unit_price('b26', 2.2700, SETTLEMENT_DAY) - 3998.495826, RND)
B28 = round(unit_price('b28', 2.7000, SETTLEMENT_DAY) - 4090.934677, RND)
B30 = round(unit_price('b30', 3.0500, SETTLEMENT_DAY) - 4147.060396, RND)
B35 = round(unit_price('b35', 3.4700, SETTLEMENT_DAY) - 4321.096872, RND)
B40 = round(unit_price('b40', 3.7728, SETTLEMENT_DAY) - 4340.995659, RND)
B45 = round(unit_price('b45', 4.0136, SETTLEMENT_DAY) - 4390.039770, RND)
B50 = round(unit_price('b50', 4.0337, SETTLEMENT_DAY) - 4441.954983, RND)
B55 = round(unit_price('b55', 4.0511, SETTLEMENT_DAY) - 4562.577704, RND)

difs = [B21, B22, B23, B24, B25, B26, B28, B30, B35, B40, B45, B50, B55]
labels = ['B21:', 'B22:', 'B23:', 'B24:', 'B25:', 'B26:', 'B28:',
          'B30:', 'B35:', 'B40:', 'B45:', 'B50:', 'B55:']

i = 0
for ntnb in difs:
    print(labels[i], ntnb)
    i += 1
    