import pandas as pd


def mapeamento_centro_custo(casa, df):
    regras_globais_centro_custo = {
        'CONSUMO GERÊNCIA|CONSUMO GERENCIA|DESCONTO FUNCIONÁRIOS 30%|CONSUMO GERENCIAL|COLABORADOR 30%|COLABORADORES \(30%\)|COLABORADOR \(30%\)|REUNIÃO - EVENTOS|COLABORADORES 30%|REUNIÃO - COMPRAS': '  -  Alimentação Funcionário',
        'MÚSICOS|REUNIÃO - ARTÍSTICO|TÉCNICO DE SOM|ARTÍSTICO': 'Alimentação e Transporte',
        'REUNIÃO - MKT|REUNIÃO - MARKETING|MARKETING|\[Ação de Marketing\] - Captação|\[Ação de Marketing\] - Influencer|PERMUTA': 'Eventos de Marketing', # Não considero [Ação de Marketing]
        'REUNIÃO - TI|REUNIÃO - T.I.': 'Sistemas Gerais - Operacionais',
        'CONTROLE DE EVENTOS': 'FATURAMENTO', # Não considero [Evento]
        'PROMOÇÃO': 'Ferramentas de Marketing',
        'FOTOS E VIDEOS MKT': 'Produção Gráfica e Material Institucional',
        'INFLUENCER|INFLUENCERS|\[Ação de Marketing\] - Influencers Delivery': 'Influenciadores', # Granja
    }

    # Sobrescreve essas categorias para essas casas
    regras_por_casa_centro_custo = {
        (110, 131): {  # Blue Note - São Paulo, BNSP
            'REUNIÃO - EVENTOS': 'Brindes e Confraternizações - Eventos'
        },

        (156, 160): {  # Girondino, CCBB
            'REUNIÃO - EVENTOS': 'Serviços Terceirizados - Eventos'
        },

        (105,): {  # Jacaré
            'Captação|Shooting|FOTOS E VIDEOS MKT': 'Sessão de Fotos/Captação de Vídeo'
        },

        (115,): {  # Riviera Bar
            '\[Ação de Marketing\] - Captação': 'Produção Gráfica e Material Institucional'
        },

        (104,): { # Orfeu
            '\[Ação de Marketing\] - Captação': None
        }
    }

    df_categorias_mes_centro_custo = df.copy()
    
    # Aplica regras globais
    for padrao, categoria in regras_globais_centro_custo.items():
        cond = df_categorias_mes_centro_custo["CATEGORIA"].str.contains(padrao, na=False, regex=True)
        df_categorias_mes_centro_custo.loc[cond, "Centro de Custo"] = categoria

    # Aplica regras específicas por casa
    for casas, regras in regras_por_casa_centro_custo.items():
        df_casa = df_categorias_mes_centro_custo["FK_CASA"].isin(casas)

        for padrao, categoria in regras.items():
            cond = df_categorias_mes_centro_custo["CATEGORIA"].str.contains(padrao, na=False, regex=True)
            df_categorias_mes_centro_custo.loc[df_casa & cond, "Centro de Custo"] = categoria
    
    return df_categorias_mes_centro_custo


def mapeamento_descontos_dre(casa, df):
    regras_globais_descontos_dre = {
        'EVENTO': 'Faturamento - Eventos',
        'COTA|OPERAÇÕES|REUNIÃO|MÚSICOS|REUNIÃO - ARTÍSTICO|REUNIÃO - TI|OUTROS|CLIENTE - DUO GOURMET|ASSINADA SÓCIOS E DIRETOR|ASSINADA SÓCIO FACUNDO|CORTESIA|CONVÊNIO|REUNIÃO - SUPRIMENTOS|RETIRADA / REDUÇÃO DE SERVIÇO|TREINAMENTO|LUCIANO PERES - SOCIO|LUCIANO PERES - SÓCIO|REUNIÃO - FABLAB|TESTE|TÉCNICO DE SOM|POLÍCIA|REUNIÃO - OPERAÇÕES|SEM JUSTIFICATIVA|PROMOÇÕES|OPERACIONAL|SERVIÇO|PERMUTA|OUTRO|REUNIÃO - OPERACIONAL|CONTA ASSINADA|10% LOJISTAS - CPF|10% CONVENIADOS - CPF|PROMOO': 'Descontos - Operação',
        'CONSUMO GERÊNCIA|CONSUMO GERENCIAL|DESCONTO FUNCIONÁRIO|CONSUMO COLABORADOR|COLABORADOR 30%|COLABORADORES \(30%\)|COLABORADOR \(30%\)|REUNIÃO - EVENTOS|COLABORADORES 30%|REUNIÃO - COMPRAS|30% FÁBRICA DE BARES|CARTÃO BLACK - ESHOWS, ESTAFF, FABLAB|CARTÃO BLACK - FB|30% FUNCIONÁRIOS FB|30% ESHOWS - CPF|30% ESHOWS - RG|30% DIVERTI - CPF|DIVERT 30%|30% FB - ORFEU|CONTA ASSINADA - FDB|CONTA ASSINADA - FACUNDO|REUNIÃO - EVENTOS|REUNIÃO - COMPRAS|30% FB - ORFEU': 'Desconto - Alimentação Escritório',
        'REUNIÃO - MKT|REUNIÃO - MARKETING|MARKETING|PROMOÇÃO|FOTOS E VIDEOS MKT|INFLUENCER|\[Ação de Marketing\]': 'Descontos - Marketing',
        '\[Event\]|\[Evento\]|PACOTE': 'Faturamento de Eventos - Promoções Utilizadas',
        '\[Evento\] - Confraternização FB': 'Descontos - Promoções Utilizadas' # Bar Léo
    }

    # Sobrescreve essas categorias para essas casas
    regras_por_casa_descontos_dre = {
        (122, 104, 116, 105, 128, 115): {  # Arcos, Orfeu, Bar Léo - Centro, Jacaré, Love Cabaret, Riviera Bar
            'EVENTO|\[Evento\] - Aniversário Cairê': 'FATURAMENTO'
        },

        (114,): {  # Bar Brahma - Centro
            'CONSUMO GERENCIAL|30% ESHOWS - RG': 'Descontos - Operação',
            'CONTA ASSINADA': 'Desconto - Alimentação Escritório'
        },

        (148,): {  # Bar Brahma - Granja
            '30% FÁBRICA DE BARES': 'Descontos - Operação',
            'CORTESIA - GERENCIAL': 'Desconto - Alimentação Escritório'
        },

        (110, 131): { # Blue Note - São Paulo
            'ASSINADA SÓCIOS E DIRETORIA|LUCIANO PERES - SOCIO|REUNIÃO - FINANCEIRO|CONTA ASSINADA - FLÁVIO|CONTA ASSINADA - CALAINHO|CONTA ASSINADA - MEGALE|REUNIÃO - T.I.': 'Desconto - Alimentação Escritório', 
            'CONVÊNIO': '(-) Despesas de Patrocínio',
            'PERMUTA|Members Club Blue Note São Paulo_Categoria Premium|Members Club Blue Note São Paulo_Categoria Comum': 'Descontos - Marketing'
        },

        (156, 160): { # Girondino
            'CARTÃO BLACK - ESHOWS, ESTAFF, FABLAB|CARTÃO BLACK - FB|30% FUNCIONÁRIOS FB|30% ESHOWS - CPF|30% ESHOWS - RG|CONSUMO GERENCIAL|REUNIÃO - EVENTOS|30% FÁBRICA DE BARES': 'Descontos - Operação',
            'PROMOÇÕES': 'Descontos - Marketing'
        },

        (105,): { # Jacaré
            'CLIENTE MASTERCARD|REUNIÃO - EVENTOS|30% DIVERT - CPF|30% ESHOWS - CPF': 'Descontos - Operação'
        },

        (128,): { # Love Cabaret
            '30 % promoção colaborador|CONTA ASSINADA - JOÃO|CONTA ASSINADA - CAIRÊ|CURADOR|DEVOLUÇÃO PAGAMENTO ANTECIPADO|DESCONTO LOVERS|10% Sócios|MARKETING|ARTÍSTICO|CONTA ASSINADA - LILY': 'Descontos - Operação'
        },

        (104,): { # Orfeu
            '30% DIVERTI - CPF|10% CONVENIADOS GRUPO ENJOEI': 'Descontos - Operação'
        },

        (162,): {  # Terraço Notiê
            'CONVÊNIO|CLIENTE MASTERCARD|CARTAO MASTER 10%|COTA|Descontos - Marketing|\[Reunião\] - Eventos|\[Reunião\] - Marketing': 'Desconto - Marketing',
            'CLIENTE - BEM SP|FUNCIONÁRIOS MASTERCARD|30% TERRAÇO NOTIÊ|\[Convênio\] - 50% BEM SP|\[Convênio\] - 30% BEM SP|CLIENTE - MASTECARD|COTA - MASTERCARD|\[Cota\] - MASTERCARD|Descontos - Operação|\[Convidados\] - Karina Mota|CONTA ASSINADA|\[BemSP\]': 'Descontos - Operação',
            'REUNIÃO - AUDITORIA|REUNIÃO - T.I.': 'Desconto - Alimentação Escritório',
            'EVENTO|\[Evento\]|PRO_240874 Bem SP-Itau 100 anos': 'Faturamento Eventos - Promoções Utilizadas'
        },

        (115,): { # Riviers Bar
            'CONTA ASSINANDA - CAIRÊ': 'Desconto - Alimentação Escritório',
            '30% DIVERTI - CPF|30% FÁBRICA DE BARES': 'Desconto - Operação',
            '\[Evento\]': 'Faturamento Eventos - Promoções Utilizadas'
        }
    }

    df_categorias_mes_descontos_dre = df.copy()
    
    # Aplica regras globais
    for padrao, categoria in regras_globais_descontos_dre.items():
        cond = df_categorias_mes_descontos_dre["CATEGORIA"].str.contains(padrao, na=False, regex=True)
        df_categorias_mes_descontos_dre.loc[cond, "Descontos - DRE"] = categoria

    # Aplica regras específicas por casa
    for casas, regras in regras_por_casa_descontos_dre.items():
        df_casa = df_categorias_mes_descontos_dre["FK_CASA"].isin(casas)

        for padrao, categoria in regras.items():
            cond = df_categorias_mes_descontos_dre["CATEGORIA"].str.contains(padrao, na=False, regex=True)
            df_categorias_mes_descontos_dre.loc[df_casa & cond, "Descontos - DRE"] = categoria
    
    return df_categorias_mes_descontos_dre


def filtra_df(df_descontos, df_promocoes, mes, ano, id_casa):
    df_descontos_filtrado = df_descontos.copy()
    df_descontos_filtrado['DATA'] = pd.to_datetime(df_descontos_filtrado['DATA'], errors='coerce')
    df_descontos_filtrado = df_descontos_filtrado[
        (df_descontos_filtrado['DATA'].dt.month == int(mes)) &
        (df_descontos_filtrado['DATA'].dt.year == ano)
    ].copy()

    df_promocoes_filtrado = df_promocoes.copy()
    df_promocoes_filtrado['DATA'] = pd.to_datetime(df_promocoes_filtrado['DATA'], errors='coerce')
    df_promocoes_filtrado = df_promocoes_filtrado[
        (df_promocoes_filtrado['DATA'].dt.month == int(mes)) &
        (df_promocoes_filtrado['DATA'].dt.year == ano)
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

