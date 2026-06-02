# Nome | apelido no Github | link do Github
# Andrei de Carvalho Bley | andrei-bley | https://github.com/andrei-bley
# Vinicius Cordeiro Vogt | vinivaldox | https://github.com/vinivaldox
# Vitor Matias Percegona Bilbao | vitormpbilbao | https://github.com/vitormpbilbao

# Grupo: RA3_16

# Gramática LL(1) fatorada para a linguagem RPN com estruturas de controle


def construirGramatica():
    return {
        "Programa": [["PARENTESIS_ESQ", "START", "PARENTESIS_DIR", "ListaOuFim"]],
        "ListaOuFim": [["PARENTESIS_ESQ", "ConteudoOuFim"]],
        "ConteudoOuFim": [
            ["END", "PARENTESIS_DIR"],
            ["Conteudo", "PARENTESIS_DIR", "ListaOuFim"],
        ],
        "Comando": [["PARENTESIS_ESQ", "Conteudo", "PARENTESIS_DIR"]],
        "Conteudo": [["Elemento", "RestoConteudo"]],
        "RestoConteudo": [["Elemento", "Cauda"], ["RES"], ["EPSILON"]],
        "Cauda": [["OPERADOR"], ["MEM"], ["IF"], ["WHILE"]],
        "Elemento": [["NUMERO"], ["VARIAVEL"], ["Comando"]],
    }


def calcularFirst(gramatica):
    firsts = {nt: set() for nt in gramatica}

    terminais = {
        "PARENTESIS_ESQ",
        "PARENTESIS_DIR",
        "START",
        "END",
        "EPSILON",
        "RES",
        "OPERADOR",
        "MEM",
        "IF",
        "WHILE",
        "NUMERO",
        "VARIAVEL",
    }

    teve_mudanca = True
    while teve_mudanca:
        teve_mudanca = False

        for nt, regras in gramatica.items():
            for regra in regras:
                tamanho_antigo = len(firsts[nt])
                for simbolo in regra:
                    if simbolo in terminais:
                        firsts[nt].add(simbolo)
                        break
                    else:
                        firsts_do_vizinho = firsts[simbolo]
                        firsts[nt].update(firsts_do_vizinho - {"EPSILON"})
                        if "EPSILON" not in firsts_do_vizinho:
                            break
                else:
                    firsts[nt].add("EPSILON")
                if len(firsts[nt]) > tamanho_antigo:
                    teve_mudanca = True

    return firsts


def calcularFollow(gramatica, firsts):
    follows = {nt: set() for nt in gramatica}
    follows["Programa"].add("$")
    teve_mudanca = True
    while teve_mudanca:
        teve_mudanca = False
        for nt, regras in gramatica.items():
            for regra in regras:
                for i, simbolo in enumerate(regra):
                    if simbolo not in gramatica:
                        continue
                    proximo = regra[i + 1 :] if i < len(regra) - 1 else []
                    tamanho_antigo = len(follows[simbolo])

                    for prox_simbolo in proximo:
                        if prox_simbolo in gramatica:
                            follows[simbolo].update(firsts[prox_simbolo] - {"EPSILON"})
                        else:
                            follows[simbolo].add(prox_simbolo)

                    if not proximo or all(
                        "EPSILON" in firsts.get(s, set()) for s in proximo
                    ):
                        follows[simbolo].update(follows[nt])

                    if len(follows[simbolo]) > tamanho_antigo:
                        teve_mudanca = True

    return follows


def mapearTokensParaTerminais(token):
    """Mapeia tokens léxicos para terminais da gramática."""
    if token.tipo == "PARENTESIS" and token.valor == "(":
        return "PARENTESIS_ESQ"
    elif token.tipo == "PARENTESIS" and token.valor == ")":
        return "PARENTESIS_DIR"
    elif token.tipo == "KEYWORD" and token.valor == "START":
        return "START"
    elif token.tipo == "KEYWORD" and token.valor == "END":
        return "END"
    elif token.tipo == "COMANDO" and token.valor == "RES":
        return "RES"
    elif token.tipo == "COMANDO" and token.valor == "MEM":
        return "MEM"
    elif token.tipo == "KEYWORD" and token.valor == "IF":
        return "IF"
    elif token.tipo == "KEYWORD" and token.valor == "WHILE":
        return "WHILE"
    elif token.tipo == "NUMERO":
        return "NUMERO"
    elif token.tipo == "VARIAVEL":
        return "VARIAVEL"
    elif token.tipo == "OPERADOR":
        return "OPERADOR"
    else:
        return None
