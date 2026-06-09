import os
import shutil
import subprocess

SKILLS_DIR = os.path.expanduser("~/.agents/skills")

# Skills específicas do AgenteFO
# Por enquanto usa skills locais (criadas neste arquivo).
# Quando você publicar no GitHub, substitua pelas URLs dos repos.
REMOTE_SKILLS = [
    # ("https://github.com/SEU_USUARIO/skill-fio-de-ouro.git", "fio-de-ouro"),
]

JOKES = [
    "📋 Instalando o manual de regras comerciais...",
    "🧾 Configurando o sistema de cadastro...",
    "📊 Preparando os modelos de planilha...",
]

_joke_index = 0

def next_joke():
    global _joke_index
    joke = JOKES[_joke_index % len(JOKES)]
    _joke_index += 1
    return joke


def create_local_skills():
    """Cria as skills locais do AgenteFO diretamente no disco."""

    os.makedirs(SKILLS_DIR, exist_ok=True)

    # ── Skill: regras-negocio ─────────────────────────────────────────────────
    skill_regras_dir = os.path.join(SKILLS_DIR, "regras-negocio")
    os.makedirs(skill_regras_dir, exist_ok=True)

    with open(os.path.join(skill_regras_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("""\
# Skill: Regras de Negócio — Fio de Ouro

## Propósito
Fornecer ao agente as regras de onboarding de representantes da Fio de Ouro,
lendo sempre o arquivo `regras.json` em `/content/drive/My Drive/AgenteFO/`.

## Como Usar
1. Leia `regras.json` para obter os valores vigentes.
2. Aplique cada critério na ordem: restrição → renda → cidade → limite.
3. Registre o resultado no `representantes.csv` e no `historico.log`.

## Critérios (valores padrão — podem mudar via regras.json)
- `restricao_credito`: bloqueia imediatamente se "sim"
- `renda_minima`: padrão R$ 3.000,00
- `populacao_minima_cidade`: padrão 10.000 habitantes
- `percentual_limite_compra`: padrão 30% (0.30)

## Fórmula do Limite
```
limite_compra = renda_mensal * percentual_limite_compra
```
""")
    print("✅ Skill regras-negocio criada.")

    # ── Skill: gestao-csv ─────────────────────────────────────────────────────
    skill_csv_dir = os.path.join(SKILLS_DIR, "gestao-csv")
    os.makedirs(skill_csv_dir, exist_ok=True)

    with open(os.path.join(skill_csv_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("""\
# Skill: Gestão de CSV — Representantes

## Propósito
Ler, criar, atualizar e remover linhas do arquivo `representantes.csv`
em `/content/drive/My Drive/AgenteFO/`.

## Operações Disponíveis

### Criar arquivo (se não existir)
```python
import csv, os
path = "/content/drive/My Drive/AgenteFO/representantes.csv"
if not os.path.exists(path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id","nome","cpf","cidade","populacao_cidade",
                    "renda_mensal","restricao_credito","status",
                    "limite_compra","motivo_reprovacao","data_cadastro"])
```

### Adicionar representante
```python
import csv
from datetime import datetime
path = "/content/drive/My Drive/AgenteFO/representantes.csv"
with open(path, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow([id, nome, cpf, cidade, pop, renda, restricao,
                status, limite, motivo, datetime.now().strftime("%d/%m/%Y")])
```

### Ler todos
```python
import csv
with open(path, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
```

### Remover por ID
```python
rows = [r for r in rows if r["id"] != str(target_id)]
# reescrever o arquivo com os rows filtrados
```

## Regras de ID
- Sempre use o maior ID existente + 1.
- Se o arquivo estiver vazio, comece pelo ID 1.
""")
    print("✅ Skill gestao-csv criada.")

    # ── Skill: log ────────────────────────────────────────────────────────────
    skill_log_dir = os.path.join(SKILLS_DIR, "historico-log")
    os.makedirs(skill_log_dir, exist_ok=True)

    with open(os.path.join(skill_log_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("""\
# Skill: Histórico de Log

## Propósito
Registrar todas as ações executadas pelo AgenteFO em `historico.log`
em `/content/drive/My Drive/AgenteFO/`.

## Formato de Entrada
```
[DD/MM/AAAA HH:MM] AÇÃO | Detalhes
```

## Tipos de Ação
- `CADASTRO`  — novo representante adicionado
- `REMOÇÃO`   — representante removido
- `ALTERAÇÃO` — dado de representante alterado
- `REGRA`     — regra de negócio alterada
- `CONSULTA`  — consulta realizada (opcional registrar)
- `RELATÓRIO` — relatório gerado

## Código Python
```python
from datetime import datetime
log_path = "/content/drive/My Drive/AgenteFO/historico.log"
def registrar(acao, detalhes):
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {acao} | {detalhes}\\n")
```
""")
    print("✅ Skill historico-log criada.")

    # ── Skill: relatorio ──────────────────────────────────────────────────────
    skill_rel_dir = os.path.join(SKILLS_DIR, "relatorio-fo")
    os.makedirs(skill_rel_dir, exist_ok=True)

    with open(os.path.join(skill_rel_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("""\
# Skill: Relatório Comercial — Fio de Ouro

## Propósito
Gerar relatório resumido dos representantes em
`/content/drive/My Drive/AgenteFO/relatorio_DDMMAAAA.txt`.

## Conteúdo do Relatório
1. Data e hora de geração
2. Total de representantes cadastrados
3. Breakdown: Aprovados / Reprovados / Pendentes
4. Soma total de limites concedidos (R$)
5. Média de limite por representante aprovado
6. Top 5 cidades com mais representantes
7. Lista dos últimos 10 cadastros

## Template
```
========================================
RELATÓRIO COMERCIAL — FIO DE OURO
Gerado em: DD/MM/AAAA HH:MM
========================================

RESUMO
------
Total de representantes : XX
  Aprovados             : XX
  Reprovados            : XX
  Pendentes             : XX

Crédito Total Concedido : R$ X.XXX,XX
Média por Aprovado      : R$ X.XXX,XX

TOP 5 CIDADES
-------------
1. Cidade A — X representantes
...

ÚLTIMOS CADASTROS
-----------------
...
========================================
```
""")
    print("✅ Skill relatorio-fo criada.")


def install_skills():
    print(f"\n{next_joke()}")
    print("🔧 Instalando skills do AgenteFO...")

    create_local_skills()

    # Se houver skills remotas no GitHub, clonar aqui
    for repo_url, name in REMOTE_SKILLS:
        tmp = f"/tmp/skill_{name}"
        if os.path.exists(tmp):
            shutil.rmtree(tmp)
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, tmp],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            dest = os.path.join(SKILLS_DIR, name)
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(tmp, dest, dirs_exist_ok=True)
            print(f"✅ {name} instalada do GitHub.")
        else:
            print(f"❌ Falha ao clonar {repo_url}")

    print(f"\n{next_joke()}")
    print("\n🎉 Todas as skills do AgenteFO instaladas!")


if __name__ == "__main__":
    install_skills()
