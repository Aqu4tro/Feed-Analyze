## Feed Analyze

Este projeto é uma aplicação Django com autenticação de usuários e integração completa com o Metabase para geração de dashboards automatizados. Ele permite login seguro, registro de sessões de usuários, visualização de métricas como tempo online e tráfego diário, e automação da criação de dashboards e perguntas com filtros integrados.

---

# 🔧 Tecnologias utilizadas

- **Django** (backend)
- **Metabase** (dashboards)
- **PostgreSQL** (banco de dados)
- **JWT** (para geração de tokens de embed)
- **Docker (opcional)** para execução local do Metabase
- **Python `requests`** (para automatizar chamadas à API do Metabase)

---

# 📁 Estrutura do Projeto

- `accounts/`
  - Views, models e formulários do usuário
  - Sessões de login com início e término
  - Validação de senha reforçada
- `metabase.py`
  - Script de automação:
    - login via API
    - criação de perguntas (cards)
    - criação de dashboards
    - conexão de filtros
    - geração de links públicos
- `settings.py`
  - URLs públicas dos dashboards são atualizadas automaticamente
- `templates/`
  - `login/index.html`, `register/index.html`, `home/index.html`

---

# 🔐 Funcionalidades

## Autenticação

- Cadastro com validação de senha forte (regex)
- Login com limitação de tentativas consecutivas falhas
- Logout automático atualiza `logout_time`

## Sessões de Usuário

- Registro de cada login e logout na tabela `UserSession`
- Cálculo automático de tempo online nos últimos 7 dias

## Dashboards Metabase

- Dashboards criados automaticamente:
  - **Tráfego diário de usuários**
  - **Tempo logado por usuário**
  - **Usuários ativos nos últimos 10 minutos**
- Filtros conectados automaticamente (e.g. `login_date`)
- Links públicos gerados dinamicamente com JWT

---

# ▶️ Como executar

## 1. Clonar o projeto

```bash
git clone https://github.com/Aqu4tro/Feed-Analyze.git
cd Feed-Analyze/django-backend
```

## 2. Configurar variáveis de ambiente

Crie um arquivo `.env` com as credenciais do Metabase e a URL local:

> 🔐 `METABASE_SECRET_KEY` é usada para geração de JWT Embed. Documentação: [Metabase Embledding](https://www.metabase.com/docs/latest/embedding/static-embedding)

```env
METABASE_SECRET_KEY=your_secret_key
METABASE_SITE_URL=http://localhost:3000
EMAIL=example@example.com
PASSWORD=password
```

## 3. Ajustar banco de dados

Certifique-se de que o Django está apontando para um banco PostgreSQL e execute as migrações:

```bash
python manage.py makemigrations
python manage.py migrate
```

## 4. Rodar servidor Django

```bash
python manage.py runserver
```

## 5. Rodar script de automação do Metabase

```bash
python metabase.py
```

> Isso criará dashboards e perguntas com filtros automáticos, conectará os filtros e salvará os links públicos no `settings.py`.

---

# 📊 Dashboards gerados

## Tráfego diário
Consulta usuários registrados no dia.

## Tempo logado por usuário
Exibe o tempo online (em minutos) por sessão, com filtro `login_date`.

## Usuários ativos nos últimos 10 minutos
Mostra contagem de usuários com `last_login >= now() - 10 minutes`.

---

# 🔒 Segurança

- Validação de senha com regex (mínimo de 8 caracteres, maiúscula, minúscula, número e símbolo)
- Tentativas de login consecutivas são monitoradas e bloqueadas temporariamente após 5 falhas
- Filtros protegidos no JWT para visualização segura de dashboards por usuário

---

# ⚙️ Instruções para uso do script `metabase.py`

O script `metabase.py` automatiza a criação de dashboards e perguntas (cards) no Metabase, conectando filtros dinâmicos e exportando os links públicos diretamente para o `settings.py`. No entanto, alguns **ajustes manuais ainda são necessários após a execução**:

---

## ✅ Passos para utilizar corretamente

### 1. Executar o script

```bash
python metabase.py
```

Esse comando irá:

- Fazer login via API no Metabase
- Criar perguntas (questions)
- Criar dashboards
- Conectar filtros automaticamente (quando possível)
- Gerar links públicos com JWT
- Atualizar o arquivo `settings.py` com as URLs dos dashboards

---

## 🛠️ Ajustes manuais obrigatórios no Metabase

### 🔗 1. Conectar manualmente **pergunta (question)** ao **dashboard**

Após o script criar o dashboard e as perguntas, você deve:

1. Acessar o dashboard gerado no Metabase
2. Clicar em **Editar**
3. Clicar na engrenagem (⚙️) da pergunta desejada
4. Selecionar **"Conectar filtro → à variável da pergunta"**

📚 Referência:  
[📘 Metabase – Conectar filtros](https://www.metabase.com/docs/latest/interactive-dashboard-filters/connecting-filters-to-cards)

---

### 🔢 2. Configurar variável como **Number**

Para a pergunta que usa a variável `current_user_id` (ex: **Tempo logado por usuário**):

1. Editar a pergunta no Metabase
2. Ir até o **Editor SQL**
3. Certificar-se de que a variável está visível na query, por exemplo:

   ```sql
   WHERE user_id = CAST({{current_user_id}} AS bigint)
   ```

   ⚠️ Atenção: evite espaços excessivos ou comentários antes da variável, pois o Metabase pode não detectá-la corretamente

4. Na aba lateral de **parâmetros**, defina o tipo da variável `current_user_id` como `Number`

📚 Referência:  
[📘 Metabase – Variáveis em SQL](https://www.metabase.com/docs/latest/users-guide/13-native-parameters.html)

---

### 🧩 3. Conectar filtro no dashboard

1. Acesse o dashboard
2. Clique em **Editar**
3. Adicione um filtro do tipo **Number**
4. Conecte esse filtro à variável `current_user_id` da pergunta

📚 Referência:  
[📘 Metabase – Filtros de Dashboard](https://www.metabase.com/docs/latest/interactive-dashboard-filters/)

---

## 🧪 Teste de filtros dinâmicos

Depois de realizar as conexões:

- Acesse o link público do dashboard
- Use a variável na URL para filtrar dados do usuário:

```bash
https://metabase.example.com/public/dashboard/abc123?current_user_id=42
```

---

Esses passos garantem que os dashboards funcionem corretamente com filtros dinâmicos baseados no usuário logado.