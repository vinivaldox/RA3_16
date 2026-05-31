# Nome | apelido no Github | link do Github
# Andrei de Carvalho Bley | andrei-bley | https://github.com/andrei-bley
# Vinicius Cordeiro Vogt | vinivaldox | https://github.com/vinivaldox
# Vitor Matias Percegona Bilbao | vitormpbilbao | https://github.com/vitormpbilbao

# Grupo: RA3 16
# FASE 3: Analisador Semântico + Geração Assembly

from dataclasses import dataclass

COMANDOS = {"MEM", "RES"}
KEYWORDS = {"START", "END", "IF", "WHILE"}


@dataclass
class Token:
    """Representa um token reconhecido pelo analisador léxico."""

    tipo: str  # "NUMERO", "OPERADOR", "PARENTESIS", "COMANDO", "VARIAVEL", "KEYWORD"
    valor: str  # O valor real do token. Exemplo, "3", "+", "(", "MEM"
    linha: int = 0  # Linha onde o token aparece (para erros)

    def to_dict(self) -> dict:
        """Converte o Token para formato dicionário."""
        return {"tipo": self.tipo, "valor": self.valor, "linha": self.linha}


def remover_comentarios(texto: str) -> str:
    """Remove comentários delimitados por *{ e }* do código-fonte.

    Comentários podem estar em linhas inteiras, no final de linhas ou entre expressões.

    Args:
        texto: Conteúdo do arquivo de entrada

    Returns:
        Texto com comentários removidos
    """
    resultado = []
    i = 0
    while i < len(texto):
        # Procura por início de comentário
        if i < len(texto) - 1 and texto[i : i + 2] == "*{":
            # Encontrou início de comentário, pula até o fim
            i += 2
            while i < len(texto) - 1:
                if texto[i : i + 2] == "}*":
                    i += 2
                    break
                i += 1
            else:
                # Comentário não fechado - erro semântico será reportado depois
                if i < len(texto):
                    i += 1
        else:
            resultado.append(texto[i])
            i += 1

    return "".join(resultado)


def estado_inicial(caractere: str, contexto: dict) -> str:
    """Estado inicial do DFA - reconhece primeiro caractere de cada token."""

    # parênteses, tem retorno imediato
    if caractere == "(":
        contexto["tokens"].append(Token("PARENTESIS", "(", contexto.get("linha", 0)))
        return "inicial"
    elif caractere == ")":
        contexto["tokens"].append(Token("PARENTESIS", ")", contexto.get("linha", 0)))
        return "inicial"

    # ignora espaços e tabs
    elif caractere in " \t":
        return "inicial"

    # digitos de um numero
    elif caractere.isdigit():
        contexto["buffer"] = caractere
        return "numero"

    # operadores simples
    elif caractere in "+-|":
        contexto["tokens"].append(
            Token("OPERADOR", caractere, contexto.get("linha", 0))
        )
        return "inicial"

    # potência
    elif caractere == "^":
        contexto["tokens"].append(
            Token("OPERADOR", caractere, contexto.get("linha", 0))
        )
        return "inicial"

    # divisão ou divisão inteira
    elif caractere == "/":
        contexto["buffer"] = caractere
        return "divisao"

    # resto ou módulo
    elif caractere == "%":
        contexto["tokens"].append(Token("OPERADOR", "%", contexto.get("linha", 0)))
        return "inicial"

    # multiplicação
    elif caractere == "*":
        contexto["tokens"].append(Token("OPERADOR", "*", contexto.get("linha", 0)))
        return "inicial"

    # operadores relacionais compostos (podem ser simples ou duplos)
    elif caractere == "<":
        contexto["buffer"] = "<"
        return "relacional"

    elif caractere == ">":
        contexto["buffer"] = ">"
        return "relacional"

    elif caractere == "=":
        contexto["buffer"] = "="
        return "relacional"

    elif caractere == "!":
        contexto["buffer"] = "!"
        return "relacional"

    # letra: pode ser variável ou keyword
    elif caractere.isalpha():
        contexto["buffer"] = caractere
        return "letra"

    # quebra de linha
    elif caractere == "\n":
        contexto["linha"] = contexto.get("linha", 0) + 1
        return "inicial"

    else:
        raise ValueError(
            f"Caractere inválido: '{caractere}' na linha {contexto.get('linha', 0)}"
        )
    
def estado_numero(caractere: str, contexto: dict) -> str:
    """Estado para processamento de números."""
    if caractere.isdigit():
        contexto["buffer"] += caractere
        return "numero"
    elif caractere == ".":
        contexto["buffer"] += caractere
        return "numero_flutuante"
    else:
        # termina o número
        token = Token("NUMERO", contexto["buffer"], contexto.get("linha", 0))
        contexto["tokens"].append(token)
        contexto["buffer"] = ""
        # reprocessa o caractere atual
        return estado_inicial(caractere, contexto)


def estado_numero_flutuante(caractere: str, contexto: dict) -> str:
    """Estado para processamento de números com ponto decimal."""
    if caractere.isdigit():
        contexto["buffer"] += caractere
        return "numero_flutuante"
    elif caractere == ".":
        # Detecta segundo ponto decimal - erro
        raise ValueError(
            f"Número malformado: dois pontos - '{contexto['buffer']}' na linha {contexto.get('linha', 0)}"
        )
    else:
        # termina o número
        token = Token("NUMERO", contexto["buffer"], contexto.get("linha", 0))
        contexto["tokens"].append(token)
        contexto["buffer"] = ""
        return estado_inicial(caractere, contexto)