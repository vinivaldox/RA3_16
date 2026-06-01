# Nome | apelido no Github | link do Github
# Andrei de Carvalho Bley | andrei-bley | https://github.com/andrei-bley
# Vinicius Cordeiro Vogt | vinivaldox | https://github.com/vinivaldox
# Vitor Matias Percegona Bilbao | vitormpbilbao | https://github.com/vitormpbilbao

# Grupo: RA3_16
"""
Fase 3 do Compilador: Análise Semântica + Geração de Assembly
Este módulo expande o parser da Fase 2 com análise semântica.
"""

from dataclasses import dataclass, field


@dataclass
class NoArvore:
    """Representa um nó da árvore sintática com anotações semânticas."""

    rotulo: str
    tipo: str  # "terminal" ou "nao_terminal"
    valor: str | None = None
    filhos: list["NoArvore"] = field(default_factory=list)
    tipo_semantico: str | None = None  # Tipo inferido (int, float, bool)
    categoria_semantica: str | None = None  # Classificação semântica
    linha: int = 0  # Para relatórios de erro

    def __repr__(self) -> str:
        if self.tipo == "terminal":
            return f"NoArvore({self.rotulo}, '{self.valor}')"
        else:
            return f"NoArvore({self.rotulo}, filhos={len(self.filhos)})"

    def serializar(self):
        return {
            "rotulo": self.rotulo,
            "tipo": self.tipo,
            "valor": self.valor,
            "tipo_semantico": self.tipo_semantico,
            "categoria_semantica": self.categoria_semantica,
            "linha": self.linha,
            "filhos": [filho.serializar() for filho in self.filhos],
        }


@dataclass
class ErroSintatico:
    """
    Representa um erro sintático detectado durante parsing.

    Armazena informações detalhadas sobre erros encontrados,
    incluindo localização, token esperado/encontrado e mensagem descritiva.

    Parameters
    ----------
    numero_comando : int
        Índice do comando onde o erro foi detectado (1-indexed)
    indice_token : int
        Posição do token problemático dentro do comando
    esperado : str
        Terminal ou símbolo esperado pela gramática
    encontrado : str
        Terminal ou símbolo efetivamente encontrado
    mensagem : str
        Descrição completa e legível do erro

    Examples
    --------
    >>> erro = ErroSintatico(1, 5, "NUMERO", "VARIAVEL",
    ...                       "Esperado NUMERO, encontrado VARIAVEL")
    >>> print(erro)
    ErroSintatico(cmd=1[5]: Esperado NUMERO, encontrado VARIAVEL)

    Notes
    -----
    Usada para relatório de erros ao usuário final.
    """

    numero_comando: int  # Qual comando tem erro
    indice_token: int  # Posição no token do comando
    esperado: str  # O que era esperado
    encontrado: str  # O que foi encontrado
    mensagem: str  # Mensagem descritiva completa

    def __repr__(self) -> str:
        """
        Representação em string do erro.

        Returns
        -------
        str
            Formato: "ErroSintatico(cmd=N[M]: mensagem)"
        """
        return f"ErroSintatico(cmd={self.numero_comando}[{self.indice_token}]: {self.mensagem})"


class ParserLL1:
    """Parser LL(1) recursivo descendente para análise sintática."""

    def __init__(self, gramatica):
        self.gramatica = gramatica
        self.tokens = []
        self.posicao = 0
        self.derivacoes = []
        self.erros = []
        self.numero_comando = 0

    def get_terminal(self, token: dict) -> str:
        """Mapeia um token para seu terminal na gramática."""
        if not token:
            return "$"
        tipo = token.get("tipo", "")
        valor = str(token.get("valor", "")).upper()

        if tipo == "PARENTESIS":
            return "PARENTESIS_ESQ" if valor == "(" else "PARENTESIS_DIR"
        elif tipo == "NUMERO":
            return "NUMERO"
        elif tipo == "VARIAVEL":
            return "VARIAVEL"
        elif tipo == "OPERADOR":
            return "OPERADOR"
        elif tipo in ["COMANDO", "KEYWORD"]:
            return valor
        else:
            return "DESCONHECIDO"

    def _next_token(self) -> dict | None:
        """Retorna próximo token sem avançar."""
        if self.posicao < len(self.tokens):
            return self.tokens[self.posicao]
        return None

    def _get_next_token(self) -> dict | None:
        """Consome e retorna próximo token."""
        token = self._next_token()
        if token:
            self.posicao += 1
        return token

    def _add_erro(self, esperado: str, encontrado: str, contexto: str):
        """Registra um erro sintático."""
        token = self._next_token()
        linha = token.get("linha", 0) if token else 0
        erro = ErroSintatico(
            numero_comando=self.numero_comando,
            indice_token=self.posicao,
            esperado=esperado,
            encontrado=encontrado,
            mensagem=f"Linha {linha}: Esperado '{esperado}', encontrado '{encontrado}' ({contexto})",
        )
        self.erros.append(erro)

    def _combinar_terminal(self, esperado, contexto, no):
        """Combina um terminal esperado com próximo token."""
        token = self._next_token()
        terminal = self.get_terminal(token)

        if terminal == esperado:
            self._get_next_token()
            no_terminal = NoArvore(
                esperado,
                "terminal",
                valor=token.get("valor", ""),
                linha=token.get("linha", 0),  # Anotação de linha para erros semânticos
            )
            no.filhos.append(no_terminal)
            return True
        else:
            self._add_erro(esperado, terminal, contexto)
            return False

    def parser_programa(self):
        """Parseia não-terminal Programa."""
        no = NoArvore("Programa", "nao_terminal")
        if not self._combinar_terminal("PARENTESIS_ESQ", "início", no):
            return None
        if not self._combinar_terminal("START", "palavra START", no):
            return None
        if not self._combinar_terminal("PARENTESIS_DIR", "fim START", no):
            return None

        lista_no = self.parser_lista_ou_fim()
        if lista_no:
            no.filhos.append(lista_no)
        return no

    def parser_lista_ou_fim(self):
        """Parseia não-terminal ListaOuFim."""
        no = NoArvore("ListaOuFim", "nao_terminal")
        if not self._combinar_terminal("PARENTESIS_ESQ", "início de bloco", no):
            return None

        conteudo_no = self.parser_conteudo_ou_fim()
        if conteudo_no:
            no.filhos.append(conteudo_no)
        return no

    def parser_conteudo_ou_fim(self):
        """Parseia não-terminal ConteudoOuFim."""
        no = NoArvore("ConteudoOuFim", "nao_terminal")
        token = self._next_token()
        terminal = self.get_terminal(token)

        if terminal == "END":
            self._combinar_terminal("END", "palavra END", no)
            self._combinar_terminal("PARENTESIS_DIR", "fim END", no)
        else:
            conteudo_no = self.parser_conteudo()
            if conteudo_no:
                no.filhos.append(conteudo_no)
            self._combinar_terminal("PARENTESIS_DIR", "fim de comando", no)

            lista_no = self.parser_lista_ou_fim()
            if lista_no:
                no.filhos.append(lista_no)
        return no

    def parser_comando(self):
        """Parseia não-terminal Comando."""
        no = NoArvore("Comando", "nao_terminal")
        if not self._combinar_terminal("PARENTESIS_ESQ", "início comando", no):
            return None
        conteudo_no = self.parser_conteudo()
        if conteudo_no:
            no.filhos.append(conteudo_no)
        if not self._combinar_terminal("PARENTESIS_DIR", "fim comando", no):
            return None
        return no

    def parser_conteudo(self):
        """Parseia não-terminal Conteudo."""
        no = NoArvore("Conteudo", "nao_terminal")
        elem_no = self.parser_elemento()
        if elem_no:
            no.filhos.append(elem_no)
        resto_no = self.parser_resto_conteudo()
        if resto_no:
            no.filhos.append(resto_no)
        return no

    def parser_resto_conteudo(self):
        """Parseia não-terminal RestoConteudo."""
        no = NoArvore("RestoConteudo", "nao_terminal")
        token = self._next_token()
        terminal = self.get_terminal(token)

        if terminal == "RES":
            self._combinar_terminal("RES", "comando RES", no)
        elif terminal in ["NUMERO", "VARIAVEL", "PARENTESIS_ESQ"]:
            elem_no = self.parser_elemento()
            if elem_no:
                no.filhos.append(elem_no)
            cauda_no = self.parser_cauda()
            if cauda_no:
                no.filhos.append(cauda_no)
        return no

    def parser_cauda(self):
        """Parseia não-terminal Cauda."""
        no = NoArvore("Cauda", "nao_terminal")
        token = self._next_token()
        terminal = self.get_terminal(token)
        if terminal in ["OPERADOR", "MEM", "IF", "WHILE"]:
            self._combinar_terminal(terminal, "ação", no)
        return no

    def parser_elemento(self):
        """Parseia não-terminal Elemento."""
        no = NoArvore("Elemento", "nao_terminal")
        token = self._next_token()
        terminal = self.get_terminal(token)

        if terminal == "NUMERO":
            self._combinar_terminal("NUMERO", "valor", no)
        elif terminal == "VARIAVEL":
            self._combinar_terminal("VARIAVEL", "id", no)
        elif terminal == "PARENTESIS_ESQ":
            cmd_no = self.parser_comando()
            if cmd_no:
                no.filhos.append(cmd_no)
        return no

    def parser_comando_completo(self, tokens, num_comando):
        """Processa um comando completo (programa inteiro)."""
        self.tokens = tokens
        self.posicao = 0
        self.numero_comando = num_comando
        self.erros = []
        arvore = self.parser_programa()
        return {
            "numero_comando": num_comando,
            "sucesso": arvore is not None and len(self.erros) == 0,
            "arvore": arvore.serializar() if arvore else None,
            "erros": [vars(e) for e in self.erros],
        }


def parsear(tokens_planificados: list[dict], gramatica: dict) -> dict:
    """Processa um programa completo e retorna resultado de parsing."""
    parser = ParserLL1(gramatica)
    resultado = parser.parser_comando_completo(tokens_planificados, 1)

    return {
        "sucesso": resultado["sucesso"],
        "resultados": [resultado],
        "resumo": "Processamento do programa completo",
    }
