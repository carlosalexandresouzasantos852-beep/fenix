# Stub de audioop para Python 3.13
# Serve apenas para evitar crash do discord.py
# Funções NÃO fazem processamento de áudio

def error(*args, **kwargs):
    raise NotImplementedError("Audio disabled")

def lin2lin(*args, **kwargs):
    return b""

def ratecv(*args, **kwargs):
    return b"", None

def add(*args, **kwargs):
    return b""

def mul(*args, **kwargs):
    return b""

def bias(*args, **kwargs):
    return b""

def max(*args, **kwargs):
    return 0

def avg(*args, **kwargs):
    return 0

def rms(*args, **kwargs):
    return 0