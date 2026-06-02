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


def main():
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso correto: python main.py <arquivo_teste.txt>")
        sys.exit(1)

    nome_arquivo = sys.argv[1]

    print(f"\n{'=' * 70}")
    print("COMPILADOR RPN > ASSEMBLY ARMv7 (Fase 3)")
    print("Analisador Semantico + Geracao de Codigo")
    print(f"{'=' * 70}\n")

    try:
        # ==========================================
        # PASSO 1: ANALISADOR LÉXICO
        # ==========================================
        print("[1/6] Tokenizando arquivo fonte...")
        tokens_brutos = lerTokens(nome_arquivo)
        tokens_planificados = [token for linha in tokens_brutos for token in linha]
        print(f"[+] OK! {len(tokens_planificados)} tokens lidos.")

        # DEBUG: Mostrar primeiros 20 tokens
        if len(tokens_planificados) > 0:
            print(
                f"  Primeiros 5 tokens: {[(t.tipo, t.valor) for t in tokens_planificados[:5]]}\n"
            )

        # ==========================================
        # PASSO 2: GRAMÁTICA LL(1)
        # ==========================================
        print("[2/6] Carregando a Gramática LL(1)...")
        gramatica = construirGramatica()
        print("[+] OK! Gramática fatorada carregada.\n")

        # ==========================================
        # PASSO 3: ANÁLISE SINTÁTICA
        # ==========================================
        print("[3/6] Executando Análise Sintática (Parsing)...")

        # Converter tokens para formato esperado
        tokens_dict = converter_tokens(tokens_planificados)

        resultado_parser = parsear(tokens_dict, gramatica)

        if not resultado_parser["sucesso"]:
            print("[!] ERRO SINTÁTICO! O código possui erros:")
            for r in resultado_parser["resultados"]:
                if not r["sucesso"]:
                    for erro in r["erros"]:
                        print(
                            f"  > Linha {erro.get('numero_comando', '?')}: {erro.get('mensagem', erro)}"
                        )
            sys.exit(1)

        print(f"[+] OK! {resultado_parser['resumo']}.\n")

        # ==========================================
        # PASSO 4: ÁRVORE SINTÁTICA
        # ==========================================
        print("[4/6] Gerando Árvore Sintática (AST)...")
        arvores = gerarArvore(resultado_parser)
        salvar_arvore_json(arvores, "arvore.json")

        # Validar estrutura do programa
        if arvores and arvores[0] is not None:
            if not validar_programa(arvores[0]):
                print(
                    "[!] ERRO: Programa deve começar com (START) e terminar com (END)"
                )
                sys.exit(1)
            print("[+] OK! Árvore salva em 'arvore.json'")
            print("   Estrutura da árvore:")
            print(imprimir_arvore(arvores[0], prefixo="   "))
        else:
            print("[!] ERRO: Árvore sintática vazia")
            sys.exit(1)
        print("")

        # ==========================================
        # PASSO 5: ANÁLISE SEMÂNTICA
        # ==========================================
        print("[5/6] Executando Análise Semântica...")
        analisador = AnalisadorSemantico()
        sucesso_semantico, arvore_aumentada, erros_semanticos = analisador.analisar(
            arvores[0]
        )

        # Salvar artefatos semânticos
        analisador.tabela_simbolos.salvar_markdown("tabela_simbolos.md")
        analisador.tabela_simbolos.salvar_json("tabela_simbolos.json")
        analisador.salvar_arvore_aumentada(arvore_aumentada, "arvore_aumentada.json")

        # Relatório de análise semântica
        print(analisador.gerar_relatorio())

        if not sucesso_semantico:
            print("\n[!] ERRO SEMÂNTICO! A geração de Assembly foi BLOQUEADA")
            print("Erros encontrados:")
            for erro in erros_semanticos:
                print(f"  > {erro}")
            sys.exit(1)

        print("[+] OK! Análise semântica concluída sem erros.\n")

        # ==========================================
        # PASSO 6: GERAÇÃO DE CÓDIGO ASSEMBLY
        # ==========================================
        print("[6/6] Traduzindo para Assembly ARMv7...")

        # Recriar estrutura de árvore para gerador
        arvores_para_gerar = [arvore_aumentada]
        codigo_assembly = gerarAssembly(arvores_para_gerar)

        with open("saida.s", "w", encoding="utf-8") as f:
            f.write(codigo_assembly)

        print("[+] OK! Código Assembly gerado e salvo em 'saida.s'.\n")

        # ==========================================
        # RESUMO FINAL
        # ==========================================
        print(f"{'=' * 70}")
        print("COMPILAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"{'=' * 70}")
        print("\nArquivos gerados:")
        print("  - arvore.json              (Árvore Sintática)")
        print("  - arvore_aumentada.json    (Árvore com Anotações Semânticas)")
        print("  - tabela_simbolos.md       (Tabela de Símbolos - Markdown)")
        print("  - tabela_simbolos.json     (Tabela de Símbolos - JSON)")
        print("  - saida.s                  (Código Assembly ARMv7)")
        print("")

    except FileNotFoundError:
        print(f"\n[!] ERRO: Arquivo '{nome_arquivo}' não encontrado.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] ERRO INESPERADO: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
