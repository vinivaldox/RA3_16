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

    def __init__(self):
        self.tabela_simbolos = TabelaSimbolos()
        self.erros_semanticos = []
        self.arvore_aumentada = None
        self.ultimo_tipo = None  # Tipo do resultado da última expressão
        self.stack_rpn = []  # Stack RPN para rastrear tipos e variáveis
        self.ultima_variavel = None  # Última variável encontrada

    def analisar(self, arvore: NoArvore) -> Tuple[bool, NoArvore, list]:
        """Realiza análise semântica completa.

        Args:
            arvore: Árvore sintática a ser analisada

        Returns:
            Tupla (sucesso, arvore_aumentada, erros)
        """
        self.arvore_aumentada = self._clonar_no(arvore)
        self._analisar_programa(self.arvore_aumentada)

        return (
            not self.tabela_simbolos.tem_erros() and len(self.erros_semanticos) == 0,
            self.arvore_aumentada,
            self.tabela_simbolos.erros_semanticos + self.erros_semanticos,
        )

    def _clonar_no(self, no: NoArvore) -> NoArvore:
        """Clona um nó da árvore mantendo sua estrutura."""
        novo_no = NoArvore(
            rotulo=no.rotulo,
            tipo=no.tipo,
            valor=no.valor,
            tipo_semantico=no.tipo_semantico,
            categoria_semantica=no.categoria_semantica,
            linha=no.linha,
        )
        for filho in no.filhos:
            novo_no.filhos.append(self._clonar_no(filho))
        return novo_no

    def _analisar_programa(self, no: NoArvore):
        """Analisa o não-terminal Programa."""
        # Processa Programa como árvore
        for filho in no.filhos:
            # Apenas reset em elementos do nível mais alto (ListaOuFim)
            if filho.tipo != "terminal" and filho.rotulo == "ListaOuFim":
                self.stack_rpn = []
                self.ultima_variavel = None
            self._analisar_no(filho)

    def _analisar_no(self, no: NoArvore) -> Optional[str]:
        """Analisa um nó da árvore retornando seu tipo.

        Returns:
            Tipo inferido ("int", "float", "bool") ou None
        """
        if no is None:
            return None

        if no.tipo == "terminal":
            return self._analisar_terminal(no)
        else:
            # Não-terminal: processa filhos em sequência
            último_tipo = None

            for filho in no.filhos:
                tipo = self._analisar_no(filho)
                if tipo:
                    último_tipo = tipo

            return último_tipo

    def _analisar_terminal(self, no: NoArvore) -> Optional[str]:
        """Analisa um nó terminal (folha)."""

        if no.rotulo == "NUMERO":
            # Inferir tipo do número literal
            if "." in no.valor:
                no.tipo_semantico = "float"
                tipo = "float"
            else:
                no.tipo_semantico = "int"
                tipo = "int"

            # Rastrear na stack
            self.stack_rpn.append(("numero", no.valor, tipo, no.linha))
            return tipo

        elif no.rotulo == "VARIAVEL":
            # Usar ou inferir tipo da variável
            tipo = self.tabela_simbolos.usar_variavel(no.valor, no.linha)
            if tipo is None:
                # Tipo desconhecido ainda - será definido quando MEM a atribuir
                tipo = "float"  # Tipo padrão para inferência

            # Rastrear na stack para MEM
            self.stack_rpn.append(("variavel", no.valor, tipo, no.linha))
            self.ultima_variavel = (no.valor, tipo, no.linha)

            no.tipo_semantico = tipo
            return tipo

        elif no.rotulo == "OPERADOR":
            no.categoria_semantica = "operacao"

            # Calcular tipo do resultado da operação
            # Em RPN, os dois últimos operandos foram o penúltimo e antepenúltimo
            tipo_resultado = None
            if len(self.stack_rpn) >= 2:
                tipo_dir = self.stack_rpn[-1][2]  # Topo: direito
                tipo_esq = self.stack_rpn[-2][2]  # Penúltimo: esquerdo
                tipo_resultado = self._validar_operacao(
                    no.valor, tipo_esq, tipo_dir, no.linha
                )

            if tipo_resultado:
                # Adicionar resultado à stack
                self.stack_rpn.append(("resultado", no.valor, tipo_resultado, no.linha))

            return tipo_resultado

        elif no.rotulo == "MEM":
            no.categoria_semantica = "atribuicao"

            # Em RPN: ( valor variável MEM )
            # Última variável e penúltimo valor foram adicionados à stack
            if self.ultima_variavel and len(self.stack_rpn) >= 2:
                # Stack topo: ("variavel", nome, tipo_desconhecido, linha)
                # Stack penúltimo: ("numero", valor, tipo_verdadeiro, linha)

                tipo_valor = None
                # Procurar o valor imediatamente anterior na stack
                if len(self.stack_rpn) >= 2:
                    item_penultimo = self.stack_rpn[-2]
                    if item_penultimo[0] in ("numero", "resultado"):
                        tipo_valor = item_penultimo[2]  # tipo real do número

                # Obter nome da variável do topo
                if self.ultima_variavel:
                    var_nome = self.ultima_variavel[0]
                    var_linha = self.ultima_variavel[2]

                    # Se achamos um tipo de valor, define a variável com esse tipo
                    if tipo_valor:
                        self.tabela_simbolos.definir_variavel(
                            var_nome, tipo_valor, var_linha
                        )
                    else:
                        # Padrão: float
                        self.tabela_simbolos.definir_variavel(
                            var_nome, "float", var_linha
                        )

            return None

        elif no.rotulo == "RES":
            no.tipo_semantico = "float"  # RES sempre retorna float
            return "float"

        elif no.rotulo in ("START", "END"):
            no.categoria_semantica = "controle_programa"
            return None

        elif no.rotulo == "IF":
            no.categoria_semantica = "condicional"
            return None

        elif no.rotulo == "WHILE":
            no.categoria_semantica = "laco"
            return None

        return None

    def _validar_operacao(
        self,
        operador: str,
        tipo_esq: Optional[str],
        tipo_dir: Optional[str],
        linha: int,
    ) -> Optional[str]:
        """Valida uma operação aritmética ou lógica.

        Args:
            operador: O operador (+, -, *, /, //, %, ^, etc.)
            tipo_esq: Tipo do operando esquerdo
            tipo_dir: Tipo do operando direito
            linha: Número da linha

        Returns:
            Tipo resultante ou None se erro
        """

        # Operadores de divisão inteira e resto só trabalham com inteiros
        if operador in ("//", "%"):
            if tipo_esq != "int" or tipo_dir != "int":
                self.erros_semanticos.append(
                    f"Linha {linha}: Operador '{operador}' requer operandos inteiros. "
                    f"Recebeu: {tipo_esq} {operador} {tipo_dir}"
                )
                return None
            return "int"

        # Operadores aritméticos normais
        if operador in ("+", "-", "*", "/", "^", "|"):
            if tipo_esq is None or tipo_dir is None:
                return "float"  # Padrão

            # Se algum é float, resultado é float
            if tipo_esq == "float" or tipo_dir == "float":
                return "float"

            # Se ambos são int
            if tipo_esq == "int" and tipo_dir == "int":
                return "int" if operador != "/" else "float"

            return "float"

        # Operadores relacionais retornam bool
        if operador in (">", "<", ">=", "<=", "==", "!="):
            if tipo_esq is None or tipo_dir is None:
                return "bool"
            return "bool"

        return None