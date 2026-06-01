# Nome | apelido no Github | link do Github
# Andrei de Carvalho Bley | andrei-bley | https://github.com/andrei-bley
# Vinicius Cordeiro Vogt | vinivaldox | https://github.com/vinivaldox
# Vitor Matias Percegona Bilbao | vitormpbilbao | https://github.com/vitormpbilbao

# Grupo: RA3_16

# COMPILADOR RPN → ASSEMBLY ARMv7 (Fase 3)
# Analisador Semântico + Geração de Código


import sys
from analisador_lexico import lerTokens
from gramatica import construirGramatica
from parsear import parsear, NoArvore
from analisador_semantico import AnalisadorSemantico
from gerarAssembly import (
    gerarArvore,
    gerarAssembly,
    imprimir_arvore,
    salvar_arvore_json,
)


def validar_programa(arvore: NoArvore) -> bool:
    """Valida se o programa começa com (START) e termina com (END)."""
    if arvore is None:
        return False

    # Verificar se a árvore tem a estrutura correta
    # Programa -> ( START ) ListaOuFim
    if arvore.rotulo != "Programa":
        return False

    # Procurar por START e END na árvore
    tem_start = False
    tem_end = False

    def buscar_tokens(no):
        nonlocal tem_start, tem_end
        if no is None:
            return
        if no.tipo == "terminal":
            if no.rotulo == "START" and no.valor == "START":
                tem_start = True
            elif no.rotulo == "END" and no.valor == "END":
                tem_end = True
        for filho in no.filhos:
            buscar_tokens(filho)

    buscar_tokens(arvore)
    return tem_start and tem_end


def converter_tokens(tokens_brutos: list) -> list:
    """Converte tokens do analisador léxico para formato esperado pelo parser."""
    tokens_convertidos = []
    for token in tokens_brutos:
        # Converter Token object para dict se necessário
        if hasattr(token, "to_dict"):
            token_dict = token.to_dict()
            # Adicionar linha (que pode estar em __dict__)
            if hasattr(token, "linha"):
                token_dict["linha"] = token.linha
        else:
            token_dict = token
        tokens_convertidos.append(token_dict)
    return tokens_convertidos
