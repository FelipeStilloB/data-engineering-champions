import pandas as pd
from google.cloud import storage
from google.cloud import bigquery
import io

client_bq = bigquery.Client(project='project-1b883040-1b32-4af2-ab0')
dataset_id = "project-1b883040-1b32-4af2-ab0.champions_league"
cliente = storage.Client(project='project-1b883040-1b32-4af2-ab0')
bucket_trusted = cliente.get_bucket("champions_trusted_bucket")
blob_trusted = bucket_trusted.blob("dados_limpos.csv")

#transformando o cvs em "arquivo" na memória para o pandas interpretar
texto_csv = blob_trusted.download_as_string().decode('utf-8')
df = pd.read_csv(io.StringIO(texto_csv))

df_jogados = df.dropna(subset=['winner']).copy()

if df_jogados.empty:
        print('nenhum jogo foi encontrado')
else:

    # 1. Cruzamento dos dados dos times mandantes (Casa)
    stats_casa = (pd.crosstab(df_jogados['homeTeam'], df_jogados['winner'], normalize='index') * 100).round(2)

    # 2. Planificação e renomeação da tabela de mandantes
    stats_casa = stats_casa.rename_axis(None, axis=1).reset_index().rename(columns={
        'homeTeam': 'time', 
        'HOME_TEAM': 'vitorias_em_casa',
        'DRAW': 'empates_em_casa',
        'AWAY_TEAM': 'derrotas_em_casa'
    })

    # 3. Cruzamento dos dados dos times visitantes (Fora)
    stats_fora = (pd.crosstab(df_jogados['awayTeam'], df_jogados['winner'], normalize='index') * 100).round(2)

    # 4. Planificação e renomeação da tabela de visitantes
    stats_fora = stats_fora.rename_axis(None, axis=1).reset_index().rename(columns={
        'awayTeam': 'time',  
        'AWAY_TEAM': 'vitorias_fora',
        'DRAW': 'empates_fora',
        'HOME_TEAM': 'derrotas_fora'
    })

    # 5. União final das duas tabelas
    tabela_final_analise1_por_time = pd.merge(stats_casa, stats_fora, on='time', how='outer').fillna(0)

    vantagem_casa = (df_jogados['winner'].value_counts(normalize=True) * 100).round(2)

    def calcular_vencedor_intervalo(linha):
        if linha ['halftimeHomeScore'] > linha['halftimeAwayScore']:
            return 'HOME_TEAM'
        elif linha ['halftimeHomeScore'] < linha['halftimeAwayScore']:
            return 'AWAY_TEAM'
        else:
            return 'DRAW'

    df_jogados['vencedor_intervalo'] = df_jogados.apply(calcular_vencedor_intervalo, axis = 1)

    #olha os jogos em que um time abriu liderança no primeiro tempo
    jogos_com_lider = df_jogados[df_jogados['vencedor_intervalo'] != 'DRAW'].copy()

    #verificando qual foi a dinamica do placar após o intevalo e até o fim do jogo
    def resultado_do_lider_primeiro_tempo(linha):
        if linha['winner'] == linha['vencedor_intervalo']:
            return 'Manteve Lideranca'
        elif linha['winner'] == 'DRAW':
            return 'Cedeu empate'
        else:
            return 'Virada'

    jogos_com_lider['dinamica_do_jogo'] = jogos_com_lider.apply(resultado_do_lider_primeiro_tempo, axis=1)
    stats_virada = (jogos_com_lider['dinamica_do_jogo'].value_counts(normalize=True)*100).__round__(2)

# Envio dos dados para o bigquery    

    #sobrescreve a tabela
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE"
    )

    #Envia a tabela de desempenho de cada time
    tabela_times_ref = f"{dataset_id}.tb_desempenho_times"
    job_times = client_bq.load_table_from_dataframe(
        tabela_final_analise1_por_time, tabela_times_ref, job_config=job_config
    )
    job_times.result()  
    print(f"Tabela 'tb_desempenho_times' carregada.")

    # 2. Converter Series de dinâmicas para DataFrame e enviar
    df_virada = stats_virada.reset_index()
    df_virada.columns = ['dinamica_jogo', 'porcentagem']

    tabela_virada_ref = f"{dataset_id}.tb_dinamica_segundo_tempo"
    job_virada = client_bq.load_table_from_dataframe(
        df_virada, tabela_virada_ref, job_config=job_config
    )
    job_virada.result()  # Aguarda a conclusão da carga
    print(f"Tabela 'tb_dinamica_segundo_tempo' carregada com sucesso no BigQuery.")



