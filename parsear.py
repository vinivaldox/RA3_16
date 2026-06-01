# Nome | apelido no Github | link do Github
# Andrei de Carvalho Bley | andrei-bley | https://github.com/andrei-bley
# Vinicius Cordeiro Vogt | vinivaldox | https://github.com/vinivaldox
# Vitor Matias Percegona Bilbao | vitormpbilbao | https://github.com/vitormpbilbao

# Grupo: RA2 15
"""
Fase 2 do Compilador: Análise Sintática Descendente
Descrição:
    Implementa um parser LL(1) não-recursivo usando algoritmo de pilha
    para validar tokens contra a gramática fornecida pelo Aluno 1.
"""

from dataclasses import dataclass, field


@dataclass
class NoArvore:
    """
    Representa um nó da árvore sintática.

    Utilizados para construir a árvore de derivação durante o parsing.
    Cada nó pode ser terminal (folha) ou não-terminal (interno).

    Parameters
    ----------
    rotulo : str
        Nome do símbolo representado (ex: "Programa", "Comando", "Elemento")
    tipo : str
        Tipo do nó: "terminal" ou "nao_terminal"
    valor : str or None, optional
        Valor associado (apenas para nós terminais), por padrão None
    filhos : list of NoArvore, optional
        Lista de nós filhos, por padrão lista vazia
        Usa field(default_factory=list) para evitar mutabilidade compartilhada

    Examples
    --------
    >>> no_terminal = NoArvore("NUMERO", "terminal", valor="42")
    >>> no_nao_terminal = NoArvore("Elemento", "nao_terminal")
    >>> no_nao_terminal.filhos.append(no_terminal)
    """

    rotulo: str  # Programa, Comando, Elemento
    tipo: str  # terminal ou nao_terminal
    valor: str | None = None  # Valor para terminais
    # importa construtor de lista vazia para evitar mutabilidade compartilhada (onibus fantasma)
    filhos: list["NoArvore"] = field(default_factory=list)

    def __repr__(self) -> str:
        """
        Representação em string do nó da árvore.

        Returns
        -------
        str
            Para terminais: "NoArvore(rótulo, 'valor')"
            Para não-terminais: "NoArvore(rótulo, filhos=N)"
        """
        if self.tipo == "terminal":
            return f"NoArvore({self.rotulo}, '{self.valor}')"
        else:
            return f"NoArvore({self.rotulo}, filhos={len(self.filhos)})"

    def serializar(self):
        """
        Converte nó para dicionário (JSON-compatível).

        Recursivamente serializa todos os filhos para permitir
        conversão completa da árvore para JSON.

        Returns
        -------
        dict
            Dicionário com chaves: rotulo, tipo, valor, filhos

        Examples
        --------
        >>> no = NoArvore("NUMERO", "terminal", valor="42")
        >>> no.serializar()
        {'rotulo': 'NUMERO', 'tipo': 'terminal', 'valor': '42', 'filhos': []}
        """
        return {
            "rotulo": self.rotulo,
            "tipo": self.tipo,
            "valor": self.valor,
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
    """
    Parser LL(1) recursivo descendente para análise sintática.

    Implementa algoritmo de parsing recursivo descendente que valida
    uma sequência de tokens contra uma gramática LL(1) fornecida.
    Constrói uma árvore sintática durante o parsing.

    Parameters
    ----------
    gramatica : dict
        Dicionário com a gramática LL(1) (não utilizado nesta versão,
        mantido para compatibilidade futura)

    Attributes
    ----------
    tokens : list
        Tokens sendo processados no momento
    posicao : int
        Índice do próximo token a processar
    derivacoes : list
        Histórico de derivações durante o parsing
    erros : list of ErroSintatico
        Erros detectados durante parsing
    numero_comando : int
        Identificador do comando sendo processado

    Examples
    --------
    >>> parser = ParserLL1({})
    >>> tokens = [{'tipo': 'PARENTESIS', 'valor': '('}, ...]
    >>> resultado = parser.parser_comando_completo(tokens, 1)

    Notes
    -----
    O parser utiliza análise descendente com backtracking implícito.
    Cada método de parsing corresponde a um não-terminal da gramática.
    """

    def __init__(self, gramatica):
        """
        Inicializa o parser.

        Parameters
        ----------
        gramatica : dict
            Gramática LL(1) (não utilizado, mantido para compatibilidade)
        """
        self.gramatica = gramatica
        # Variáveis padronizadas para evitar AttributeError
        self.tokens = []
        self.posicao = 0
        self.derivacoes = []
        self.erros = []
        self.numero_comando = 0

    def get_terminal(self, token: dict) -> str:
        """
        Mapeia um token para seu terminal na gramática.

        Converte a representação interna de token para o símbolo
        terminal equivalente reconhecido pela gramática.

        Parameters
        ----------
        token : dict or None
            Token com estrutura {'tipo': str, 'valor': str}
            Tipos válidos: PARENTESIS, NUMERO, VARIAVEL, OPERADOR, COMANDO

        Returns
        -------
        str
            Terminal mapeado: NUMERO, VARIAVEL, OPERADOR, PARENTESIS_ESQ,
            PARENTESIS_DIR, START, END, MEM, RES, IF, WHILE, ou
            "$" se token é None, "DESCONHECIDO" caso contrário

        Examples
        --------
        >>> parser = ParserLL1({})
        >>> token_num = {'tipo': 'NUMERO', 'valor': '42'}
        >>> parser.get_terminal(token_num)
        'NUMERO'
        >>> parser.get_terminal(None)
        '$'
        """
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
            # Mapeia START, END, MEM, RES, IF, WHILE
            return valor
        else:
            return "DESCONHECIDO"

    def _next_token(self) -> dict | None:
        """
        Retorna próximo token sem avançar.

        Realiza lookahead do próximo token sem consumir da sequência.

        Returns
        -------
        dict or None
            Próximo token ou None se fim da sequência atingido

        See Also
        --------
        _get_next_token : Avança a posição após retornar token
        """
        if self.posicao < len(self.tokens):
            return self.tokens[self.posicao]
        return None

    def _get_next_token(self) -> dict | None:
        """
        Consome e retorna próximo token.

        Retorna o próximo token e incrementa a posição no buffer.

        Returns
        -------
        dict or None
            Próximo token ou None se fim atingido

        See Also
        --------
        _next_token : Apenas olha sem consumir
        """
        token = self._next_token()
        if token:
            self.posicao += 1
        return token

    def _add_erro(self, esperado: str, encontrado: str, contexto: str):
        """
        Registra um erro sintático.

        Cria instância de ErroSintatico e adiciona ao histórico.

        Parameters
        ----------
        esperado : str
            Terminal esperado
        encontrado : str
            Terminal efetivamente encontrado
        contexto : str
            Descrição do contexto onde erro ocorreu
        """
        erro = ErroSintatico(
            numero_comando=self.numero_comando,
            indice_token=self.posicao,
            esperado=esperado,
            encontrado=encontrado,
            mensagem=f"Cmd {self.numero_comando}[{self.posicao}]: "
            f"Esperado '{esperado}', encontrado '{encontrado}' ({contexto})",
        )
        self.erros.append(erro)

    def _combinar_terminal(self, esperado, contexto, no):
        """
        Combina um terminal esperado com próximo token.

        Se próximo token matches o terminal esperado, consome-o
        e adiciona nó folha à árvore. Caso contrário, registra erro.

        Parameters
        ----------
        esperado : str
            Terminal esperado pela gramática
        contexto : str
            Descrição do contexto (para mensagens de erro)
        no : NoArvore
            Nó pai onde adicionar o terminal como filho

        Returns
        -------
        bool
            True se matching bem-sucedido, False caso contrário
        """
        token = self._next_token()
        terminal = self.get_terminal(token)

        if terminal == esperado:
            self._get_next_token()
            no_terminal = NoArvore(esperado, "terminal", valor=token.get("valor", ""))
            no.filhos.append(no_terminal)
            return True
        else:
            self._add_erro(esperado, terminal, contexto)
            return False

    def _add_derivacao(self, derivacao: str):
        """
        Registra uma derivação (para debug/trace).

        Parameters
        ----------
        derivacao : str
            String descrevendo a derivação (ex: "Programa -> ( START )")
        """
        self.derivacoes.append(derivacao)

    def parser_programa(self):
        """
        Parseia não-terminal Programa.

        Gramática: Programa ::= ( START ) ListaOuFim

        Returns
        -------
        NoArvore or None
            Nó raiz da árvore sintática se parsing bem-sucedido,
            None se erro detectado
        """
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
        """
        Parseia não-terminal ListaOuFim.

        Gramática: ListaOuFim ::= ( ConteudoOuFim )

        Returns
        -------
        NoArvore or None
            Nó da árvore se bem-sucedido, None caso contrário
        """
        no = NoArvore("ListaOuFim", "nao_terminal")
        if not self._combinar_terminal("PARENTESIS_ESQ", "início de bloco", no):
            return None

        conteudo_no = self.parser_conteudo_ou_fim()
        if conteudo_no:
            no.filhos.append(conteudo_no)
        return no

    def parser_conteudo_ou_fim(self):
        """
        Parseia não-terminal ConteudoOuFim.

        Gramática: ConteudoOuFim ::= END | Conteudo ListaOuFim

        Utiliza lookahead para decidir qual alternativa parsear.

        Returns
        -------
        NoArvore
            Nó da árvore (nunca None, epsilon retorna nó vazio)
        """
        no = NoArvore("ConteudoOuFim", "nao_terminal")
        token = self._next_token()
        terminal = self.get_terminal(token)

        if terminal == "END":
            self._combinar_terminal("END", "palavra END", no)
            self._combinar_terminal("PARENTESIS_DIR", "fim END", no)
            self._add_derivacao("ConteudoOuFim -> END )")
        else:
            conteudo_no = self.parser_conteudo()
            if conteudo_no:
                no.filhos.append(conteudo_no)
            self._combinar_terminal("PARENTESIS_DIR", "fim de comando", no)

            lista_no = self.parser_lista_ou_fim()
            if lista_no:
                no.filhos.append(lista_no)
            self._add_derivacao("ConteudoOuFim -> Conteudo ) ListaOuFim")
        return no

    def parser_comando(self):
        """
        Parseia não-terminal Comando.

        Gramática: Comando ::= ( Conteudo )

        Returns
        -------
        NoArvore or None
            Nó da árvore se bem-sucedido, None caso contrário
        """
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
        """
        Parseia não-terminal Conteudo.

        Gramática: Conteudo ::= Elemento RestoConteudo

        Returns
        -------
        NoArvore
            Nó da árvore (nunca None)
        """
        no = NoArvore("Conteudo", "nao_terminal")
        elem_no = self.parser_elemento()
        if elem_no:
            no.filhos.append(elem_no)
        resto_no = self.parser_resto_conteudo()
        if resto_no:
            no.filhos.append(resto_no)
        return no

    def parser_resto_conteudo(self):
        """
        Parseia não-terminal RestoConteudo.

        Gramática: RestoConteudo ::= Elemento Cauda | RES | epsilon

        Usa lookahead para decidir qual alternativa seguir.

        Returns
        -------
        NoArvore
            Nó da árvore (nunca None, epsilon retorna nó vazio)
        """
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
        return no  # Se não entrar nos ifs, é EPSILON

    def parser_cauda(self):
        """
        Parseia não-terminal Cauda.

        Gramática: Cauda ::= OPERADOR | MEM | IF | WHILE | epsilon

        Returns
        -------
        NoArvore
            Nó da árvore (nunca None, epsilon retorna nó vazio)
        """
        no = NoArvore("Cauda", "nao_terminal")
        token = self._next_token()
        terminal = self.get_terminal(token)
        if terminal in ["OPERADOR", "MEM", "IF", "WHILE"]:
            self._combinar_terminal(terminal, "ação", no)
        return no

    def parser_elemento(self):
        """
        Parseia não-terminal Elemento.

        Gramática: Elemento ::= NUMERO | VARIAVEL | Comando

        Returns
        -------
        NoArvore
            Nó da árvore (nunca None)
        """
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
        """
        Processa um comando completo (programa inteiro).

        Inicializa estado do parser, executa parsing e retorna resultado
        estruturado com árvore, derivações e erros.

        Parameters
        ----------
        tokens : list of dict
            Tokens do comando (com tipos e valores)
        num_comando : int
            Identificador do comando (1-indexed)

        Returns
        -------
        dict
            Estrutura com chaves:
            - numero_comando : int - ID do comando
            - sucesso : bool - True se parsing sem erros
            - arvore : dict or None - Árvore sintática serializada
            - erros : list of dict - Erros detectados (convertidos de ErroSintatico)

        Examples
        --------
        >>> parser = ParserLL1({})
        >>> tokens = [...]
        >>> resultado = parser.parser_comando_completo(tokens, 1)
        >>> if resultado['sucesso']:
        ...     print(resultado['arvore'])
        """
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
    """
    Processa um programa completo e retorna resultado de parsing.

    Função principal que coordena a análise sintática. Aceita uma sequência
    de tokens do analisador léxico (Aluno 3) e retorna árvore sintática,
    derivações e lista de erros.

    Parameters
    ----------
    tokens_planificados : list of dict
        Lista de tokens do analisador léxico, cada token é dicionário:
        {'tipo': str, 'valor': str|float}

        Tipos válidos: PARENTESIS, NUMERO, VARIAVEL, OPERADOR, COMANDO
    gramatica : dict
        Dicionário com gramática LL(1) (mantido para compatibilidade,
        atualmente não utilizado)

    Returns
    -------
    dict
        Resultado do parsing com estrutura:
        - sucesso : bool - True se nenhum erro sintático
        - resultados : list of dict - Lista com resultado do comando
        - resumo : str - Descrição breve do resultado

        Cada resultado em 'resultados' contém:
        - numero_comando : int - ID (sempre 1 neste caso)
        - sucesso : bool - True se sem erros
        - arvore : dict or None - Árvore sintática serializada
        - erros : list of dict - Erros detectados

    Examples
    --------
    >>> tokens = [
    ...     {'tipo': 'PARENTESIS', 'valor': '('},
    ...     {'tipo': 'NUMERO', 'valor': 'START'},
    ...     {'tipo': 'PARENTESIS', 'valor': ')'},
    ...     ...
    ... ]
    >>> resultado = parsear(tokens, {})
    >>> if resultado['sucesso']:
    ...     print("Parsing bem-sucedido!")
    ...     arvore = resultado['resultados'][0]['arvore']

    Notes
    -----
    Processa todos os tokens como um único programa, já que a gramática
    engloba (START), lista de comandos e (END) em uma única derivação.
    """
    parser = ParserLL1(gramatica)
    # passamos todos os tokens de uma vez porque o programa
    # engloba o START, Lista de Comandos e o END.
    resultado = parser.parser_comando_completo(tokens_planificados, 1)

    return {
        "sucesso": resultado["sucesso"],
        "resultados": [resultado],
        "resumo": "Processamento do programa completo",
    }
