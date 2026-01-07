import json
import os

CONFIG_PATH = "meu_bot_farm/data/config_farm.json"

CONFIG_PADRAO = {
    # ======================
    # METAS POR CARGO
    # ======================
    "metas": {
        "Aviãozinho": 50,
        "Membro": 100,
        "Recrutador": 200,
        "Gerente": 300
    },

    # ======================
    # CANAIS
    # ======================
    "canal_adv": None,        # ID do canal de ADV automático
    "canal_aceitos": None,    # ID do canal de entregas aceitas
    "canal_recusados": None,  # ID do canal de entregas recusadas

    # ======================
    # CATEGORIAS
    # ======================
    "categoria_analise": None # ID da categoria de análise
}


# ======================
# FUNÇÕES
# ======================
def criar_config():
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(CONFIG_PADRAO, f, indent=4, ensure_ascii=False)
        print("[CONFIG] config_farm.json criado com sucesso.")


def carregar_config() -> dict:
    criar_config()

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    return config


def salvar_config(config: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def validar_config(config: dict):
    erros = []

    for chave in [
        "canal_adv",
        "canal_aceitos",
        "canal_recusados",
        "categoria_analise"
    ]:
        if not isinstance(config.get(chave), int):
            erros.append(chave)

    if erros:
        raise ValueError(
            f"[CONFIG] IDs inválidos ou não configurados: {', '.join(erros)}"
        )