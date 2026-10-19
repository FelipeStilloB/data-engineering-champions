import json
import pandas as pd
from google.cloud import storage

cliente = storage.Client(project='project-1b883040-1b32-4af2-ab0')
bucket = cliente.get_bucket("champions_raw_bucket")
blob = bucket.blob("dados.json")

texto_json = blob.download_as_string()
dados_dicionario = json.loads(texto_json)

df = pd.DataFrame(dados_dicionario['matches'])

#Aqui printei as colunas da tabela para poder escolher com quais iria trabalhar
print("Formato da tabela:", df.shape)
print("Colunas:", df.columns.tolist())

df = df.drop_duplicates(subset=['id'])

#Limpeza dos dicionários e criação de cada coluna para que tenhamos os dados necessários para análise de forma mais limpa
df['homeTeam'] = df['homeTeam'].apply(lambda x: x['name'])
df['awayTeam'] = df['awayTeam'].apply(lambda x: x['name'])
df['fulltimeHomeScore'] = df['score'].apply(lambda x: x['fullTime']['home'])
df['fulltimeAwayScore'] = df['score'].apply(lambda x: x['fullTime']['away'])
df['halftimeHomeScore'] = df['score'].apply(lambda x: x['halfTime']['home'])
df['halftimeAwayScore'] = df['score'].apply(lambda x: x['halfTime']['away'])
df['winner'] = df['score'].apply(lambda x: x['winner'])

#Aqui estão as colunas que foram escolhidas pensando que usaremos apenas os dados da champions e alguns não são tão relevantes
df_limpo = df[['id','utcDate','status','homeTeam','awayTeam','fulltimeHomeScore','fulltimeAwayScore', 'halftimeHomeScore', 'halftimeAwayScore', 'winner']]
print("Tabela Limpa:", df_limpo.shape)


#Aqui os dados são transformados em csv para que possam ser enviados ao GCP e é feito o upload deles pra um novo bucke sem duplicatas, sendo esse chamado de trusted
dados_csv = df_limpo.to_csv(index=False)
bucket_trusted = cliente.get_bucket("champions_trusted_bucket")
csv_trusted= bucket_trusted.blob("dados_limpos.csv")
csv_trusted.upload_from_string(dados_csv, content_type="text/csv")

