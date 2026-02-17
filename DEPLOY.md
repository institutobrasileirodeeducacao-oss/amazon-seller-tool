# 🚀 Guia Rápido de Publicação - IBES

## ⚡ Publicar no Netlify (Mais Fácil)

### Opção 1: Drag & Drop
1. Acesse: https://app.netlify.com/drop
2. Arraste a pasta `new-project` para a página
3. Aguarde o deploy
4. Pronto! Seu site está no ar

### Opção 2: Via GitHub
1. Crie um repositório no GitHub
2. Faça push dos arquivos
3. Em Netlify: New Site > Import from Git
4. Selecione o repositório
5. Deploy!

### Opção 3: Via CLI
```bash
npm install -g netlify-cli
netlify login
netlify deploy --prod
```

---

## 🗄️ Configurar Banco de Dados Supabase

### Passo 1: Criar Projeto
1. Acesse: https://supabase.com
2. Clique em "New Project"
3. Dê um nome: `ibes-plataforma`
4. Escolha uma senha forte
5. Selecione a região mais próxima

### Passo 2: Executar SQL
1. No painel, vá em **SQL Editor**
2. Clique em "New Query"
3. Copie TODO o conteúdo de `supabase-schema.sql`
4. Cole no editor
5. Clique em **RUN** (botão verde)
6. Aguarde a confirmação

### Passo 3: Obter Credenciais
1. Vá em **Settings** > **API**
2. Copie:
   - **Project URL** (exemplo: https://xxx.supabase.co)
   - **anon/public key** (chave longa começando com eyJ...)

### Passo 4: Atualizar app.js
Abra o arquivo `app.js` e na linha 6-7, substitua:

```javascript
const SUPABASE_URL = 'COLE_SUA_URL_AQUI';
const SUPABASE_ANON_KEY = 'COLE_SUA_KEY_AQUI';
```

---

## ✅ Testar Localmente Antes de Publicar

### Opção 1: Python
```bash
cd new-project
python -m http.server 8000
```
Acesse: http://localhost:8000

### Opção 2: Node.js
```bash
cd new-project
npx http-server
```
Acesse: http://localhost:8080

### Opção 3: VS Code Live Server
1. Abra a pasta no VS Code
2. Clique direito em `index.html`
3. Selecione "Open with Live Server"

---

## 🔐 Login de Teste

Após configurar o banco, use:

- **Admin**:
  - Email: `admin@ibes.edu.br`
  - Senha: `admin123`

- **Professor**:
  - Email: `prof@ibes.edu.br`
  - Senha: `prof123`

- **Aluno**:
  - Email: `aluno@ibes.edu.br`
  - Senha: `aluno123`

---

## 📝 Checklist de Deploy

- [ ] Banco de dados Supabase criado
- [ ] Script SQL executado com sucesso
- [ ] Credenciais copiadas (URL + Key)
- [ ] Arquivo `app.js` atualizado com as credenciais
- [ ] Testado localmente
- [ ] Publicado no Netlify
- [ ] Testado online
- [ ] Login funcionando

---

## 🐛 Problemas Comuns

### Erro: "relation 'Usuários' does not exist"
❌ **Causa**: SQL não foi executado corretamente
✅ **Solução**: Execute novamente o `supabase-schema.sql`

### Erro: "Failed to fetch"
❌ **Causa**: Credenciais incorretas no `app.js`
✅ **Solução**: Verifique URL e Key no Supabase

### Login não funciona
❌ **Causa**: Tabela Usuários vazia
✅ **Solução**: Execute a parte "DADOS INICIAIS" do SQL

### CORS Error
❌ **Causa**: Abrindo arquivo direto (file://)
✅ **Solução**: Use um servidor local (python, http-server, etc)

---

## 🎯 Próximos Passos

1. ✅ **Banco configurado**
2. ✅ **App funcionando**
3. 🔄 **Publicar no Netlify**
4. 📧 **Testar todas as funcionalidades**
5. 🎨 **Personalizar (cores, logo)**
6. 🔐 **Configurar domínio próprio (opcional)**

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique o **console do navegador** (F12)
2. Veja os **logs do Supabase**
3. Revise o README.md completo

---

✨ **Boa sorte com seu projeto IBES!**
