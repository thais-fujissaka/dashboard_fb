import pandas as pd


def mapeamento_centro_custo(casa, df):
    regras_centro_custo = {
        'CONSUMO GERÊNCIA|CONSUMO GERENCIA|DESCONTO FUNCIONÁRIOS 30%|CONSUMO GERENCIAL|COLABORADOR 30%|COLABORADORES \(30%\)|COLABORADOR \(30%\)|REUNIÃO - EVENTOS|COLABORADORES 30%|REUNIÃO - COMPRAS': '  -  Alimentação Funcionário',
        'MÚSICOS|REUNIÃO - ARTÍSTICO|TÉCNICO DE SOM|ARTÍSTICO': 'Alimentação e Transporte',
        'REUNIÃO - MKT|REUNIÃO - MARKETING|MARKETING|\[Ação de Marketing\]|PERMUTA|\[Promoção\]': 'Eventos de Marketing',
        # '[Promoção] - Jantar Love Cabaret': 'Eventos de Marketing', # Love
        'REUNIÃO - TI|REUNIÃO - T.I.': 'Sistemas Gerais - Operacionais',
        'CONTROLE DE EVENTOS|\[Evento\]': 'FATURAMENTO',
        'PROMOÇÃO': 'Ferramentas de Marketing',
        'FOTOS E VIDEOS MKT': 'Produção Gráfica e Material Institucional',
        'INFLUENCER|INFLUENCERS|\[Ação de Marketing\] - Influencers Delivery': 'Influenciadores', # Granja
    }

    # Sobrescreve essas categorias para essas casas
    if casa in ['Blue Note - São Paulo', 'BNSP']:
        regras_centro_custo['REUNIÃO - EVENTOS'] = ('Brindes e Confraternizações - Eventos')

    if casa in ['Girondino ', 'Girondino - CCBB']:
        regras_centro_custo['REUNIÃO - EVENTOS'] = ('Serviços Terceirizados - Eventos')

    if casa in ['Jacaré']:
        regras_centro_custo['Captação|Shooting|FOTOS E VIDEOS MKT'] = ('Sessão de Fotos/Captação de Vídeo')
    
    if casa in ['Riviera Bar']:
        regras_centro_custo['\[Ação de Marketing\] - Captação'] = ('Produção Gráfica e Material Institucional')

    df_categorias_mes_centro_custo = df.copy()
    
    for padrao, categoria in regras_centro_custo.items(): # Mapeamento - Centro de Custo
        condicao = df_categorias_mes_centro_custo["CATEGORIA"].str.contains(padrao, na=False)    
        df_categorias_mes_centro_custo.loc[condicao, "Centro de Custo"] = categoria

    return df_categorias_mes_centro_custo

def mapeamento_descontos_dre(casa, df):
    regras_descontos_dre = {
        'EVENTO': 'Faturamento - Eventos',
        'COTA|OPERAÇÕES|REUNIÃO|MÚSICOS|REUNIÃO - ARTÍSTICO|REUNIÃO - TI|OUTROS|CLIENTE - DUO GOURMET|ASSINADA SÓCIOS E DIRETOR|ASSINADA SÓCIO FACUNDO|CORTESIA|CONVÊNIO|REUNIÃO - SUPRIMENTOS|RETIRADA / REDUÇÃO DE SERVIÇO|TREINAMENTO|LUCIANO PERES - SOCIO|LUCIANO PERES - SÓCIO|REUNIÃO - FABLAB|TESTE|TÉCNICO DE SOM|POLÍCIA|REUNIÃO - OPERAÇÕES|SEM JUSTIFICATIVA|PROMOÇÕES|OPERACIONAL|SERVIÇO|PERMUTA|OUTRO|REUNIÃO - OPERACIONAL|CONTA ASSINADA|10% LOJISTAS - CPF|10% CONVENIADOS - CPF|PROMOO': 'Descontos - Operação',
        'CONSUMO GERÊNCIA|CONSUMO GERENCIAL|DESCONTO FUNCIONÁRIO|CONSUMO COLABORADOR|COLABORADOR 30%|COLABORADORES \(30%\)|COLABORADOR \(30%\)|REUNIÃO - EVENTOS|COLABORADORES 30%|REUNIÃO - COMPRAS|30% FÁBRICA DE BARES|CARTÃO BLACK - ESHOWS, ESTAFF, FABLAB|CARTÃO BLACK - FB|30% FUNCIONÁRIOS FB|30% ESHOWS - CPF|30% ESHOWS - RG|30% DIVERTI - CPF|DIVERT 30%|30% FB - ORFEU|CONTA ASSINADA - FDB|CONTA ASSINADA - FACUNDO|REUNIÃO - EVENTOS|REUNIÃO - COMPRAS|30% FB - ORFEU': 'Desconto - Alimentação Escritório',
        'REUNIÃO - MKT|REUNIÃO - MARKETING|MARKETING|PROMOÇÃO|FOTOS E VIDEOS MKT|INFLUENCER|\[Ação de Marketing\]': 'Descontos - Marketing',
        '\[Evento\]|PACOTE': 'Faturamento de Eventos - Promoções Utilizadas',
        '\[Evento\] - Confraternização FB': 'Descontos - Promoções Utilizadas' # Bar Léo
    }

    # Sobrescreve essas categorias para essas casas
    if casa in ['Bar Brahma - Centro']:
        regras_descontos_dre['CONSUMO GERENCIAL|30% ESHOWS - RG'] = ('Descontos - Operação')
        regras_descontos_dre['CONTA ASSINADA'] = ('Desconto - Alimentação Escritório')

    if casa in ['Arcos', 'Orfeu', 'Bar Léo - Centro', 'Jacaré', 'Love Cabaret', 'Riviera Bar']:
        regras_descontos_dre['EVENTO|\[Evento\] - Aniversário Cairê'] = ('FATURAMENTO')

    if casa in ['Bar Brahma - Granja']:
        regras_descontos_dre['30% FÁBRICA DE BARES'] = ('Descontos - Operação')
        regras_descontos_dre['CORTESIA - GERENCIAL'] = ('Desconto - Alimentação Escritório')

    if casa in ['Blue Note - São Paulo', 'BNSP']:
        regras_descontos_dre['ASSINADA SÓCIOS E DIRETORIA|LUCIANO PERES - SOCIO|REUNIÃO - FINANCEIRO|CONTA ASSINADA - FLÁVIO|CONTA ASSINADA - CALAINHO|CONTA ASSINADA - MEGALE|REUNIÃO - T.I.'] = ('Desconto - Alimentação Escritório')
        regras_descontos_dre['CONVÊNIO'] = ('(-) Despesas de Patrocínio')
        regras_descontos_dre['PERMUTA|Members Club Blue Note São Paulo_Categoria Premium|Members Club Blue Note São Paulo_Categoria Comum'] = ('Descontos - Marketing')

    if casa in ['Girondino ', 'Girondino - CCBB']:
        regras_descontos_dre['CARTÃO BLACK - ESHOWS, ESTAFF, FABLAB|CARTÃO BLACK - FB|30% FUNCIONÁRIOS FB|30% ESHOWS - CPF|30% ESHOWS - RG|CONSUMO GERENCIAL|REUNIÃO - EVENTOS|30% FÁBRICA DE BARES'] = ('Descontos - Operação')
        regras_descontos_dre['PROMOÇÕES'] = ('Descontos - Marketing')

    if casa in ['Jacaré']:
        regras_descontos_dre['CLIENTE MASTERCARD|REUNIÃO - EVENTOS|30% DIVERT - CPF|30% ESHOWS - CPF'] = ('Descontos - Operação')

    if casa in ['Love Cabaret']:
        regras_descontos_dre['30 % promoção colaborador|CONTA ASSINADA - JOÃO|CONTA ASSINADA - CAIRÊ|CURADOR|DEVOLUÇÃO PAGAMENTO ANTECIPADO|DESCONTO LOVERS|10% Sócios|MARKETING|ARTÍSTICO|CONTA ASSINADA - LILY'] = ('Descontos - Operação')

    if casa in ['Orfeu']:
        regras_descontos_dre['30% DIVERTI - CPF|10% CONVENIADOS GRUPO ENJOEI'] = ('Descontos - Operação')

    if casa in ['Terraço Notiê']:
        regras_descontos_dre['CONVÊNIO|CLIENTE MASTERCARD|CARTAO MASTER 10%|COTA|Descontos - Marketing|[Reunião] - Eventos'] = ('Desconto - Marketing')
        regras_descontos_dre['CLIENTE - BEM SP|FUNCIONÁRIOS MASTERCARD|30% TERRAÇO NOTIÊ|[Convênio] - 50% BEM SP|[Convênio] - 30% BEM SP|CLIENTE - MASTECARD|COTA - MASTERCARD|[Cota] - MASTERCARD|Descontos - Operação|[Convidados] - Karina Mota|CONTA ASSINADA'] = ('Descontos - Operação')
        regras_descontos_dre['REUNIÃO - AUDITORIA|REUNIÃO - T.I.'] = ('Desconto - Alimentação Escritório')
        regras_descontos_dre['EVENTO|\[Evento\]|PRO_240874 Bem SP-Itau 100 anos'] = ('Faturamento Eventos - Promoções Utilizadas')

    if casa in ['Riviera Bar']:
        regras_descontos_dre['CONTA ASSINANDA - CAIRÊ'] = ('Desconto - Alimentação Escritório')
        regras_descontos_dre['30% DIVERTI - CPF|30% FÁBRICA DE BARES'] = ('Desconto - Operação')
        # regras_descontos_dre['\[Evento\]'] = ('Faturamento Eventos - Promoções Utilizadas')

    df_categorias_mes_descontos_dre = df.copy()
    
    for padrao, categoria in regras_descontos_dre.items(): # Mapeamento - Centro de Custo
        condicao = df_categorias_mes_descontos_dre["CATEGORIA"].str.contains(padrao, na=False)    
        df_categorias_mes_descontos_dre.loc[condicao, "Descontos - DRE"] = categoria

    return df_categorias_mes_descontos_dre


def filtra_df(df_descontos, df_promocoes, mes, ano, id_casa):
    df_descontos_filtrado = df_descontos[
        (df_descontos['DATA'].dt.month == int(mes)) &
        (df_descontos['DATA'].dt.year == ano)
    ].copy()

    df_promocoes_filtrado = df_promocoes[
        (df_promocoes['DATA'].dt.month == int(mes)) &
        (df_promocoes['DATA'].dt.year == ano)
    ].copy()

    # Se selecionou uma casa específica, filtra
    if id_casa is not None:
        df_descontos_filtrado = df_descontos_filtrado[
            df_descontos_filtrado['FK_CASA'] == id_casa
        ].copy()

        df_promocoes_filtrado = df_promocoes_filtrado[
            df_promocoes_filtrado['FK_CASA'] == id_casa
        ].copy()

    return df_descontos_filtrado, df_promocoes_filtrado


def prepara_consolidado(df_descontos_filtrado, df_promocoes_filtrado):
    # Descontos - soma total por categoria
    df_descontos_mes = df_descontos_filtrado.groupby(['FK_CASA', 'DATA', 'CATEGORIA'], as_index=False).agg({
        'DESCONTO': 'sum',
        'DATA': 'first',
    })

    # Promoções - soma total por categoria
    df_promocoes_mes = df_promocoes_filtrado.groupby(['FK_CASA', 'DATA', 'PROMOCAO'], as_index=False).agg({
        'DESCONTO_TOTAL': 'sum',
        'DATA': 'first',
    })
    
    df_promocoes_mes = df_promocoes_mes.rename(columns={
        'PROMOCAO': 'CATEGORIA',
        'DESCONTO_TOTAL': 'DESCONTO'
    })

    df_concatenado = pd.concat([df_descontos_mes, df_promocoes_mes]).reset_index(drop=True)

    return df_descontos_mes, df_promocoes_mes, df_concatenado

