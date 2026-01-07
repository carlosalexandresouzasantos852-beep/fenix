import json
import os

CONFIG_PATH = "meu_bot_farm/data/config_farm.json"

CONFIG_PADRAO = {
    "metas": {
        "Aviãozinho": 50,
        "Membro": 100,
        "Recrutador": 200,
        "Gerente": 300
    },
    "canal_adv": 0,
    "canal_aceitos": 0,
    "canal_recusados": 0,
    "categoria_analise": 0
}


def garantir_config():
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(CONFIG_PADRAO, f, indent=4, ensure_ascii=False)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_config(config: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)