# Dashboard de Praticagem Rio (Serverless) 🚢

Este projeto é um painel de monitoramento das manobras de navios no porto do Rio de Janeiro. Ele foi desenvolvido com uma arquitetura **100% gratuita e automatizada** (Serverless), utilizando GitHub Actions para coletar dados e GitHub Pages para hospedagem.

**Desenvolvido por:**
- **Dalmo dos Santos Cabral**
- **Agent da Antigravity**

---

## 🏗️ Arquitetura do Projeto

O sistema funciona em um ciclo automatizado de 3 etapas:

1.  **Coleta (Scraper):** Um script Python (`scraper/scraper.py`) roda a cada **5 minutos** nos servidores do GitHub. Ele acessa o site da Praticagem RJ, extrai as informações e verifica conflitos.
2.  **Armazenamento:** O script salva os dados tratados em um arquivo JSON (`public/data.json`) e faz um *commit* automático no repositório.
3.  **Deploy:** Assim que o JSON é atualizado, o GitHub Actions constrói o site React e publica a nova versão no GitHub Pages.

**Fluxo:** `Site Praticagem` -> `Python` -> `data.json` -> `React` -> `Seu Celular`

---

## 🚀 Tecnologias

-   **Frontend:** React (Vite), CSS Puro (Moderno/Responsivo), Lucide React (Ícones).
-   **Backend/Bot:** Python 3.9, BeautifulSoup4 (Web Scraping).
-   **Automação:** GitHub Actions (YAML).
-   **Hospedagem:** GitHub Pages.

---

## 📂 Estrutura de Pastas

```bash
praticagem_dashboard/
├── .github/workflows/
│   └── scrape.yml       # O "Coração" do projeto. Controla o robô e o deploy.
├── public/
│   └── data.json        # Arquivo de dados gerado automaticamente (NÃO EDITE MANUALMENTE).
├── scraper/
│   ├── scraper.py       # Código Python que baixa e trata os dados.
│   └── requirements.txt # Bibliotecas Python necessárias.
├── src/
│   ├── App.jsx          # Lógica principal do React (Tabelas, Filtros, Cache Busting).
│   └── index.css        # Estilos (incluindo o layout mobile customizado).
└── package.json         # Dependências do Node.js.
```

---

## 🛠️ Como Executar Localmente (No seu PC)

Se precisar mexer no código ou testar mudanças antes de subir:

### 1. Pré-requisitos
-   Node.js instalado.
-   Python instalado.

### 2. Rodar o Site (Frontend)
```bash
npm install       # Instala dependências
npm run dev       # Inicia o servidor local (localhost:5173)
```

### 3. Rodar o Robô (Opcional)
Se quiser testar a captura de dados no seu PC:
```bash
pip install -r scraper/requirements.txt
python scraper/scraper.py
```
Isso vai atualizar o arquivo `public/data.json` localmente com dados reais do momento.

---

## ⚙️ Manutenção e Configurações

### Alterar Intervalo de Atualização
O robô roda a cada 5 minutos. Para mudar, edite `.github/workflows/scrape.yml`:
```yaml
schedule:
  - cron: '*/5 * * * *'  # Mude o 5 para os minutos desejados
```

### Adicionar/Remover Berços
A filtragem de berços ("TECONT", "MANGUINHOS", etc.) fica no arquivo `scraper/scraper.py` na variável:
```python
BERCOS_INCLUIR_TODOS = { ... }
```

### Resolver "Dados Desatualizados" (Cache)
Se o site parecer "preso" no passado, o código já possui uma proteção no `App.jsx`:
```javascript
fetch(`./data.json?t=${new Date().getTime()}`)
```
Isso força o navegador a baixar a versão mais recente sempre.

---

## ⚠️ Solução de Problemas Comuns

| Problema | Causa Provável | Solução |
| :--- | :--- | :--- |
| **Site não atualiza** | Robô falhou ou GitHub Actions suspenso | Vá na aba "Actions" no GitHub e veja se tem erro vermelho. Se estiver suspenso, clique em "Enable Workflow". |
| **Horário errado** | Fuso horário do servidor | O script já converte para `America/Sao_Paulo`. Verifique se o PC local está com a hora certa. |
| **Tabela quebra no celular** | CSS Mobile | O layout mobile fica no final do `index.css`. Verifique as regras `@media (max-width: 768px)`. |

---

> _Documentação gerada automaticamente em 01/02/2026._
