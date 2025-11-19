# 🔑 GUIA COMPLETO - COMO PEGAR CREDENCIAIS

## 1️⃣ SUPABASE (2 credenciais necessárias)

### Passo 1: Acessar Projeto Supabase
1. Abra: **https://app.supabase.com**
2. Faça login
3. Você verá seus projetos (ou opção pra criar novo)

### Passo 2: Entrar no Projeto
- Clique no nome do seu projeto
- OU clique em "**New Project**" se não tiver nenhum (é grátis!)
  - Nome: `prometheus-knowledge`
  - Database Password: escolha uma senha forte (anote!)
  - Region: `South America (São Paulo)` (mais próximo)
  - Plan: **Free** ($0)

### Passo 3: Pegar as Credenciais
1. No menu lateral esquerdo, clique no ícone ⚙️ **Settings** (última opção)
2. Clique em **API**
3. Você verá uma tela com:

```
┌─────────────────────────────────────────────────────────┐
│ Configuration                                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Project URL                                              │
│ https://xxxxxxxxxxx.supabase.co                         │ ← COPIE ISSO
│                                                          │
│ API Keys                                                 │
│                                                          │
│ anon public                                              │
│ eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJz... │ ← COPIE ISSO
│ [Reveal]  [Copy]                                         │
│                                                          │
│ service_role secret                                      │
│ eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJz... │ ← COPIE ISSO TAMBÉM
│ [Reveal]  [Copy]                                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

4. Clique em **[Copy]** ao lado de cada um:
   - **Project URL** → vai para `SUPABASE_URL`
   - **anon public** → vai para `SUPABASE_ANON_KEY` (NOVO!)
   - **service_role** → vai para `SUPABASE_SERVICE_ROLE_KEY`

---

## 2️⃣ OPENAI (1 credencial necessária)

### Passo 1: Acessar OpenAI Platform
1. Abra: **https://platform.openai.com/api-keys**
2. Faça login (ou crie conta se não tiver)

### Passo 2: Criar API Key
1. Você verá uma lista de API keys (pode estar vazia)
2. Clique em **"+ Create new secret key"** (botão verde)
3. Preencha:
   - Name: `Prometheus Knowledge Brain`
   - Permissions: **All** (ou somente "Model capabilities")
4. Clique em **Create secret key**

### Passo 3: Copiar a Key
```
┌─────────────────────────────────────────────────────────┐
│ Save your key                                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Please save this secret key somewhere safe and          │
│ accessible. For security reasons, you won't be able     │
│ to view it again through your OpenAI account.           │
│                                                          │
│ sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx      │ ← COPIE ISSO
│                                                          │
│ [Copy]  [Done]                                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

⚠️ **IMPORTANTE**: Você só vê a key UMA VEZ! Copie e guarde.

---

## 3️⃣ ATUALIZAR O ARQUIVO .ENV

Abra o arquivo: `C:\Users\lucas\Prometheus\.env`

Procure estas linhas e substitua:

### ANTES (linhas 28-30):
```bash
SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_key_here
```

### DEPOIS:
```bash
SUPABASE_URL=https://xxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### ANTES (linha 47):
```bash
OPENAI_API_KEY=your_openai_key_here
```

### DEPOIS:
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 4️⃣ VERIFICAR SE FUNCIONOU

Execute no terminal:

```bash
cd C:\Users\lucas\Prometheus
python check_credentials.py
```

Se tudo estiver OK, você verá:

```
✅ SUPABASE_URL encontrada: https://xxx...co
✅ SUPABASE_ANON_KEY encontrada: eyJhbG...
   ✅ Conexão com Supabase OK!

✅ OPENAI_API_KEY encontrada: sk-proj...
   ✅ Conexão com OpenAI OK!

🎉 TUDO PRONTO! Você pode começar a implementação.
```

---

## 💰 CUSTOS

### Supabase Free Tier
- ✅ 500 MB Database
- ✅ 1 GB File Storage
- ✅ 50,000 usuários ativos/mês
- ✅ **$0/mês**

### OpenAI Embeddings
- **Setup inicial**: ~$1.25 (uma vez só)
- **Uso mensal**: ~$0.06/mês
- **Total**: praticamente grátis

---

## 🆘 PROBLEMAS?

### "Não consigo criar projeto no Supabase"
- Certifique-se de estar logado
- Tente outro navegador (Chrome recomendado)
- Limpe cache e cookies

### "OpenAI pede cartão de crédito"
- Sim, é necessário cadastrar (mas não cobra se ficar no free tier)
- Você ganha $5 de créditos grátis
- Só cobra se ultrapassar os créditos grátis

### "Ainda dá erro ao verificar"
- Execute: `pip install python-dotenv supabase openai`
- Verifique se copiou as keys completas (sem espaços extras)
- Certifique-se que salvou o arquivo .env

---

## ✅ PRÓXIMOS PASSOS

Quando `check_credentials.py` mostrar tudo OK:

1. **Criar schema no Supabase** (vou te dar o SQL pronto)
2. **Executar implementação completa** (5-6 horas)
3. **Testar com arquivos reais**
4. **🎉 Sistema funcionando!**
