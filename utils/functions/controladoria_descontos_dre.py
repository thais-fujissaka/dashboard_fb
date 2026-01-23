def mapeamento_centro_custo(casa, df):
    regras_centro_custo = {
        'CONSUMO GERÊNCIA|CONSUMO GERENCIA|DESCONTO FUNCIONÁRIOS 30%|CONSUMO GERENCIAL|COLABORADOR 30%|COLABORADORES \(30%\)|COLABORADOR \(30%\)|REUNIÃO - EVENTOS|COLABORADORES 30%|REUNIÃO - COMPRAS|30% FÁBRICA DE BARES - CPF': '  -  Alimentação Funcionário',
        'MÚSICOS|REUNIÃO - ARTÍSTICO|TÉCNICO DE SOM|ARTÍSTICO': 'Alimentação e Transporte',
        'REUNIÃO - MKT|REUNIÃO - MARKETING|MARKETING|\[Ação de Marketing\]|PERMUTA|\[Promoção\]': 'Eventos de Marketing',
        '[Promoção] - Jantar Love Cabaret': 'Eventos de Marketing', # Love
        'REUNIÃO - TI|REUNIÃO - T.I.': 'Sistemas Gerais - Operacionais',
        'CONTROLE DE EVENTOS|\[Evento\]': 'FATURAMENTO',
        'PROMOÇÃO': 'Ferramentas de Marketing',
        'FOTOS E VIDEOS MKT': 'Produção Gráfica e Material Institucional',
        'INFLUENCER|INFLUENCERS|\[Ação de Marketing\] - Influencers Delivery': 'Influenciadores',
    }

    # Sobrescreve essas categorias para essas casas
    if casa in ['Blue Note - São Paulo', 'BNSP']:
        regras_centro_custo['REUNIÃO - EVENTOS'] = ('Brindes e Confraternizações - Eventos')

    if casa in ['Girondino ', 'Girondino - CCBB']:
        regras_centro_custo['REUNIÃO - EVENTOS'] = ('Serviços Terceirizados - Eventos')

    if casa in ['Riviera Bar']:
        regras_centro_custo['FOTOS E VIDEOS MKT|\[Ação de Marketing\] - Captação'] = ('Produção Gráfica e Material Institucional')

    if casa in ['Jacaré']:
        regras_centro_custo['Captação|Shooting'] = ('Sessão de Fotos/Captação de Vídeo')

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
        mapeamento_descontos_dre['CONSUMO GERENCIAL|30% ESHOWS - RG'] = ('Descontos - Operação')
        mapeamento_descontos_dre['CONTA ASSINADA'] = ('Desconto - Alimentação Escritório')

    if casa in ['Arcos', 'Orfeu', 'Bar Léo - Centro', 'Jacaré', 'Love Cabaret', 'Riviera Bar']:
        mapeamento_descontos_dre['EVENTO|\[Evento\] - Aniversário Cairê'] = ('FATURAMENTO')

    if casa in ['Bar Brahma - Granja']:
        mapeamento_descontos_dre['30% FÁBRICA DE BARES'] = ('Descontos - Operação')
        mapeamento_descontos_dre['CORTESIA - GERENCIAL'] = ('Desconto - Alimentação Escritório')

    if casa in ['Blue Note - São Paulo', 'BNSP']:
        mapeamento_descontos_dre['ASSINADA SÓCIOS E DIRETORIA|LUCIANO PERES - SOCIO|REUNIÃO - FINANCEIRO|CONTA ASSINADA - FLÁVIO|CONTA ASSINADA - CALAINHO|CONTA ASSINADA - MEGALE|REUNIÃO - T.I.'] = ('Desconto - Alimentação Escritório')
        mapeamento_descontos_dre['CONVÊNIO'] = ('(-) Despesas de Patrocínio')
        mapeamento_descontos_dre['PERMUTA|Members Club Blue Note São Paulo_Categoria Premium|Members Club Blue Note São Paulo_Categoria Comum'] = ('Descontos - Marketing')

    if casa in ['Girondino ', 'Girondino - CCBB']:
        mapeamento_descontos_dre['CARTÃO BLACK - ESHOWS, ESTAFF, FABLAB|CARTÃO BLACK - FB|30% FUNCIONÁRIOS FB|30% ESHOWS - CPF|30% ESHOWS - RG|CONSUMO GERENCIAL|REUNIÃO - EVENTOS|30% FÁBRICA DE BARES'] = ('Descontos - Operação')
        mapeamento_descontos_dre['PROMOÇÕES'] = ('Descontos - Marketing')

    if casa in ['Jacaré']:
        mapeamento_descontos_dre['CLIENTE MASTERCARD|REUNIÃO - EVENTOS|30% DIVERT - CPF|30% ESHOWS - CPF'] = ('Descontos - Operação')

    if casa in ['Love Cabaret']:
        mapeamento_descontos_dre['30 % promoção colaborador|CONTA ASSINADA - JOÃO|CONTA ASSINADA - CAIRÊ|CURADOR|DEVOLUÇÃO PAGAMENTO ANTECIPADO|DESCONTO LOVERS|10% Sócios|MARKETING|ARTÍSTICO|CONTA ASSINADA - LILY'] = ('Descontos - Operação')

    if casa in ['Orfeu']:
        mapeamento_descontos_dre['30% DIVERTI - CPF|10% CONVENIADOS GRUPO ENJOEI'] = ('Descontos - Operação')

    if casa in ['Terraço Notiê']:
        mapeamento_descontos_dre['CONVÊNIO|CLIENTE MASTERCARD|CARTAO MASTER 10%|COTA|Descontos - Marketing|[Reunião] - Eventos'] = ('Desconto - Marketing')
        mapeamento_descontos_dre['CLIENTE - BEM SP|FUNCIONÁRIOS MASTERCARD|30% TERRAÇO NOTIÊ|[Convênio] - 50% BEM SP|[Convênio] - 30% BEM SP|CLIENTE - MASTECARD|COTA - MASTERCARD|[Cota] - MASTERCARD|Descontos - Operação|[Convidados] - Karina Mota|CONTA ASSINADA'] = ('Descontos - Operação')
        mapeamento_descontos_dre['REUNIÃO - AUDITORIA|REUNIÃO - T.I.'] = ('Desconto - Alimentação Escritório')
        mapeamento_descontos_dre['EVENTO|\[Evento\]|PRO_240874 Bem SP-Itau 100 anos'] = ('Faturamento Eventos - Promoções Utilizadas')

    if casa in ['Riviera Bar']:
        mapeamento_descontos_dre['CONTA ASSINANDA - CAIRÊ'] = ('Desconto - Alimentação Escritório')
        mapeamento_descontos_dre['30% DIVERTI - CPF|30% FÁBRICA DE BARES'] = ('Desconto - Operação')
        mapeamento_descontos_dre['\[Evento\]'] = ('Faturamento Eventos - Promoções Utilizadas')

    df_categorias_mes_descontos_dre = df.copy()
    
    for padrao, categoria in regras_descontos_dre.items(): # Mapeamento - Centro de Custo
        condicao = df_categorias_mes_descontos_dre["CATEGORIA"].str.contains(padrao, na=False)    
        df_categorias_mes_descontos_dre.loc[condicao, "Descontos - DRE"] = categoria

    return df_categorias_mes_descontos_dre
