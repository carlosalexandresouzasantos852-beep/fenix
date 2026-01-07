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
    "canal_adv": None,
    "canal_aceitos": None,
    "canal_recusados": None,
    "categoria_analise": None
}


def _carregar_arquivo():
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _salvar_arquivo(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_config(guild_id: int) -> dict:
    data = _carregar_arquivo()
    gid = str(guild_id)

    if gid not in data:
        data[gid] = CONFIG_PADRAO.copy()
        _salvar_arquivo(data)

    return data[gid]


def set_config(guild_id: int, chave: str, valor):
    data = _carregar_arquivo()
    gid = str(guild_id)

    if gid not in data:
        data[gid] = CONFIG_PADRAO.copy()

    data[gid][chave] = valor
    _salvar_arquivo(data)