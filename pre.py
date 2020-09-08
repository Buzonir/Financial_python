# -*- coding: utf-8 -*-
"""
Created on Wed Aug 26 21:36:06 2020

@author: Buzoni
"""
#Pacotes.
from datetime import datetime, timedelta
from bizdays import Calendar

#Puxando o TXT contendo os feriados da ANBIMA.
FERIADOS = open('C:/Users/buzon/Documents/Python/Arquivos base/Anbima.txt', 'r')
HOLIDAYS = []
for linha in FERIADOS:
    HOLIDAYS.append(linha[:10])
FERIADOS.close()

#Feriados e data base.
cal = Calendar(HOLIDAYS, ['Sunday', 'Saturday'])
dt_hoje = datetime.today()
dt_base = cal.adjust_previous(datetime.today()+timedelta(-1))

#Constantes.
FORMATO = '%d%m%Y'
COD_BBG = 'OD'
COD_BMF = 'DI1'

#Vencimentos BM&F.
bmef = {'F':'01', 'G':'02', 'H':'03', 'J':'04', 'K':'05', 'M':'06',
        'N':'07', 'Q':'08', 'U':'09', 'V':'10', 'X':'11', 'Z':'12'}

#CDI
CDI = 0.019 #b252 ao ano
FATOR = (1 + CDI)**(1/252)


def trata_data(data):
    """Tratando a data do vencimento. Formato: ddmmaaaa"""
    if data[:2].upper() == COD_BBG:
        data = '01' + bmef[data[2].upper()] + "20" + data[3:]
    elif data[:3].upper() == COD_BMF:
        data = '01' + bmef[data[3].upper()] + "20" + data[4:]
    return cal.adjust_next(datetime.strptime(data, FORMATO))

def dias_entre_datas(data, base, data_inicio=dt_base):
    """Dias entre datas - úteis ou corridos"""
    if base == 252:
        data = cal.bizdays(data_inicio, data) #b252 -> du
    elif base == 360:
        data = (data - data_inicio).days #b360 -> dc
    else:
        print('Base inválida!')
        return False
    return data

def carrega(value, intraday=False):
    """Carrega o value"""
    if not intraday:
        value *= FATOR
    return value

def pv_di(taxa, dias_uteis):
    """Trazendo o DI pra valor presente"""
    taxa /= 100
    return 100000/((1+taxa)**((dias_uteis)/252))

def shft_taxa(taxa, bps=1):
    """Eleva a taxa a em x bps"""
    taxa += bps/100
    return taxa

def pnl_di(vcto, qtdes, tx_d2, tx_d1, intra=False):
    """Calcula o PnL de Futuro de Juros."""
    vcto = trata_data(vcto)
    dias_entre = dias_entre_datas(vcto, 252)
    dias_entre_d1 = dias_entre + 1
    if intra:
        dias_entre_d1 = dias_entre
    #Present Values
    pv_1 = pv_di(tx_d1, dias_entre)
    pv_2 = carrega(pv_di(tx_d2, dias_entre_d1), intra)
    #PnL
    pnl = -(pv_1 - pv_2) * qtdes
    #Output
    return round(pnl, 2)
    
def dv_di(vcto, qtdes, taxa):
    """Calcula o DV01"""
    taxa_sh = shft_taxa(taxa)
    vcto = trata_data(vcto)
    dias_uteis = dias_entre_datas(vcto, 252, dt_hoje)
    p_value = pv_di(taxa, dias_uteis)
    p_value_sh = pv_di(taxa_sh, dias_uteis)
    dv01 = -(p_value_sh - p_value) / FATOR * qtdes
    return round(dv01, 2)

teste = dv_di('odf21', -22130, 1.98)
print(-73557.13, 'reais.')
print(teste, 'reais.')
print(round(teste + 73557.13, 2), 'reais de diferença.', end='\n\n')

teste = dv_di('odf24', 9500, 5.19)
print(253509.1, 'reais.')
print(teste, 'reais.')
print(round(teste - 253509.1, 2), 'reais de diferença.')