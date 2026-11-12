# TRM-Analytics v2

Engine de engenharia de dados e auditoria fiscal *in-memory* desenvolvida para validar e cruzar arquivos fiscais (**XML** vs. **SPED Fiscal/Contribuições** ou **Sintegra**) de forma rápida, isolada e multiusuário.

---

## 📋 Sobre o Projeto

O **TRM-Analytics v2** elimina o gargalo operacional na validação de arquivos fiscais antes do envio às contabilidades. A aplicação recebe um pacote `.zip` contendo os XMLs de venda e os arquivos fiscais (`.txt`), realiza o ETL em memória e aponta exatamente onde há divergências de valores ou documentos.

### Principais Funcionalidades
* **ETL In-Memory:** Extração e padronização automática de lotes de XMLs (`.zip`), SPED (1 ou 2 arquivos `.txt`) e Sintegra (`.txt`).
* **Auditoria Cruzada via SQL:** Comparação analítica de alta velocidade utilizando tabelas temporárias isoladas por sessão (`TEMP TABLES` no DuckDB), permitindo execuções simultâneas na rede.
* **Preview e Exportação:** Visualização prévia das divergências diretamente na interface web com exportação para planilha Excel (`.xlsx`).

---

## 🛠️ Tecnologias Utilizadas

* **Back-end (`backend/`):** Python, FastAPI, DuckDB, Pytest
* **Front-end (`front-end/`):** React, TypeScript, Axios, Vitest
* **Infraestrutura:** Docker, Docker Compose, GitHub Actions (CI/CD)

---

## 📂 Estrutura do Repositório

```text
TRM-Analytics-v2/
├── .github/workflows/   # Pipeline de integração contínua (testes automatizados)
├── backend/             # API monolítica FastAPI, parsers (XML, SPED, Sintegra) e testes
├── front-end/           # Interface web SPA em React + TypeScript
├── docker-compose.yml   # Orquestração dos contêineres da aplicação
└── README.md
```

---

## 🚀 Como Executar

### Pré-requisitos
* [Docker](https://www.docker.com/) e [Docker Compose](https://docs.docker.com/compose/) instalados.

### Subindo a aplicação com Docker
1. Clone o repositório:
   ```bash
   git clone https://github.com/Nicolas-Granato/TRM-Analytics-v2.git
   cd TRM-Analytics-v2
   ```

2. Inicie os contêineres:
   ```bash
   docker-compose up --build -d
   ```

3. Acesse a aplicação no navegador através do endereço configurado para o front-end (ex.: `http://localhost:3000` ou `http://localhost:5173`).

---

## 🧪 Executando os Testes

* **Back-end (Pytest):**
  ```bash
  cd backend
  pytest
  ```

* **Front-end (Vitest):**
  ```bash
  cd front-end
  npm test
  ```

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.