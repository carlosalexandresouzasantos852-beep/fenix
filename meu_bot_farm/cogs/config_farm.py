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
    "canal_adv": 0,            # Canal onde o ADV automático será enviado
    "canal_aceitos": 0,        # Canal de entregas aceitas
    "canal_recusados": 0,      # Canal de entregas recusadas

    # ======================
    # CATEGORIAS
    # ======================
    "categoria_analise": 0     # Categoria onde os tickets de análise são criados
}


def criar_config():
    """Cria o arquivo config_farm.json se não existir"""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(CONFIG_PADRAO, f, indent=4, ensure_ascii=False)
        print("[CONFIG] config_farm.json criado com sucesso.")


def carregar_config():
    """Carrega a configuração"""
    criar_config()
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_config(config: dict):
    """Salva alterações no config"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)