# RA3_16 - Compilador RPN → ARMv7 Assembly (Fase 3)

## Informações do Projeto

- **Disciplina**: Linguagens Formais e Compiladores
- **Professor**: FRANK COELHO DE ALCANTARA
- **Instituição**: PUCPR (Pontifícia Universidade Católica do Paraná)
- **Grupo**: RA3_16

  - Andrei de Carvalho Bley | andrei-bley | https://github.com/andrei-bley
  - Vinicius Cordeiro Vogt | vinivaldox | https://github.com/vinivaldox
  - Vitor Matias Percegona Bilbao | vitormpbilbao | https://github.com/vitormpbilbao

- **Fase**: 3 - Analisador Semântico + Geração de Código Assembly

## Descrição Geral

Implementação completa de um compilador para uma linguagem baseada em **Notação Polonesa Inversa (RPN)** com suporte a:
- **Estruturas de controle** (IF/WHILE) com validação de tipos
- **Sistema de tipos estático e forte** (int, float, bool)
- **Análise semântica** com inferência de tipos e detecção de erros
- **Tabela de símbolos** com rastreamento de variáveis
- **Geração de código Assembly ARMv7** para a arquitetura **Cpulator-ARMv7 DEC1-SOC(v16.1)**

## Características da Fase 3

### 1. **Tratamento de Comentários**
- Comentários delimitados por `*{` e `}*`
- Podem aparecer em qualquer lugar do código (linhas inteiras, fim de linhas, entre expressões)
- Automaticamente removidos na fase léxica, preservando informações de linha para erros

### 2. **Análise Semântica Contextual**
- **Sistema de Tipos Estático e Forte**: 
  - `int`: números inteiros (sem ponto decimal)
  - `float`: números reais IEEE 754 (com ponto decimal)
  - `bool`: resultados de operações relacionais
- **Inferência Inteligente de Tipos**: tipos são inferidos do contexto de uso
- **Análise Contextual**: reconhece padrões semânticos distintos:
  - Atribuição: `(valor VAR MEM)` - define VAR
  - Controle: `(condição corpo IF/WHILE)` - valida tipo bool
  - Expressões: operações aritméticas e relacionais

### 3. **Validação de Operações**
- **Aritméticas**: `+`, `-`, `*`, `^`, `|`
  - Aceitam int e float com promoção automática a float quando necessário
- **Divisão Real** (`/`): sempre resulta em float
- **Divisão Inteira** (`//`) e **Módulo** (`%`): requerem **APENAS** operandos inteiros
- **Operadores Relacionais**: `>`, `<`, `>=`, `<=`, `==`, `!=`
  - Sempre retornam `bool`, não aceitam operandos bool
- **Operações em Estruturas de Controle**:
  - IF/WHILE requerem condição do tipo `bool`
  - Bloqueiam geração de Assembly se tipo for incorreto

### 4. **Tabela de Símbolos com Rastreamento Completo**
- Rastreamento de todas as variáveis definidas e usadas
- Informações coletadas:
  - Nome da variável
  - Tipo inferido (int, float, bool)
  - Linha de definição
  - Última linha de uso
  - Status de inicialização
- Detecção automática de:
  - Variáveis usadas sem definição prévia
  - Redefinições com tipos compatíveis (avisos)
  - Variáveis possivelmente não inicializadas
- Exportação em **Markdown** (formato legível) e **JSON** (processamento automático)

### 5. **Árvore Sintática Aumentada com Anotações Semânticas**
- Cada nó da árvore recebe anotações:
  - **Tipo semântico**: int, float, bool ou nulo
  - **Categoria semântica**: operação, atribuição, leitura, atribuição_destino, controle_programa, condicional, laco, referencia_resultado
  - **Informações de linha**: para relatórios de erro precisos
- Árvore salva em JSON para análise posterior e debugging

### 6. **Validação Rigorosa com Bloqueio de Assembly**
- Geração de Assembly é **BLOQUEADA** se houver qualquer erro
- Mensagens de erro estruturadas incluem:
  - Número de linha exato
  - Contexto do erro
  - Sugestões de correção
- Relatório completo de análise semântica impresso antes de qualquer operação

## Estrutura de Arquivos

```
RA3_16/
├── main.py                      # Orquestrador do pipeline (6 fases)
├── analisador_lexico.py         # Tokenização + remoção de comentários
├── gramatica.py                 # Gramática LL(1) fatorada
├── parsear.py                   # Parser recursivo descendente
├── analisador_semantico.py      # Análise semântica com tipagem (CORRIGIDO)
├── tabela_simbolos.py           # Gerenciamento de símbolos e tipos
├── gerarAssembly.py             # Gerador de código ARMv7 com VFP
│
├── teste_1.txt                  # Teste: operadores + MEM + IF/WHILE
├── teste_2.txt                  # Teste: comentários + controle fluxo
├── teste_3.txt                  # Teste: divisão inteira, módulo, aninhamento
├── teste_simples_valido.txt     # Teste: programa mínimo válido
│
├── arvore.json                  # (gerado) Árvore sintática
├── arvore_aumentada.json        # (gerado) Árvore com anotações semânticas
├── tabela_simbolos.md           # (gerado) Tabela em Markdown
├── tabela_simbolos.json         # (gerado) Tabela em JSON
├── saida.s                      # (gerado) Código Assembly ARMv7 final
│
└── README.md                    # Este arquivo
```

## Como Executar

### Pré-requisitos
- Python 3.8+
- Nenhuma dependência externa necessária

### Compilar um Programa

```bash
python main.py <arquivo_teste.txt>
```

**Exemplos:**
```bash
python main.py teste_simples_valido.txt
python main.py teste_1.txt
python main.py teste_2.txt
python main.py teste_3.txt
```

### Saída Esperada

O compilador imprime 6 fases de execução:
```
[1/6] Tokenizando arquivo fonte...      ← Análise léxica
[2/6] Carregando a Gramática LL(1)...   ← Carregamento
[3/6] Executando Análise Sintática...   ← Parsing
[4/6] Gerando Árvore Sintática (AST)... ← Construção de árvore
[5/6] Executando Análise Semântica...   ← Tipagem + validação
[6/6] Traduzindo para Assembly ARMv7... ← Geração de código
```

Se qualquer erro for detectado na fase 5, a fase 6 é **bloqueada** automaticamente.

## Artefatos Gerados

### 1. **arvore.json**
- Árvore sintática em formato JSON
- Contém estrutura completa do programa com todos os nós (terminais e não-terminais)
- Útil para debugging do parser

### 2. **arvore_aumentada.json**
- Árvore sintática com anotações semânticas completas
- Cada nó contém:
  - `tipo_semantico`: int | float | bool | null
  - `categoria_semantica`: operacao, atribuicao, leitura, etc.
  - `linha`: número da linha para rastreamento de erros
- Salva mesmo quando há erros (útil para análise)

### 3. **tabela_simbolos.md**
- Tabela de símbolos em formato Markdown legível
- Seções:
  - **Variáveis Definidas**: nome | tipo | linha de definição | último uso
  - **Erros Semânticos**: lista detalhada com números de linha
  - **Avisos**: redefinições, tipos compatíveis

### 4. **tabela_simbolos.json**
- Mesmas informações em JSON para processamento automático
- Estrutura:
  ```json
  {
    "variaveis": [{"nome": "X", "tipo": "int", "definida": 2, "ultimo_uso": 4}],
    "erros": [],
    "avisos": []
  }
  ```

### 5. **saida.s**
- Código Assembly ARMv7 final
- **APENAS gerado se programa for 100% válido**
- Pronto para execução no Cpulator-ARMv7 DEC1-SOC(v16.1)
- Inclui:
  - Seção de dados com variáveis
  - Instruções VFP para ponto flutuante
  - Instruções de controle de fluxo (branches condicionais)
  - Rotulagem automática de saltos para IF/WHILE

## Gramática EBNF (LL(1) Fatorada)

```ebnf
Programa         ::= "(" START ")" ListaOuFim
ListaOuFim       ::= "(" ConteudoOuFim
ConteudoOuFim    ::= "END" ")" | Conteudo ")" ListaOuFim
Conteudo         ::= Elemento RestoConteudo
RestoConteudo    ::= Elemento Cauda | RES | ε
Elemento         ::= NUMERO | VARIAVEL | Comando
Comando          ::= "(" Conteudo ")"
Cauda            ::= OPERADOR | MEM | IF | WHILE
```

**Fatores Principais**:
- Eliminação de recursão à esquerda em ListaOuFim
- Factorização em Conteudo/RestoConteudo para evitar retrocesso
- Suporte a comentários `*{...}*` em qualquer posição

## Sistema de Tipos (Regras de Inferência)

### Literais
```
─────────────────── [T-INT]
⊢ <inteiro> : int      (ex: 5, 100, -3)

─────────────────── [T-FLOAT]
⊢ <decimal> : float    (ex: 2.5, 3.14, 0.0)
```

### Atribuição
```
Γ ⊢ expr : T
────────────────────── [T-MEM]
Γ ⊢ (expr VAR MEM) → VAR : T   (define VAR com tipo T)
```

### Operações Aritméticas
```
Γ ⊢ e1 : int   Γ ⊢ e2 : int
────────────────────────────── [T-ARITH-II]
Γ ⊢ e1 {+,-,*,^} e2 : int

Γ ⊢ e1 : float ∨ Γ ⊢ e2 : float
────────────────────────────── [T-ARITH-IF]
Γ ⊢ e1 {+,-,*,^} e2 : float

Γ ⊢ e1 : T1   Γ ⊢ e2 : T2   (T1, T2 ∈ {int,float})
────────────────────────────── [T-DIV-REAL]
Γ ⊢ e1 / e2 : float          (/ SEMPRE retorna float)

Γ ⊢ e1 : int   Γ ⊢ e2 : int
────────────────────────────── [T-INT-DIV]
Γ ⊢ e1 // e2 : int
Γ ⊢ e1 % e2 : int
```

### Operações Relacionais
```
Γ ⊢ e1 : T   Γ ⊢ e2 : T   T ∈ {int, float}
────────────────────────────── [T-REL]
Γ ⊢ e1 {>, <, >=, <=, ==, !=} e2 : bool
```

### Estruturas de Controle
```
Γ ⊢ cond : bool   Γ ⊢ corpo : T
────────────────────────────── [T-IF]
Γ ⊢ (cond corpo IF) : T

Γ ⊢ cond : bool   Γ ⊢ corpo : T
────────────────────────────── [T-WHILE]
Γ ⊢ (cond corpo WHILE) : T
```

## Operações Suportadas

### Aritméticas
| Operador | Operandos | Resultado | Regra |
|----------|-----------|-----------|-------|
| `+` | int + int | int | [T-ARITH-II] |
| `+` | float ou misto | float | [T-ARITH-IF] |
| `-` | int + int | int | [T-ARITH-II] |
| `-` | float ou misto | float | [T-ARITH-IF] |
| `*` | int + int | int | [T-ARITH-II] |
| `*` | float ou misto | float | [T-ARITH-IF] |
| `/` | T1, T2 ∈ {int,float} | **float** | [T-DIV-REAL] |
| `//` | int + int | int | [T-INT-DIV] |
| `//` | outro | ❌ ERRO | Requer int |
| `%` | int + int | int | [T-INT-DIV] |
| `%` | outro | ❌ ERRO | Requer int |
| `^` | bases numéricas | numérico | Promoção a float se necessário |
| `\|` | números | promoção | (OR bitwise ou similar) |

### Relacionais
| Operador | Operandos | Resultado | Notas |
|----------|-----------|-----------|-------|
| `>` | T ∈ {int, float} | bool | Rejeita bool |
| `<` | T ∈ {int, float} | bool | Rejeita bool |
| `>=` | T ∈ {int, float} | bool | Rejeita bool |
| `<=` | T ∈ {int, float} | bool | Rejeita bool |
| `==` | T ∈ {int, float} | bool | Rejeita bool |
| `!=` | T ∈ {int, float} | bool | Rejeita bool |

### Comandos Especiais
| Comando | Sintaxe | Semântica | Exemplo |
|---------|--------|-----------|---------|
| Atribuição | `(valor VAR MEM)` | Define VAR com tipo do valor | `(10 X MEM)` define X como int |
| Estrutura IF | `(cond corpo IF)` | Executa corpo se cond = true | `((X 5 >) (X 100 MEM) IF)` |
| Estrutura WHILE | `(cond corpo WHILE)` | Loop enquanto cond = true | `((I 10 <) (corpo) WHILE)` |
| Programa | `(START)` ... `(END)` | Delimitadores do programa | Obrigatórios |

## Exemplos de Programas

### Exemplo 1: Soma Simples
```
(START)
( 10 X MEM )
( 5 Y MEM )
( X Y + )
(END)
```
**Análise**: Define X=10 (int), Y=5 (int), computa X+Y=15 (int)

### Exemplo 2: Com Comentários
```
(START)
*{ Inicializar variáveis }*
( 100 VALOR MEM )
( 7 DIVISOR MEM )
*{ Operações aritméticas }*
( VALOR DIVISOR + )
( VALOR DIVISOR - )
( VALOR DIVISOR / )
*{ Resultado será float }*
(END)
```
**Análise**: Comentários são removidos, operações realizadas normalmente

### Exemplo 3: Divisão Inteira com Validação
```
(START)
( 10 NUM MEM )
( 3 DIV MEM )
( NUM DIV // )
*{ Resultado: 3 (divisão inteira) }*
(END)
```
**Análise**: // requer ambos int, NUM//DIV = 3

### Exemplo 4: WHILE com Estrutura Complexa
```
(START)
( 1 I MEM )
( 0 SOMA MEM )
( ( I 5 <= ) ( ( ( SOMA I + ) SOMA MEM ) ( ( I 1 + ) I MEM ) ) WHILE )
( SOMA )
(END)
```
**Análise**: 
- Inicializa I=1, SOMA=0
- Enquanto I ≤ 5: SOMA += I, I++
- Resultado: 1+2+3+4+5 = 15

### Exemplo 5: IF Condicional
```
(START)
( 10 N MEM )
( 2.5 FATOR MEM )
( ( N 5 > ) ( FATOR N * ) IF )
*{ Se N > 5, multiplica N por FATOR (resultado float) }*
(END)
```
**Análise**:
- N é int, FATOR é float
- Condição: N > 5 produz bool
- Corpo: FATOR * N = float * int = float
- Executa apenas se condição for true

## Tratamento de Erros

### Erros Léxicos
```
[!] ERRO: Comentário não fechado na linha X
[!] ERRO: Caractere inválido 'char' na linha X
```

### Erros Sintáticos
```
[!] ERRO SINTÁTICO (Linha X): Parêntese desbalanceado
[!] ERRO SINTÁTICO (Linha X): Token inesperado 'TOKEN'
[!] ERRO SINTÁTICO (Linha X): Estrutura de programa inválida (sem START/END)
```

### Erros Semânticos (Bloqueiam Assembly)
```
[!] Linha X: Variável 'A' usada antes de ser definida. Defina-a primeiro com: (valor A MEM).

[!] Linha X: Operador '//' requer operandos inteiros. Recebeu: float // float.

[!] Linha X: Estrutura 'IF' requer condição do tipo 'bool', mas recebeu 'int'.

[!] Linha X: Operador aritmético '*' não pode ser aplicado a operandos do tipo bool.

[!] Linha X: Variável 'A' foi redefinida com tipo incompatível.
```

## Fluxo de Compilação (6 Fases)

```
Arquivo Fonte (teste.txt)
        ↓
[1] Análise Léxica
    • Remove comentários *{...}*
    • Tokeniza em (KEYWORD, NUMERO, VARIAVEL, OPERADOR, etc.)
    • Preserva informações de linha
        ↓
Tokens com metadata
        ↓
[2] Carregamento de Gramática
    • Carrega gramática LL(1) fatorada
    • Computa First/Follow sets
        ↓
[3] Análise Sintática (Parsing)
    • Parser recursivo descendente
    • Consome tokens e constrói árvore
    • Detecta erros de parênteses e estrutura
        ↓
Árvore Sintática (AST)
        ↓
[4] Geração de Árvore
    • Serializa árvore em arvore.json
    • Pronto para inspeção
        ↓
[5] Análise Semântica
    • Análise contextual de Conteudo
    • Inferência de tipos (int/float/bool)
    • Validação de operações
    • Construção de tabela de símbolos
    • Detecção de erros de tipo
    • Geração de relatório
        ↓
VERIFICAR: Há erros semânticos?
    ├─ SIM → BLOQUEAR fase 6, parar
    └─ NÃO → Continuar
        ↓
[6] Geração de Código Assembly ARMv7
    • Traduz árvore anotada para Assembly
    • Usa VFP para operações em ponto flutuante
    • Gera labels para IF/WHILE
    • Escreve em saida.s
        ↓
Arquivo saida.s (Assembly final - pronto para Cpulator)
```

## Validação Rigorosa

A geração de Assembly é **BLOQUEADA** se:
- ✗ Houver erros léxicos (caracteres inválidos, comentários não fechados)
- ✗ Houver erros sintáticos (parênteses desbalanceados, START/END faltando)
- ✗ Houver erros semânticos (tipos incompatíveis, variáveis não definidas, operações inválidas)

Apenas programas **100% válidos** geram Assembly.

**Princípio**: "Fail Fast" — erros são reportados assim que detectados, bloqueando a continuação.

## Responsabilidades do Grupo

O projeto é dividido em componentes com responsabilidades claras:

### Andrei de Carvalho Bley
- **Analisador Léxico** (parte 1): Tokenização básica, reconhecimento de palavras-chave
- **Analisador Léxico** (parte 2): DFA para comentários, remoção, tratamento de erros

### Vinicius Cordeiro Vogt
- **Gramática LL(1)**: Definição da gramática fatorada, First/Follow
- **Parser**: Recursivo descendente com construção de AST
- **Tabela de Símbolos**: Gerenciamento de variáveis, tipos e escopos

### Vitor Matias Percegona Bilbao
- **Análise Semântica** (parte 1): Análise contextual, inferência de tipos
- **Análise Semântica** (parte 2): Validação de operações, relatórios de erro
- **Geração de Assembly**: Tradução para ARMv7 com VFP

### Coordenação Geral
- **Main.py**: Orquestração do pipeline de 6 fases
- **Testes**: Validation e debugging com múltiplos casos de teste
- **Documentação**: README, comentários, regras semânticas

## Notas Importantes

1. **Contexto de Análise**: O analisador semântico usa análise contextual para diferenciar:
   - Definições: `(valor VAR MEM)` — VAR não é "usada", é definida
   - Controles: `(cond corpo IF/WHILE)` — cond deve ser bool
   - Expressões: operações normais seguem regras de tipo

2. **Bloqueio de Assembly**: Se qualquer erro for detectado na fase 5, a fase 6 não executa. Isso garante que apenas código válido é traduzido.

3. **Comentários Completos**: Comentários podem estar em qualquer lugar, inclusive:
   - Linhas inteiras: `*{ comentário }*`
   - Fim de linha: `( 10 X MEM ) *{ define X }*`
   - Entre tokens: `( *{ op }* X *{ var }* + )`

4. **Tipagem Forte**: Uma vez que uma variável recebe um tipo, operações seguintes devem respeitar esse tipo. Redefinições com tipos diferentes geram avisos.

## Referências e Inspiração

- **Cpulator-ARMv7**: Ambiente de execução ARMv7 32-bit
- **LL(1) Parsing**: Técnica clássica de análise sintática
- **Type Inference**: Baseada em cálculo de sequentes (sequent calculus)
- **Semantic Analysis**: Padrões similares a compiladores modernos (Rust, Go)
