# IBES - Plataforma Educacional

Sistema de gestão educacional para cursos de Mestrado e Doutorado.

## 📋 Estrutura do Banco de Dados Supabase

Execute os seguintes comandos SQL no seu Supabase:

### 1. Tabela de Usuários

```sql
CREATE TABLE "Usuários" (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    "e-mail" TEXT UNIQUE NOT NULL,
    hash_da_senha TEXT NOT NULL,
    nome TEXT NOT NULL,
    papel TEXT NOT NULL CHECK (papel IN ('admin', 'professor', 'student')),
    curso TEXT CHECK (curso IN ('mestrado', 'doutorado', NULL)),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2. Tabela de Aulas/Turmas

```sql
CREATE TABLE aulas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nome TEXT NOT NULL,
    curso TEXT NOT NULL CHECK (curso IN ('mestrado', 'doutorado')),
    professor_id UUID REFERENCES "Usuários"(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3. Tabela de Materiais

```sql
CREATE TABLE materiais (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    aula_id UUID REFERENCES aulas(id) ON DELETE CASCADE,
    professor_id UUID REFERENCES "Usuários"(id) ON DELETE SET NULL,
    titulo TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('video', 'document', 'student_submission')),
    arquivo TEXT NOT NULL,
    descricao TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 4. Tabela de Orientações

```sql
CREATE TABLE orientacoes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    aluno_id UUID REFERENCES "Usuários"(id) ON DELETE CASCADE,
    professor_id UUID REFERENCES "Usuários"(id) ON DELETE SET NULL,
    mensagens JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 5. Políticas RLS (Row Level Security)

```sql
-- Habilitar RLS nas tabelas
ALTER TABLE "Usuários" ENABLE ROW LEVEL SECURITY;
ALTER TABLE aulas ENABLE ROW LEVEL SECURITY;
ALTER TABLE materiais ENABLE ROW LEVEL SECURITY;
ALTER TABLE orientacoes ENABLE ROW LEVEL SECURITY;

-- Políticas públicas para leitura (ajuste conforme necessário)
CREATE POLICY "Permitir leitura pública" ON "Usuários" FOR SELECT USING (true);
CREATE POLICY "Permitir inserção pública" ON "Usuários" FOR INSERT WITH CHECK (true);
CREATE POLICY "Permitir atualização própria" ON "Usuários" FOR UPDATE USING (true);
CREATE POLICY "Permitir deleção própria" ON "Usuários" FOR DELETE USING (true);

CREATE POLICY "Permitir leitura pública de aulas" ON aulas FOR SELECT USING (true);
CREATE POLICY "Permitir todas operações em aulas" ON aulas FOR ALL USING (true);

CREATE POLICY "Permitir leitura pública de materiais" ON materiais FOR SELECT USING (true);
CREATE POLICY "Permitir todas operações em materiais" ON materiais FOR ALL USING (true);

CREATE POLICY "Permitir leitura pública de orientações" ON orientacoes FOR SELECT USING (true);
CREATE POLICY "Permitir todas operações em orientações" ON orientacoes FOR ALL USING (true);
```

### 6. Criar usuário administrador inicial

```sql
-- Senha: admin123 (hash SHA-256)
INSERT INTO "Usuários" ("e-mail", hash_da_senha, nome, papel, curso)
VALUES (
    'admin@ibes.edu.br',
    '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9',
    'Administrador',
    'admin',
    NULL
);
```

## 🚀 Como Usar

### 1. Configurar Supabase

1. Acesse [supabase.com](https://supabase.com) e crie/acesse seu projeto
2. No SQL Editor, execute todos os comandos SQL acima
3. Copie a **URL do projeto** e a **anon key** em Project Settings > API

### 2. Atualizar Credenciais

Edite o arquivo `app.js` e atualize:

```javascript
const SUPABASE_URL = 'SUA_URL_AQUI';
const SUPABASE_ANON_KEY = 'SUA_KEY_AQUI';
```

### 3. Testar Localmente

Abra `index.html` diretamente no navegador ou use um servidor local:

```bash
# Python 3
python -m http.server 8000

# Node.js (http-server)
npx http-server

# VS Code - Live Server
# Clique com botão direito em index.html > Open with Live Server
```

### 4. Publicar no Netlify

1. Crie uma conta em [netlify.com](https://netlify.com)
2. Arraste a pasta do projeto para o Netlify Drop
3. Ou conecte ao GitHub e faça deploy automático

**Alternativamente via CLI:**

```bash
npm install -g netlify-cli
netlify deploy --prod
```

## 👤 Login de Teste

- **Email**: admin@ibes.edu.br
- **Senha**: admin123

## 📦 Estrutura de Arquivos

```
ibes-plataforma/
├── index.html          # Interface principal
├── app.js             # Lógica da aplicação
└── README.md          # Este arquivo
```

## 🔐 Segurança

⚠️ **IMPORTANTE**: As senhas são armazenadas usando SHA-256. Para produção, considere:

1. Usar bcrypt ou Argon2 no backend
2. Implementar autenticação via Supabase Auth
3. Configurar políticas RLS mais restritivas
4. Adicionar HTTPS obrigatório
5. Implementar rate limiting

## 📝 Funcionalidades

### Administrador
- Cadastrar professores
- Cadastrar alunos
- Criar turmas
- Visualizar todos os registros

### Professor
- Ver turmas atribuídas
- Enviar vídeo-aulas
- Enviar materiais
- Ver alunos matriculados
- Gerenciar orientações

### Aluno
- Acessar materiais do curso
- Assistir vídeo-aulas
- Enviar trabalhos para professores
- Chat com orientador
- Área de orientação

## 🐛 Solução de Problemas

### Erro ao fazer login
- Verifique se o banco de dados foi criado corretamente
- Confirme as credenciais do Supabase em `app.js`
- Veja o console do navegador (F12) para erros específicos

### Tabelas não encontradas
- Execute todos os comandos SQL na ordem correta
- Verifique os nomes das tabelas (com acentos e case-sensitive)

### CORS Error
- Use um servidor local, não abra direto do sistema de arquivos
- Configure CORS no Supabase se necessário

## 📞 Suporte

Para problemas ou dúvidas, verifique:
1. Console do navegador (F12)
2. Logs no Supabase Dashboard
3. Documentação oficial do Supabase

## 📄 Licença

Este projeto é fornecido como está para fins educacionais.
