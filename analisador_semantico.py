# Nome | apelido no Github | link do Github
# Andrei de Carvalho Bley | andrei-bley | https://github.com/andrei-bley
# Vinicius Cordeiro Vogt | vinivaldox | https://github.com/vinivaldox
# Vitor Matias Percegona Bilbao | vitormpbilbao | https://github.com/vitormpbilbao

# Grupo: RA3_16
# ==========================================
# MÓDULO: Analisador Semântico
# ==========================================

from tabela_simbolos import TabelaSimbolos
from parsear import NoArvore
from typing import Optional, Tuple


class AnalisadorSemantico:
    """Realiza análise semântica na árvore sintática."""