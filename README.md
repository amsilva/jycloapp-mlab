# Redboard

REDBoard é um webapp PWA desenvolvido em Python para gerenciamento pessoal e individual de doações para voluntários de bancos de sangue.

---

## Visão do Projeto

O objetivo do REDBoard é:

- Permitir registro simples de doações
- Exibir histórico organizado
- Funcionar como dashboard pessoal com contadores
- Evoluir para uma rede social/gamificada de incentivo à doação

---

## Arquitetura Inicial

- **Backend:** FastAPI  
- **Banco de Dados:** SQLite (arquivo local)  
- **Frontend:** HTML + CSS + JavaScript  
- Estrutura preparada para PWA  
- Deploy futuro previsto para:
  - Render
  - Fly.io
  - PythonAnywhere  

---

# Versão 0.1 – MVP Inicial

## Objetivo

Implementar a funcionalidade principal:

> Registro e listagem de doações.

---

## Funcionalidades

- Listagem de doações cadastradas
- Botão "+" para adicionar nova doação
- Cadastro contendo:
  - Tipo (sangue, plaqueta ou plasma)
  - Data (editável)
  - Local (campo texto aberto)

Características da versão:

- Sem autenticação
- Uso individual
- Banco local
- Foco total na funcionalidade principal

---

## Banco de Dados

Banco relacional leve baseado em arquivo.

**Escolhido:** SQLite  

Arquivo gerado:


### Entidade Inicial

#### DOACOES

- id
- tipo
- data
- local
- criado_em

---

## Frontend

- Interface minimalista
- Cards organizados por data
- Botão circular para adicionar doação
- Modal para cadastro
- CSS reaproveitado de projeto anterior

Possível evolução futura:
- TailwindCSS (opcional)

---

# Estrutura Técnica

## Backend

- FastAPI
- SQLAlchemy
- Jinja2

## Banco

- SQLite (arquivo local)

---

## Preparação para o Futuro

- Separação clara entre `models`, `schemas` e `rotas`
- Estrutura preparada para migração de banco
- Base pronta para transformação completa em PWA
- Arquitetura escalável para futuras versões

---

## Status Atual

Em desenvolvimento – Versão 0.1 (MVP).

---

