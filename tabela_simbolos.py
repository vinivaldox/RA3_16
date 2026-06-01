# Nome | apelido no Github | link do Github
# Andrei de Carvalho Bley | andrei-bley | https://github.com/andrei-bley
# Vinicius Cordeiro Vogt | vinivaldox | https://github.com/vinivaldox
# Vitor Matias Percegona Bilbao | vitormpbilbao | https://github.com/vitormpbilbao

# Grupo: RA3_16

# MÓDULO: Tabela de Símbolos

import json
from dataclasses import dataclass


@dataclass
class Simbolo:
    """Representa uma variável na tabela de símbolos."""

    nome: str
    tipo: str  # "int", "float", "bool"
    linha_definicao: int
    linha_ultimo_uso: int
    escopo: str = "global"
    inicializado: bool = False

    def to_dict(self):
        return {
            "nome": self.nome,
            "tipo": self.tipo,
            "linha_definicao": self.linha_definicao,
            "linha_ultimo_uso": self.linha_ultimo_uso,
            "escopo": self.escopo,
            "inicializado": self.inicializado,
        }


class TabelaSimbolos:
    """Gerencia a tabela de símbolos para uma análise semântica."""

    def __init__(self):
        self.simbolos: dict[str, Simbolo] = {}
        self.erros_semanticos: list = []
        self.avisos: list = []

    def definir_variavel(self, nome: str, tipo: str, linha: int) -> bool:
        """Define uma variável na tabela.

        Args:
            nome: Nome da variável (ex: "A", "VAR")
            tipo: Tipo da variável ("int", "float", "bool")
            linha: Número da linha onde foi definida

        Returns:
            True se definido com sucesso, False se já existia
        """
        if nome == "RES":
            self.erros_semanticos.append(
                f"Linha {linha}: 'RES' é uma palavra-chave reservada e não pode ser usada como variável."
            )
            return False

        if nome in self.simbolos:
            # Verificar se é redefinição incompatível
            simbolo_existente = self.simbolos[nome]
            if simbolo_existente.tipo != tipo:
                self.erros_semanticos.append(
                    f"Linha {linha}: Variável '{nome}' já foi definida como tipo '{simbolo_existente.tipo}' "
                    f"(definida na linha {simbolo_existente.linha_definicao}). "
                    f"Tentativa de redefinição com tipo incompatível '{tipo}'."
                )
                return False
            else:
                self.avisos.append(
                    f"Linha {linha}: Variável '{nome}' foi redefinida (primeira definição na linha {simbolo_existente.linha_definicao})."
                )

        self.simbolos[nome] = Simbolo(
            nome=nome,
            tipo=tipo,
            linha_definicao=linha,
            linha_ultimo_uso=linha,
            inicializado=True,
        )
        return True

    def usar_variavel(self, nome: str, linha: int) -> None | str:
        """Usa uma variável, retornando seu tipo."""
        if nome in self.simbolos:
            simbolo = self.simbolos[nome]
            simbolo.linha_ultimo_uso = linha
            return simbolo.tipo
        else:
            return None

    def inferir_tipo(self, nome: str, tipo_inferido: str, linha: int) -> bool:
        """Infere o tipo de uma variável se ainda não foi definida."""
        if nome == "RES":
            return True  # RES não tem tipo fixo

        if nome not in self.simbolos:
            self.simbolos[nome] = Simbolo(
                nome=nome,
                tipo=tipo_inferido,
                linha_definicao=linha,
                linha_ultimo_uso=linha,
                inicializado=False,
            )
            return True
        else:
            # Verificar compatibilidade
            simbolo = self.simbolos[nome]
            if simbolo.tipo != tipo_inferido:
                self.avisos.append(
                    f"Linha {linha}: Variável '{nome}' tem tipo '{simbolo.tipo}', "
                    f"mas foi usada em contexto que espera '{tipo_inferido}'."
                )
        return True

    def obter_tipo(self, nome: str) -> None | str:
        """Obtém o tipo de uma variável."""
        if nome in self.simbolos:
            return self.simbolos[nome].tipo
        return None

    def salvar_markdown(self, nome_arquivo: str = "tabela_simbolos.md"):
        """Salva a tabela de símbolos em formato Markdown."""
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write("# Tabela de Símbolos\n\n")
            f.write("| Variável | Tipo | Definida em | Último Uso | Escopo |\n")
            f.write("|----------|------|-------------|------------|--------|\n")

            for nome, simbolo in sorted(self.simbolos.items()):
                f.write(
                    f"| {simbolo.nome} | {simbolo.tipo} | "
                    f"Linha {simbolo.linha_definicao} | "
                    f"Linha {simbolo.linha_ultimo_uso} | {simbolo.escopo} |\n"
                )

            if self.erros_semanticos:
                f.write("\n## Erros Semânticos\n\n")
                for erro in self.erros_semanticos:
                    f.write(f"- {erro}\n")

            if self.avisos:
                f.write("\n## Avisos\n\n")
                for aviso in self.avisos:
                    f.write(f"- {aviso}\n")

    def salvar_json(self, nome_arquivo: str = "tabela_simbolos.json"):
        """Salva a tabela de símbolos em formato JSON."""
        dados = {
            "simbolos": {
                nome: simbolo.to_dict() for nome, simbolo in self.simbolos.items()
            },
            "erros": self.erros_semanticos,
            "avisos": self.avisos,
        }
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    def tem_erros(self) -> bool:
        """Verifica se há erros semânticos."""
        return len(self.erros_semanticos) > 0

    def relatorio(self) -> str:
        """Gera um relatório textual da tabela."""
        relatorio = "=== TABELA DE SÍMBOLOS ===\n\n"

        if not self.simbolos:
            relatorio += "Nenhuma variável definida.\n"
        else:
            relatorio += "Variáveis definidas:\n"
            for nome, simbolo in sorted(self.simbolos.items()):
                relatorio += (
                    f"  {simbolo.nome:10} | Tipo: {simbolo.tipo:6} | "
                    f"Definida: L{simbolo.linha_definicao:3} | "
                    f"Último uso: L{simbolo.linha_ultimo_uso:3}\n"
                )

        if self.erros_semanticos:
            relatorio += f"\nERROS SEMÂNTICOS ({len(self.erros_semanticos)}):\n"
            for erro in self.erros_semanticos:
                relatorio += f"  [!] {erro}\n"

        if self.avisos:
            relatorio += f"\nAVISOS ({len(self.avisos)}):\n"
            for aviso in self.avisos:
                relatorio += f"  [*] {aviso}\n"

        return relatorio
