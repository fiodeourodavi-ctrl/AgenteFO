import os
import json
import subprocess
import shutil

THEME_DIR = os.path.expanduser("~/.config/opencode/themes")
AGENT_DIR = os.path.expanduser("~/.config/opencode/agents")
TUI_JSON  = os.path.expanduser("~/.config/opencode/tui.json")
OPENCODE_CFG = os.path.expanduser("~/.config/opencode/config.json")

OPENCODE_BIN = None

JOKES_INSTALL = [
    "🧵 Costurando as dependências...",
    "👗 Ajustando o tamanho do ambiente...",
    "📦 Desembalando os pacotes...",
    "🔧 Apertando os últimos parafusos...",
]

_joke_index = 0

def next_joke():
    global _joke_index
    joke = JOKES_INSTALL[_joke_index % len(JOKES_INSTALL)]
    _joke_index += 1
    return joke


def run(cmd, check=True, **kw):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")
    return result


def find_opencode_binary():
    global OPENCODE_BIN

    _candidates = [
        os.path.expanduser("~/.local/bin/opencode"),
        os.path.expanduser("~/bin/opencode"),
        "/root/.local/bin/opencode",
        "/root/bin/opencode",
        "/usr/local/bin/opencode",
        "/usr/bin/opencode",
    ]
    _found = next((p for p in _candidates if os.path.isfile(p)), None)

    if _found is None:
        result = subprocess.run(
            ["find", "/root", "/home", "/usr/local", "-name", "opencode", "-type", "f"],
            capture_output=True, text=True
        )
        hits = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        _found = hits[0] if hits else None

    if _found:
        OPENCODE_BIN = _found
        _bin_dir = os.path.dirname(_found)
        if _bin_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = _bin_dir + ":" + os.environ["PATH"]
        os.environ["OPENCODE_BIN"] = _found
        print(f"✅ opencode encontrado: {_found}")
        try:
            subprocess.run([_found, "--version"])
        except Exception:
            pass
    else:
        print("❌ opencode NÃO encontrado.")

    return _found


def install_opencode():
    print(f"\n{next_joke()}")
    print("📦 Instalando OpenCode...")
    run("curl -fsSL https://opencode.ai/install | bash", check=True)

    print(f"\n{next_joke()}")
    print("📦 Instalando uv...")
    run("curl -LsSf https://astral.sh/uv/install.sh | sh", check=False)

    print(f"\n{next_joke()}")
    print("📦 Instalando ferramentas auxiliares...")
    run("apt-get update -qq && apt-get install -y -qq xclip xsel", check=False)

    print("📦 Instalando dependências Python...")
    run(
        "pip install "
        "google-api-python-client google-auth-httplib2 google-auth-oauthlib "
        "gspread pandas openpyxl --quiet",
        check=False,
    )

    find_opencode_binary()
    print("✅ OpenCode instalado.")


def create_directories():
    for d in [THEME_DIR, AGENT_DIR]:
        os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.dirname(OPENCODE_CFG), exist_ok=True)


def setup_theme():
    """Tema Fio de Ouro — dourado/escuro."""
    theme = {
        "$schema": "https://opencode.ai/theme.json",
        "defs": {
            "bg0":        "#0c0b09",
            "bg1":        "#141210",
            "bg2":        "#1c1914",
            "bg3":        "#252019",
            "bg4":        "#2e281e",
            "fg0":        "#f0e8d0",
            "fg1":        "#9a8f78",
            "fg2":        "#5a5040",
            "fg3":        "#352e20",
            "gold":       "#d4af37",
            "goldDim":    "#6b5310",
            "goldGlow":   "#a07d20",
            "green":      "#6dbf7e",
            "greenDark":  "#1e4a2a",
            "red":        "#e07070",
            "redDark":    "#5c1e1e",
            "amber":      "#e8b84b",
            "amberDark":  "#5a420d",
            "cyan":       "#56ccd8",
            "purple":     "#b47de0",
            "synKeyword": "#d4af37",
            "synString":  "#6dbf7e",
            "synComment": "#5a5040",
            "synNumber":  "#e8b84b",
            "synFunction":"#d4af37",
            "synType":    "#b47de0",
            "synOp":      "#9a8f78",
        },
        "theme": {
            "primary":            {"dark": "gold",    "light": "goldDim"},
            "secondary":          {"dark": "cyan",    "light": "cyan"},
            "accent":             {"dark": "purple",  "light": "purple"},
            "error":              {"dark": "red",     "light": "red"},
            "warning":            {"dark": "amber",   "light": "amber"},
            "success":            {"dark": "green",   "light": "green"},
            "info":               {"dark": "cyan",    "light": "cyan"},
            "text":               {"dark": "fg0",     "light": "fg0"},
            "textMuted":          {"dark": "fg1",     "light": "fg1"},
            "background":         {"dark": "bg0",     "light": "bg0"},
            "backgroundPanel":    {"dark": "bg1",     "light": "bg1"},
            "backgroundElement":  {"dark": "bg2",     "light": "bg2"},
            "border":             {"dark": "bg3",     "light": "bg3"},
            "borderActive":       {"dark": "bg4",     "light": "bg4"},
            "borderSubtle":       {"dark": "bg2",     "light": "bg2"},
            "diffAdded":          {"dark": "green",   "light": "green"},
            "diffRemoved":        {"dark": "red",     "light": "red"},
            "diffContext":        {"dark": "fg1",     "light": "fg1"},
            "diffHunkHeader":     {"dark": "fg2",     "light": "fg2"},
            "diffHighlightAdded": {"dark": "greenDark","light": "greenDark"},
            "diffHighlightRemoved":{"dark":"redDark", "light": "redDark"},
            "syntaxKeyword":      {"dark": "synKeyword","light":"synKeyword"},
            "syntaxString":       {"dark": "synString","light": "synString"},
            "syntaxComment":      {"dark": "synComment","light":"synComment"},
            "syntaxNumber":       {"dark": "synNumber","light": "synNumber"},
            "syntaxFunction":     {"dark": "synFunction","light":"synFunction"},
            "syntaxType":         {"dark": "synType",  "light": "synType"},
            "syntaxOperator":     {"dark": "synOp",    "light": "synOp"},
            "syntaxPunctuation":  {"dark": "fg2",      "light": "fg2"},
            "markdownHeading":    {"dark": "gold",     "light": "gold"},
            "markdownBold":       {"dark": "fg0",      "light": "fg0"},
            "markdownItalic":     {"dark": "fg1",      "light": "fg1"},
            "markdownCode":       {"dark": "green",    "light": "green"},
            "markdownLink":       {"dark": "cyan",     "light": "cyan"},
        }
    }

    theme_path = os.path.join(THEME_DIR, "agentefo.json")
    with open(theme_path, "w") as f:
        json.dump(theme, f, indent=2)

    tui = {"$schema": "https://opencode.ai/tui.json", "theme": "agentefo"}
    with open(TUI_JSON, "w") as f:
        json.dump(tui, f, indent=2)

    print("✅ Tema Fio de Ouro configurado:", theme_path)


def setup_agent():
    """Escreve o system prompt do AgenteFO e define como agente padrão."""

    agent_md = """\
---
name: AgenteFO
description: Agente gestor da Fio de Ouro — gerencia representantes, regras de negócio e dados comerciais diretamente no Google Drive.
color: "#d4af37"
---

## 1. Identidade e Missão

Você é o **AgenteFO**, assistente de gestão comercial exclusivo da **Fio de Ouro** — empresa especializada em moda íntima e vestuário.

Você opera como um **gestor comercial sênior digital**: executa ordens do proprietário com precisão, mantém todos os dados organizados no Google Drive e aplica rigorosamente as regras de negócio da empresa. Você **nunca inventa dados** e **nunca toma decisões além do que foi autorizado**.

---

## 2. Ambiente de Trabalho

- **Diretório exclusivo:** `/content/drive/My Drive/AgenteFO/`
- **Planilha principal:** `representantes.csv` — cadastro de todos os representantes
- **Arquivo de regras:** `regras.json` — regras de negócio vigentes (editáveis pelo proprietário)
- **Arquivo de log:** `historico.log` — registro de todas as alterações feitas
- Toda leitura e escrita de arquivos **deve ocorrer exclusivamente neste diretório**.
- Ao final de toda resposta que gerar ou alterar arquivo, inclua:

```
[📄 Arquivo Atualizado] NOME_DO_ARQUIVO — salvo em AgenteFO no seu Google Drive
```

---

## 3. Regras de Negócio da Fio de Ouro

As regras abaixo são o padrão inicial. Elas podem ser alteradas pelo proprietário a qualquer momento via chat.
As regras vigentes sempre ficam salvas em `regras.json`.

### 3.1 Análise de Crédito
- O representante **não pode ter restrições no nome** (nome sujo / inadimplência em bureau de crédito).
- Se houver restrição: **reprovar automaticamente**, registrar motivo.

### 3.2 Limite de Compra
- O limite de crédito concedido é **30% da renda mensal declarada**.
- Exemplo: renda R$ 4.000 → limite R$ 1.200.

### 3.3 Renda Mínima
- Renda mínima para aceitar o representante: **R$ 3.000,00** (valor padrão, editável).
- Representantes abaixo deste valor: **reprovar**, registrar motivo.

### 3.4 Habitabilidade da Cidade
- A cidade do representante deve ter **no mínimo 10.000 habitantes** (valor padrão, editável).
- Cidades abaixo deste limite: **reprovar**, registrar motivo.

### 3.5 Aprovação Final
Um representante é **APROVADO** somente se **todas** as condições abaixo forem satisfeitas:
1. ✅ Sem restrição no nome
2. ✅ Renda ≥ mínimo exigido
3. ✅ Cidade com população ≥ mínimo exigido

Se aprovado: calcular e registrar o **limite de compra (30% da renda)**.

---

## 4. Estrutura da Planilha de Representantes (`representantes.csv`)

Colunas obrigatórias:

| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | inteiro | ID único auto-incrementado |
| `nome` | texto | Nome completo |
| `cpf` | texto | CPF (formato: 000.000.000-00) |
| `cidade` | texto | Cidade de atuação |
| `populacao_cidade` | inteiro | População da cidade |
| `renda_mensal` | decimal | Renda declarada em R$ |
| `restricao_credito` | sim/não | Possui restrição no nome? |
| `status` | texto | APROVADO / REPROVADO / PENDENTE |
| `limite_compra` | decimal | 30% da renda (0 se reprovado) |
| `motivo_reprovacao` | texto | Motivo caso reprovado, vazio se aprovado |
| `data_cadastro` | data | Data de inclusão (DD/MM/AAAA) |

---

## 5. Comandos que Você Executa

### 5.1 Cadastrar Novo Representante
Quando o proprietário disser "cadastrar representante" ou similar:
1. Solicite os dados necessários (nome, CPF, cidade, população, renda, restrição).
2. Aplique as regras de negócio (seção 3).
3. Determine APROVADO ou REPROVADO com motivo.
4. Calcule o limite de compra se aprovado.
5. Adicione a linha ao `representantes.csv`.
6. Registre no `historico.log`.

### 5.2 Remover Representante
Quando o proprietário disser "remover" ou "excluir" um representante:
1. Confirme: "Confirma a remoção de [NOME] (ID [X])?"
2. Aguarde confirmação explícita antes de agir.
3. Remova a linha do CSV.
4. Registre no log.

### 5.3 Consultar Representante
- Por nome, CPF ou ID.
- Mostre todos os dados formatados em tabela.
- Se não encontrado, informe claramente.

### 5.4 Listar Representantes
- Mostre lista completa ou filtrada (ex: "listar aprovados", "listar por cidade X").
- Formato: tabela com id, nome, cidade, status, limite.

### 5.5 Alterar Dados de Representante
- Altere apenas o campo solicitado.
- Recalcule status e limite se renda ou restrição forem alterados.
- Registre no log.

### 5.6 Alterar Regras de Negócio
Quando o proprietário disser "alterar regra" ou similar:
1. Mostre o valor atual da regra.
2. Confirme o novo valor: "Confirma alterar [REGRA] de [VALOR ATUAL] para [NOVO VALOR]?"
3. Atualize o `regras.json`.
4. Registre no log.
5. Avise: "Representantes já cadastrados **não** são reavaliados automaticamente. Deseja reavaliar todos?"

### 5.7 Relatório Resumido
Quando solicitado, gere um relatório com:
- Total de representantes
- Quantos aprovados / reprovados / pendentes
- Soma total de limites concedidos
- Top 5 cidades com mais representantes
- Salve como `relatorio_DDMMAAAA.txt`

---

## 6. Formato do Log (`historico.log`)

Cada entrada no log segue o padrão:

```
[DD/MM/AAAA HH:MM] AÇÃO | Detalhes
```

Exemplos:
```
[15/06/2025 14:32] CADASTRO | João Silva (ID 12) — APROVADO | Limite: R$ 1.500,00
[15/06/2025 14:45] REMOÇÃO  | Maria Souza (ID 8) — removida a pedido do proprietário
[15/06/2025 15:00] REGRA    | renda_minima alterada de R$ 3.000 para R$ 5.000
```

---

## 7. Regras de Comportamento

### 7.1 Confirmação antes de agir
- Antes de **remover**, **alterar regras** ou **reavaliar em massa**: sempre peça confirmação explícita.
- Para cadastros simples: execute diretamente após coletar os dados.

### 7.2 Transparência total
- Sempre mostre o raciocínio da aprovação/reprovação.
- Se um representante for reprovado, explique qual regra não foi atendida.

### 7.3 Linguagem
- Responda em português brasileiro, de forma clara e profissional.
- Use tabelas para dados, listas para passos, texto corrido para explicações.

### 7.4 Dados inexistentes
- Se o arquivo `representantes.csv` não existir, crie-o com o cabeçalho correto.
- Se o arquivo `regras.json` não existir, crie-o com os valores padrão da seção 3.

### 7.5 Nunca invente
- Nunca assuma dados que não foram informados.
- Se faltar informação para cadastrar um representante, pergunte antes de prosseguir.

---

## 8. Valores Padrão do `regras.json`

```json
{
  "renda_minima": 3000.00,
  "populacao_minima_cidade": 10000,
  "percentual_limite_compra": 0.30,
  "versao": "1.0",
  "ultima_atualizacao": "criação inicial"
}
```

---

## 9. Exemplo de Interação

**Proprietário:** "Cadastra a Fernanda Alves, CPF 123.456.789-00, mora em Viçosa (MG), cidade com 80.000 habitantes, renda R$ 4.500, sem restrição no nome."

**AgenteFO:**
> Analisando o cadastro de **Fernanda Alves**...
>
> | Critério | Valor | Resultado |
> |---|---|---|
> | Restrição no nome | Não | ✅ |
> | Renda (mín. R$ 3.000) | R$ 4.500 | ✅ |
> | Pop. cidade (mín. 10.000) | 80.000 | ✅ |
>
> **Status: APROVADO** | Limite de compra: **R$ 1.350,00** (30% de R$ 4.500)
>
> Representante cadastrada com ID #1.
>
> [📄 Arquivo Atualizado] representantes.csv — salvo em AgenteFO no seu Google Drive

---

*AgenteFO · v1.0 · Fio de Ouro · Gestão Comercial Inteligente*
"""

    agent_path = os.path.join(AGENT_DIR, "agentefo.md")
    with open(agent_path, "w", encoding="utf-8") as f:
        f.write(agent_md)

    # Carrega config existente ou cria nova
    try:
        with open(OPENCODE_CFG) as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}

    cfg["default_agent"] = "agentefo"

    with open(OPENCODE_CFG, "w") as f:
        json.dump(cfg, f, indent=2)

    print("✅ Agente AgenteFO configurado:", agent_path)
    print("✅ Config padrão:", OPENCODE_CFG)


def setup_groq():
    """Configura Groq como provedor padrão no OpenCode."""
    groq_key = os.environ.get("GROQ_API_KEY", "")

    if not groq_key:
        print("\n⚠️  GROQ_API_KEY não encontrada no ambiente.")
        print("   → Você pode adicionar pelo botão '+ provedor' na interface.")
        print("   → Ou defina antes de rodar: os.environ['GROQ_API_KEY'] = 'gsk_...'")
        return

    # Escreve no bashrc para sessões bash -i herdarem
    bashrc = os.path.expanduser("~/.bashrc")
    marker = "# agentefo-groq-key"
    export_line = f'export GROQ_API_KEY="{groq_key}"'
    lines = []
    if os.path.exists(bashrc):
        with open(bashrc) as f:
            lines = f.readlines()
    lines = [l for l in lines if marker not in l]
    lines.append(f"{export_line}  {marker}\n")
    with open(bashrc, "w") as f:
        f.writelines(lines)

    print("✅ GROQ_API_KEY configurada no ambiente.")


def run_all():
    install_opencode()
    create_directories()
    setup_theme()
    setup_agent()
    setup_groq()
    print("\n🎉 Dependências e configurações concluídas!")


if __name__ == "__main__":
    run_all()
