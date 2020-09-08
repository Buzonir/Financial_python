# -*- coding: utf-8 -*-
"""
Created on Thu Aug 27 15:37:49 2020

@author: Buzoni
"""
from datetime import datetime, timedelta, date
from bizdays import Calendar

FERIADOS = open('C:/Users/buzon/Documents/Python/Arquivos base/Anbima.txt', 'r')
HOLIDAYS = []
for linha in FERIADOS:
    HOLIDAYS.append(linha.strip())
FERIADOS.close()

#Feriados e data base.
cal = Calendar(HOLIDAYS, ['Sunday', 'Saturday'])
dt_hoje = date.today()
dt_base = cal.adjust_previous(date.today()+timedelta(-1))

#Constantes.
FORMATO = '%d%m%Y'
CDI = 0.019 #b252 ao ano
FATOR = (1 + CDI)**(1/252)
INDICE_IPCA_IN = 1614.62 #july2000
CUPOM = (1 + 0.06)**(1/2) - 1
CUPOM_31 = (1 + 0.12)**(1/2) - 1

#INPUTS
INDICE_IPCA_DIVULGADO = 5344.63 #july2020
PREVIA_IPCA = 0.21 #ao mês
#INPUTS (SE NECESSÁRIO)
INDICE_IPCA_ANT = 5344.63
PREVIA_IPCA_ANT = 0.21 #ao mês

def truncar(numero, casas):
    """Truncar um número."""
    num = str(numero)
    return float(num[:num.find('.') + casas + 1])

def busca_data_ant(dt_liq=dt_base):
    """Busca o último dia 15."""
    if dt_liq.day >= 15:
        data = date(dt_liq.year, dt_liq.month, 15)
    else:
        data = cal.offset(dt_liq, -21).replace(day=15)
    return data

def busca_data_prox(dt_liq=dt_base):
    """Busca o próximo dia 15."""
    if dt_liq.day >= 15:
        data = cal.offset(dt_liq, 20).replace(day=15)
    else:
        data = date(dt_liq.year, dt_liq.month, 15)
    return data

def projeta_indice(ind=INDICE_IPCA_DIVULGADO, previa=PREVIA_IPCA, dt_liq=dt_base):
    """Projeta o índice."""
    data_anterior = cal.adjust_next(busca_data_ant(dt_liq))
    data_proxima = cal.adjust_next(busca_data_prox(dt_liq))
    #dc_passado = (dt_liq - data_anterior).days
    #dc_entre_meses = (data_proxima - data_anterior).days
    dc_passado = cal.bizdays(data_anterior, dt_liq)
    dc_entre_meses = cal.bizdays(data_anterior, data_proxima)
    return ind * (1 + previa/100)**(dc_passado/dc_entre_meses)

def fator_ipca(ind=INDICE_IPCA_DIVULGADO, previa=PREVIA_IPCA, dt_liq=dt_base):
    """Fator do IPCA dado o índice projetado"""
    return projeta_indice(ind, previa, dt_liq) / INDICE_IPCA_IN

def puxa_vna(fator):
    """Calcula o VNA."""
    return truncar(fator * 1000, 6)

def busca_vcto(ativo):
    """Acha o vcto dado a B ou a C."""
    if ativo[:1].upper() == 'B':
        if int(ativo[1:3]) % 2 == 0:
            vcto = '150820' + ativo[1:3]
        else:
            vcto = '150520' + ativo[1:3]
    elif ativo[:1].upper() == 'C':
        if int(ativo[1:3]) % 2 == 21:
            vcto = '010420' + ativo[1:3]
        else:
            vcto = '010120' + ativo[1:3]
    else:
        print('Ativo não válido!')
        return None
    return datetime.strptime(vcto, FORMATO)

def cria_fluxo(ativo, dt_liq=dt_base):
    """Cria o fluxo de pagamento."""
    fluxo = []
    vcto = busca_vcto(ativo)
    vcto = date(vcto.year, vcto.month, vcto.day)
    while vcto > dt_liq:
        fluxo.append(vcto)
        #vcto = cal.offset(vcto, -126).replace(day=15)
        vcto = cal.adjust_next(cal.offset(vcto, -126).replace(day=15))
    return fluxo

def fator_cot(ativo, tx_fech, dt_liq=dt_base):
    """Calcula o fator de cotação do Fluxo em questão."""
    if ativo == 'C31':
        cupom = CUPOM_31
    else:
        cupom = CUPOM
    fator_cotacao = 0
    tx_fech /= 100
    fluxo_de_pagamento = cria_fluxo(ativo)
    pgtos = []
    for vcto_fluxo in fluxo_de_pagamento:
        dias_uteis = cal.bizdays(dt_liq, vcto_fluxo)
        if vcto_fluxo == fluxo_de_pagamento[0]:
            pv_cupom = (1 + cupom) / ((1+tx_fech)**((dias_uteis)/252))
        else:
            pv_cupom = (cupom) / ((1+tx_fech)**((dias_uteis)/252))
        pgtos.append(pv_cupom)
    for parcela in pgtos:
        fator_cotacao += parcela
    return fator_cotacao


def preco(ativo, taxa, dt_liq=dt_base, previ=PREVIA_IPCA, ind=INDICE_IPCA_DIVULGADO):
    """Calcula o PU da NTN-B em questão."""
    fator_cotacao = fator_cot(ativo, taxa, dt_liq)
    return truncar(puxa_vna(fator_ipca(ind=ind, previa=previ, dt_liq=dt_liq)) *
                   fator_cotacao, 6)

def pnl_b(ativo, tx_d2, tx_d1, intra=False, dt_liq=dt_base):
    """Calcula o Pnl para uma quantidade de B"""
    qtdes = int(input('Quantas qtdes foram operadas: '))
    dt_d1 = cal.adjust_previous(dt_liq + timedelta(-1))
    pu_d2 = preco(ativo, tx_d2, dt_d1, PREVIA_IPCA_ANT, INDICE_IPCA_ANT)
    pu_d1 = preco(ativo, tx_d1, dt_liq)
    if not intra:
        pu_d2 *= FATOR
    return (pu_d1 - pu_d2) * qtdes

def dv_b(ativo, taxa, intra=False, dt_liq=dt_base):
    """Calcula a exposição da NTN-B"""
    taxa_sh = taxa + 0.01
    expo = pnl_b(ativo, taxa, taxa_sh, intra, dt_liq)
    return expo


RND = 2
DAT_LIQUIDA = dt_hoje
B21 = round(preco('b21', -1.5470, DAT_LIQUIDA) - 3547.971638, RND)
B22 = round(preco('b22', -0.1254, DAT_LIQUIDA) - 3716.020575, RND)
B23 = round(preco('b23', 0.2873, DAT_LIQUIDA) - 3875.761221, RND)
B24 = round(preco('b24', 1.2948, DAT_LIQUIDA) - 3914.786317, RND)
B25 = round(preco('b25', 1.7800, DAT_LIQUIDA) - 3992.909446, RND)
B26 = round(preco('b26', 2.2700, DAT_LIQUIDA) - 3998.495826, RND)
B28 = round(preco('b28', 2.7000, DAT_LIQUIDA) - 4090.934677, RND)
B30 = round(preco('b30', 3.0500, DAT_LIQUIDA) - 4147.060396, RND)
B35 = round(preco('b35', 3.4700, DAT_LIQUIDA) - 4321.096872, RND)
B40 = round(preco('b40', 3.7728, DAT_LIQUIDA) - 4340.995659, RND)
B45 = round(preco('b45', 4.0136, DAT_LIQUIDA) - 4390.039770, RND)
B50 = round(preco('b50', 4.0337, DAT_LIQUIDA) - 4441.954983, RND)
B55 = round(preco('b55', 4.0511, DAT_LIQUIDA) - 4562.577704, RND)

difs = [B21, B22, B23, B24, B25, B26, B28, B30, B35, B40, B45, B50, B55]
labels = ['B21:', 'B22:', 'B23:', 'B24:', 'B25:', 'B26:', 'B28:',
          'B30:', 'B35:', 'B40:', 'B45:', 'B50:', 'B55:']

i = 0
for ntnb in difs:
    print(labels[i], ntnb)
    i += 1
    