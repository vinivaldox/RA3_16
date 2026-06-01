# Nome | apelido no Github | link do Github
# Andrei de Carvalho Bley | andrei-bley | https://github.com/andrei-bley
# Vinicius Cordeiro Vogt | vinivaldox | https://github.com/vinivaldox
# Vitor Matias Percegona Bilbao | vitormpbilbao | https://github.com/vitormpbilbao

# Grupo: RA2 15

#Responsável: Vitor Bilbao

def construirGramatica():
    return {
        "Programa": [
            ["PARENTESIS_ESQ", "START", "PARENTESIS_DIR", "ListaOuFim"]
        ],
        "ListaOuFim": [
            ["PARENTESIS_ESQ", "ConteudoOuFim"]
        ],
        "ConteudoOuFim": [
            ["END", "PARENTESIS_DIR"],
            ["Conteudo", "PARENTESIS_DIR", "ListaOuFim"]
        ],
        "Comando": [
            ["PARENTESIS_ESQ", "Conteudo", "PARENTESIS_DIR"]
        ],
        "Conteudo": [
            ["Elemento", "RestoConteudo"]
        ],
        "RestoConteudo": [
            ["Elemento", "Cauda"],
            ["RES"],
            ["EPSILON"]
        ],
        "Cauda": [
            ["OPERADOR"], ["MEM"], ["IF"], ["WHILE"]
        ],
        "Elemento": [
            ["NUMERO"], 
            ["VARIAVEL"], 
            ["Comando"]
        ]
    }
def calcularFirst(gramatica):
    #cria dict
    firsts = {nt: set() for nt in gramatica}
    
    #se n estiver na lista o código assume que é não terminal
    terminais = {
        "PARENTESIS_ESQ", "PARENTESIS_DIR", "START", "END", "EPSILON",
        "RES", "OPERADOR", "MEM", "IF", "WHILE", "NUMERO", "VARIAVEL"
    }
    #roda
    teve_mudanca = True
    while teve_mudanca:
        teve_mudanca = False
        
        for nt, regras in gramatica.items():
            for regra in regras:
                tamanho_antigo = len(firsts[nt])
                for simbolo in regra:
                    if simbolo in terminais: #se achar terminal cai aqui
                        firsts[nt].add(simbolo)
                        break
                    else: #caso encontre um não terminal
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
        for nt_pai, regras in gramatica.items():
            for regra in regras:
                for i, simbolo in enumerate(regra):
                    if simbolo in gramatica:
                        tamanho_antigo = len(follows[simbolo])
                        #se tem a direita
                        if i + 1 < len(regra):
                            proximo_simbolo = regra[i + 1]
                            
                            if proximo_simbolo not in gramatica: #éterminal
                                follows[simbolo].add(proximo_simbolo)
                            else: #n terminal
                                firsts_do_vizinho = firsts[proximo_simbolo]
                                follows[simbolo].update(firsts_do_vizinho - {"EPSILON"})
                                
                                if "EPSILON" in firsts_do_vizinho:
                                    follows[simbolo].update(follows[nt_pai])
                        #herda o follow do pai se for o último símbolo
                        else:
                            follows[simbolo].update(follows[nt_pai])
                        if len(follows[simbolo]) > tamanho_antigo:
                            teve_mudanca = True

    return follows

def construirTabelaLL1(gramatica, firsts, follows):
    tabela = {nt: {} for nt in gramatica}
    
    terminais = {
        "PARENTESIS_ESQ", "PARENTESIS_DIR", "START", "END", 
        "RES", "OPERADOR", "MEM", "IF", "WHILE", "NUMERO", "VARIAVEL"
    }
    for nt, regras in gramatica.items():
        for regra in regras:
            first_da_regra = set()
            for simbolo in regra:
                if simbolo in terminais or simbolo == "EPSILON":
                    first_da_regra.add(simbolo)
                    break
                else:
                    firsts_do_vizinho = firsts[simbolo]
                    first_da_regra.update(firsts_do_vizinho - {"EPSILON"})
                    if "EPSILON" not in firsts_do_vizinho:
                        break
            else:
                first_da_regra.add("EPSILON")
            for terminal in first_da_regra:
                if terminal != "EPSILON":
                    if terminal in tabela[nt]:
                        print(f"ERRO DE CONFLITO LL(1): Gramática ambígua em {nt} com token {terminal}")
                    tabela[nt][terminal] = regra
            if "EPSILON" in first_da_regra:
                for terminal in follows[nt]:
                    if terminal in tabela[nt]:
                        print(f"ERRO DE CONFLITO LL(1) (FIRST/FOLLOW): em {nt} com token {terminal}")
                    tabela[nt][terminal] = regra

    return tabela

# ==========================================
#              BLOCO DE TESTE
# ==========================================
if __name__ == "__main__":
    gram = construirGramatica()
    firsts = calcularFirst(gram)
    follows = calcularFollow(gram, firsts)
    tabela = construirTabelaLL1(gram, firsts, follows)
    
    print("=== TABELA LL(1) GERADA COM SUCESSO ===")
    for nt, mapeamento in tabela.items():
        print(f"\n[{nt}]:")
        for terminal, regra in mapeamento.items():
            print(f"  Se ler '{terminal}' -> Usar regra: {regra}")