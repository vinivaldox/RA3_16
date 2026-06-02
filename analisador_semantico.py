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
        self.stack_rpn = []  # Stack de tipos para expressões RPN

    def analisar(self, arvore: NoArvore) -> Tuple[bool, NoArvore, list]:
        """Realiza análise semântica completa.

        Args:
            arvore: Árvore sintática a ser analisada

        Returns:
            Tupla (sucesso, arvore_aumentada, erros)
        """
        arvore_aumentada = self._clonar_no(arvore)
        self._analisar_no(arvore_aumentada)

        todos_erros = self.tabela_simbolos.erros_semanticos + self.erros_semanticos
        sucesso = len(todos_erros) == 0

        return (sucesso, arvore_aumentada, todos_erros)

    # ------------------------------------------------------------------
    # CLONAGEM
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # TRAVESSIA PRINCIPAL
    # ------------------------------------------------------------------

    def _analisar_no(self, no: NoArvore) -> Optional[str]:
        """Analisa um nó da árvore retornando seu tipo inferido."""
        if no is None:
            return None

        if no.tipo == "terminal":
            return self._analisar_terminal(no)

        # Tratamento especial para Conteudo: detecta contexto MEM / IF / WHILE
        if no.rotulo == "Conteudo":
            return self._analisar_conteudo_contextual(no)

        # Padrão: visita filhos em sequência
        ultimo_tipo = None
        for filho in no.filhos:
            tipo = self._analisar_no(filho)
            if tipo:
                ultimo_tipo = tipo
        return ultimo_tipo

    # ------------------------------------------------------------------
    # ANÁLISE CONTEXTUAL DE Conteudo
    # ------------------------------------------------------------------

    def _analisar_conteudo_contextual(self, no: NoArvore) -> Optional[str]:
        """Analisa Conteudo com consciência de contexto.

        Identifica três padrões:
          1. Atribuição MEM  : (valor VAR MEM) → define VAR sem chamar usar_variavel
          2. Controle IF/WHILE: (cond corpo IF/WHILE) → valida que cond seja bool
          3. Expressão normal : tudo o mais
        """
        if len(no.filhos) < 2:
            return self._analisar_filhos(no)

        elem_val = no.filhos[0]   # Elemento (valor ou condição)
        resto = no.filhos[1]       # RestoConteudo

        cauda_tipo, var_nome, cauda_linha = self._inspecionar_cauda(resto)

        if cauda_tipo == "MEM":
            return self._processar_mem(elem_val, resto, var_nome)

        if cauda_tipo in ("IF", "WHILE"):
            return self._processar_controle(elem_val, resto, cauda_tipo, cauda_linha)

        # Expressão normal: avalia todos os filhos em sequência
        return self._analisar_filhos(no)

    def _inspecionar_cauda(self, resto: NoArvore) -> Tuple[Optional[str], Optional[str], int]:
        """Inspeciona o terminal dentro de Cauda em RestoConteudo.

        Returns:
            (tipo_cauda, var_nome_se_mem, linha_cauda)
            tipo_cauda: 'MEM' | 'IF' | 'WHILE' | 'OPERADOR' | None
        """
        if resto.rotulo != "RestoConteudo":
            return (None, None, 0)

        for filho in resto.filhos:
            if filho.rotulo == "Cauda":
                for terminal in filho.filhos:
                    if terminal.tipo == "terminal":
                        rotulo = terminal.rotulo
                        linha = terminal.linha

                        if rotulo == "MEM":
                            var_nome = self._extrair_variavel_elemento(resto)
                            return ("MEM", var_nome, linha)

                        if rotulo in ("IF", "WHILE"):
                            return (rotulo, None, linha)

                        # OPERADOR ou qualquer outro terminal
                        return ("OPERADOR", None, 0)

        return (None, None, 0)

    def _extrair_variavel_elemento(self, resto: NoArvore) -> Optional[str]:
        """Extrai o nome da variável do Elemento dentro de RestoConteudo."""
        for filho in resto.filhos:
            if filho.rotulo == "Elemento":
                for neto in filho.filhos:
                    if neto.tipo == "terminal" and neto.rotulo == "VARIAVEL":
                        return neto.valor
        return None

    # ------------------------------------------------------------------
    # PROCESSAMENTO DE ATRIBUIÇÃO (valor VAR MEM)
    # ------------------------------------------------------------------

    def _processar_mem(
        self,
        elem_val: NoArvore,
        resto: NoArvore,
        var_nome: Optional[str],
    ) -> Optional[str]:
        """Processa atribuição de memória sem chamar usar_variavel no destino.

        Avalia a expressão de valor, infere seu tipo e define a variável.
        """
        # 1. Avaliar o valor (expressão à esquerda do VAR MEM)
        tipo_valor = self._analisar_no(elem_val)
        tipo_final = tipo_valor if tipo_valor else "float"

        if var_nome:
            linha_var = self._extrair_linha_variavel(resto)

            # 2. Anotar o nó VARIAVEL destino na árvore (sem passar por usar_variavel)
            self._anotar_no_variavel_destino(resto, tipo_final)

            # 3. Registrar na tabela de símbolos
            self.tabela_simbolos.definir_variavel(var_nome, tipo_final, linha_var)

        # 4. Anotar o terminal MEM
        for filho in resto.filhos:
            if filho.rotulo == "Cauda":
                for t in filho.filhos:
                    if t.tipo == "terminal" and t.rotulo == "MEM":
                        t.categoria_semantica = "atribuicao"

        # MEM não produz valor na pilha de expressão
        return None

    def _extrair_linha_variavel(self, resto: NoArvore) -> int:
        for filho in resto.filhos:
            if filho.rotulo == "Elemento":
                for neto in filho.filhos:
                    if neto.tipo == "terminal" and neto.rotulo == "VARIAVEL":
                        return neto.linha
        return 0

    def _anotar_no_variavel_destino(self, resto: NoArvore, tipo: str):
        for filho in resto.filhos:
            if filho.rotulo == "Elemento":
                for neto in filho.filhos:
                    if neto.tipo == "terminal" and neto.rotulo == "VARIAVEL":
                        neto.tipo_semantico = tipo
                        neto.categoria_semantica = "atribuicao_destino"

    # ------------------------------------------------------------------
    # PROCESSAMENTO DE ESTRUTURAS DE CONTROLE (IF / WHILE)
    # ------------------------------------------------------------------

    def _processar_controle(
        self,
        cond: NoArvore,
        resto: NoArvore,
        tipo_controle: str,
        linha: int,
    ) -> Optional[str]:
        """Processa IF ou WHILE, validando que a condição é do tipo bool."""

        # 1. Avaliar condição (separada do corpo — pilha isolada)
        pilha_salva = self.stack_rpn[:]
        self.stack_rpn = []

        tipo_cond = self._analisar_no(cond)

        self.stack_rpn = pilha_salva  # restaura pilha do contexto externo

        # 2. Validar bool
        self._validar_estrutura_controle(tipo_cond, tipo_controle, linha)

        # 3. Avaliar corpo (Elemento em RestoConteudo) — variáveis devem ser válidas
        for filho in resto.filhos:
            if filho.rotulo == "Elemento":
                self._analisar_no(filho)

        return None

    def _validar_estrutura_controle(
        self,
        tipo_condicao: Optional[str],
        tipo_estrutura: str,
        linha: int,
    ) -> bool:
        """Valida que condição de IF/WHILE seja do tipo bool.

        Regra: Γ ⊢ cond : bool ⟹ Γ ⊢ (cond corpo IF/WHILE) : ok   [T-IF / T-WHILE]
        """
        if tipo_condicao != "bool":
            tipo_recebido = tipo_condicao if tipo_condicao else "desconhecido"
            self.erros_semanticos.append(
                f"Linha {linha}: Estrutura '{tipo_estrutura}' requer condição do tipo "
                f"'bool', mas recebeu '{tipo_recebido}'. "
                f"Use um operador relacional (>, <, >=, <=, ==, !=) para produzir bool."
            )
            return False
        return True

    # ------------------------------------------------------------------
    # ANÁLISE DE TERMINAIS
    # ------------------------------------------------------------------

    def _analisar_terminal(self, no: NoArvore) -> Optional[str]:
        """Analisa um nó terminal (folha da árvore)."""

        if no.rotulo == "NUMERO":
            if "." in no.valor:
                no.tipo_semantico = "float"
                tipo = "float"
            else:
                no.tipo_semantico = "int"
                tipo = "int"
            self.stack_rpn.append(("numero", no.valor, tipo, no.linha))
            return tipo

        elif no.rotulo == "VARIAVEL":
            # Apenas leituras chegam aqui (alvos de MEM são tratados em _processar_mem)
            tipo = self.tabela_simbolos.usar_variavel(no.valor, no.linha)
            tipo_efetivo = tipo if tipo else "float"  # continua análise mesmo com erro

            self.stack_rpn.append(("variavel", no.valor, tipo_efetivo, no.linha))
            no.tipo_semantico = tipo_efetivo
            no.categoria_semantica = "leitura"
            return tipo  # retorna None se não definida, propagando a ausência de tipo

        elif no.rotulo == "OPERADOR":
            no.categoria_semantica = "operacao"
            tipo_resultado = None

            if len(self.stack_rpn) >= 2:
                tipo_dir = self.stack_rpn[-1][2]   # topo: operando direito
                tipo_esq = self.stack_rpn[-2][2]   # penúltimo: operando esquerdo
                tipo_resultado = self._validar_operacao(
                    no.valor, tipo_esq, tipo_dir, no.linha
                )

            if tipo_resultado:
                # Substituir os dois operandos pelo resultado
                if len(self.stack_rpn) >= 2:
                    self.stack_rpn.pop()
                    self.stack_rpn.pop()
                self.stack_rpn.append(("resultado", no.valor, tipo_resultado, no.linha))
                no.tipo_semantico = tipo_resultado

            return tipo_resultado

        elif no.rotulo == "MEM":
            # Apenas anotação — definição já foi feita em _processar_mem
            no.categoria_semantica = "atribuicao"
            return None

        elif no.rotulo == "RES":
            no.tipo_semantico = "float"
            no.categoria_semantica = "referencia_resultado"
            self.stack_rpn.append(("resultado", "RES", "float", no.linha))
            return "float"

        elif no.rotulo in ("START", "END"):
            no.categoria_semantica = "controle_programa"
            return None

        elif no.rotulo == "IF":
            # Validação já foi feita em _processar_controle
            no.categoria_semantica = "condicional"
            return None

        elif no.rotulo == "WHILE":
            # Validação já foi feita em _processar_controle
            no.categoria_semantica = "laco"
            return None

        return None

    # ------------------------------------------------------------------
    # VALIDAÇÃO DE OPERAÇÕES
    # ------------------------------------------------------------------

    def _validar_operacao(
        self,
        operador: str,
        tipo_esq: Optional[str],
        tipo_dir: Optional[str],
        linha: int,
    ) -> Optional[str]:
        """Valida uma operação e retorna o tipo resultante.

        Regras (cálculo de sequentes):
          [T-INT-DIV]  Γ ⊢ a:int, b:int  ⟹  Γ ⊢ (a b //):int
          [T-MOD]      Γ ⊢ a:int, b:int  ⟹  Γ ⊢ (a b %):int
          [T-ARITH]    Γ ⊢ a:T1, b:T2    ⟹  Γ ⊢ (a b op):float  (se T1 ou T2 = float)
          [T-ARITH-II] Γ ⊢ a:int, b:int  ⟹  Γ ⊢ (a b /):float   (/ sempre float)
          [T-RELOP]    Γ ⊢ a:T1, b:T2    ⟹  Γ ⊢ (a b rel):bool
        """
        # Divisão inteira e módulo: ambos operandos devem ser int
        if operador in ("//", "%"):
            if tipo_esq != "int" or tipo_dir != "int":
                self.erros_semanticos.append(
                    f"Linha {linha}: Operador '{operador}' requer operandos inteiros. "
                    f"Recebeu: {tipo_esq} {operador} {tipo_dir}."
                )
                return None
            return "int"

        # Operadores aritméticos padrão
        if operador in ("+", "-", "*", "/", "^", "|"):
            if tipo_esq is None or tipo_dir is None:
                return "float"  # prossegue com tipo padrão

            # Mistura de bool com aritmética é inválida
            if tipo_esq == "bool" or tipo_dir == "bool":
                self.erros_semanticos.append(
                    f"Linha {linha}: Operador aritmético '{operador}' não pode ser "
                    f"aplicado a operandos do tipo bool. "
                    f"Recebeu: {tipo_esq} {operador} {tipo_dir}."
                )
                return None

            # / sempre resulta em float; int+int resulta em int para demais ops
            if operador == "/":
                return "float"
            if tipo_esq == "float" or tipo_dir == "float":
                return "float"
            return "int"

        # Operadores relacionais: sempre retornam bool
        if operador in (">", "<", ">=", "<=", "==", "!="):
            if tipo_esq == "bool" or tipo_dir == "bool":
                self.erros_semanticos.append(
                    f"Linha {linha}: Operador relacional '{operador}' aplicado a "
                    f"operandos do tipo bool não é suportado. "
                    f"Recebeu: {tipo_esq} {operador} {tipo_dir}."
                )
                return None
            return "bool"

        return None

    # ------------------------------------------------------------------
    # UTILITÁRIOS
    # ------------------------------------------------------------------

    def _analisar_filhos(self, no: NoArvore) -> Optional[str]:
        """Avalia filhos em sequência, retornando o último tipo não-nulo."""
        ultimo_tipo = None
        for filho in no.filhos:
            tipo = self._analisar_no(filho)
            if tipo:
                ultimo_tipo = tipo
        return ultimo_tipo

    # ------------------------------------------------------------------
    # ARTEFATOS
    # ------------------------------------------------------------------

    def salvar_arvore_aumentada(
        self, arvore: NoArvore, nome_arquivo: str = "arvore_aumentada.json"
    ):
        """Salva a árvore aumentada em JSON."""
        import json

        with open(nome_arquivo, "w", encoding="utf-8") as f:
            json.dump(arvore.serializar(), f, ensure_ascii=False, indent=2)

    def gerar_relatorio(self) -> str:
        """Gera relatório completo da análise semântica."""
        relatorio = "=" * 60 + "\n"
        relatorio += "RELATÓRIO DE ANÁLISE SEMÂNTICA\n"
        relatorio += "=" * 60 + "\n\n"

        relatorio += self.tabela_simbolos.relatorio()

        if self.erros_semanticos:
            relatorio += f"\nERROS DE TIPAGEM ({len(self.erros_semanticos)}):\n"
            for erro in self.erros_semanticos:
                relatorio += f"  [!] {erro}\n"

        return relatorio


def processar_entrada_semantica(
    arquivo: str, arvore_sintativa: NoArvore
) -> Tuple[bool, NoArvore]:
    """Processa a análise semântica completa de um arquivo."""
    analisador = AnalisadorSemantico()
    sucesso, arvore_aumentada, erros = analisador.analisar(arvore_sintativa)

    analisador.tabela_simbolos.salvar_markdown("tabela_simbolos.md")
    analisador.tabela_simbolos.salvar_json("tabela_simbolos.json")
    analisador.salvar_arvore_aumentada(arvore_aumentada, "arvore_aumentada.json")

    print(analisador.gerar_relatorio())

    return sucesso, arvore_aumentada
