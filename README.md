# 🧵 AgenteFO — Fio de Ouro | Gestão Inteligente de Representantes

O **AgenteFO** é um assistente de gestão comercial executado no Google Colab, criado
para a Fio de Ouro. Gerencie representantes, regras de negócio e dados comerciais
diretamente por chat — tudo salvo no seu Google Drive.

---

## 🛡️ Vantagens

| # | Benefício | Detalhe |
|---|-----------|---------|
| 1 | **100% Gratuito** | Roda na infraestrutura do Google + API Groq gratuita |
| 2 | **Sem Instalação** | Pronto para uso direto no navegador |
| 3 | **Drive Integrado** | Planilha de representantes salva automaticamente |
| 4 | **Regras Flexíveis** | Altere critérios de onboarding via chat |

---

## 🚀 Como Iniciar

1. No menu superior, clique em **Ambiente de execução → Executar tudo** (ou `Ctrl + F9`).
2. Aguarde ~2 minutos enquanto as dependências são instaladas.
3. Clique no botão dourado que irá aparecer e o AgenteFO abrirá em uma nova aba.
4. Na primeira vez, clique em **"+ provedor IA"** e insira sua chave Groq gratuita
   (obtenha em: https://console.groq.com/keys).

---

## ℹ️ Informações Importantes

- **Navegador:** Use preferencialmente o **Google Chrome**.
- **Internet:** Conexão estável é obrigatória.
- **Google Drive:** Os dados ficam em `Meu Drive/AgenteFO/`.
  - `representantes.csv` — cadastro completo
  - `regras.json` — regras de negócio vigentes
  - `historico.log` — log de todas as ações
  - `backups/` — sessões salvas
- **Permissões:** Conceda todas as permissões solicitadas pelo Colab.

---

## 💬 Exemplos de comandos para o chat

```
"Cadastra a Maria Silva, CPF 123.456.789-00, mora em Ubá (MG),
 cidade com 130.000 habitantes, renda R$ 5.000, sem restrição no nome."

"Mostra todos os representantes aprovados."

"Altera a renda mínima para R$ 4.000."

"Gera um relatório resumido."

"Remove o representante de ID 3."
```

---

## Célula de execução (cole no Colab):

```python
import os, sys, subprocess, shutil

REPO_URL = "https://github.com/SEU_USUARIO/AgenteFO.git"
WORK_DIR = "/tmp/agentefo"

print("⏳ Carregando o AgenteFO...")

if os.path.exists(WORK_DIR):
    shutil.rmtree(WORK_DIR)

print("📥 Baixando arquivos...")
subprocess.run(["git", "clone", "--depth", "1", REPO_URL, WORK_DIR], capture_output=True)

os.chdir(WORK_DIR)
sys.path.insert(0, WORK_DIR)

from main import run
run()
```

---

## ⚠️ Limitações e Privacidade

O AgenteFO **não substitui** análise de crédito formal (Serasa/SPC) nem validações
jurídicas. As regras implementadas são baseadas nos critérios internos da Fio de Ouro.

> **Privacidade:** Os dados dos representantes ficam exclusivamente no seu Google Drive.
> Não insira dados sensíveis além dos necessários para o onboarding.

---

## Citação / Créditos

Baseado na arquitetura do **PesquisAI** (Gustavo Bastos Braga, UFV, 2026).
Adaptado para gestão comercial da Fio de Ouro.

---

*AgenteFO · v1.0 · Fio de Ouro · Gestão Comercial Inteligente*
