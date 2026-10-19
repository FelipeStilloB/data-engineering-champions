import requests
import json
import os 
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

def ingerir_dados_futebol(request):
    url = "https://api.football-data.org/v4/competitions/CL/matches"
    key = {"X-auth-Token" : API_TOKEN}

    resp = requests.get(url, headers = key) 

    if resp.status_code == 200:
        dados = resp.json()
        cliente = storage.Client(project='project-1b883040-1b32-4af2-ab0')
        raw_bucket = cliente.get_bucket("champions_raw_bucket")
        raw_file = raw_bucket.blob("dados.json")
        raw_file.upload_from_string(json.dumps(dados), content_type='application/json')
        return "Dados carregados no bucket", 200

    else:
        return("Erro ao realizar busca:", resp.status_code)

print(ingerir_dados_futebol(None))