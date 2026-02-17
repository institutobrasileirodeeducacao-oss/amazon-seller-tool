-- ================================================
-- IBES - PLATAFORMA EDUCACIONAL
-- Script de Configuração do Banco de Dados Supabase
-- ================================================

-- 1. CRIAR TABELAS
-- ================================================

-- Tabela de Usuários
CREATE TABLE IF NOT EXISTS "Usuários" (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    "e-mail" TEXT UNIQUE NOT NULL,
    hash_da_senha TEXT NOT NULL,
    nome TEXT NOT NULL,
    papel TEXT NOT NULL CHECK (papel IN ('admin', 'professor', 'student')),
    curso TEXT CHECK (curso IN ('mestrado', 'doutorado', NULL)),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de Aulas/Turmas
CREATE TABLE IF NOT EXISTS aulas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nome TEXT NOT NULL,
    curso TEXT NOT NULL CHECK (curso IN ('mestrado', 'doutorado')),
    professor_id UUID REFERENCES "Usuários"(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de Materiais
CREATE TABLE IF NOT EXISTS materiais (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    aula_id UUID REFERENCES aulas(id) ON DELETE CASCADE,
    professor_id UUID REFERENCES "Usuários"(id) ON DELETE SET NULL,
    titulo TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('video', 'document', 'student_submission')),
    arquivo TEXT NOT NULL,
    descricao TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de Orientações
CREATE TABLE IF NOT EXISTS orientacoes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    aluno_id UUID REFERENCES "Usuários"(id) ON DELETE CASCADE,
    professor_id UUID REFERENCES "Usuários"(id) ON DELETE SET NULL,
    mensagens JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. CRIAR ÍNDICES
-- ================================================

CREATE INDEX IF NOT EXISTS idx_usuarios_email ON "Usuários"("e-mail");
CREATE INDEX IF NOT EXISTS idx_usuarios_papel ON "Usuários"(papel);
CREATE INDEX IF NOT EXISTS idx_aulas_professor ON aulas(professor_id);
CREATE INDEX IF NOT EXISTS idx_aulas_curso ON aulas(curso);
CREATE INDEX IF NOT EXISTS idx_materiais_aula ON materiais(aula_id);
CREATE INDEX IF NOT EXISTS idx_materiais_tipo ON materiais(tipo);
CREATE INDEX IF NOT EXISTS idx_orientacoes_aluno ON orientacoes(aluno_id);

-- 3. HABILITAR RLS (Row Level Security)
-- ================================================

ALTER TABLE "Usuários" ENABLE ROW LEVEL SECURITY;
ALTER TABLE aulas ENABLE ROW LEVEL SECURITY;
ALTER TABLE materiais ENABLE ROW LEVEL SECURITY;
ALTER TABLE orientacoes ENABLE ROW LEVEL SECURITY;

-- 4. POLÍTICAS DE SEGURANÇA
-- ================================================

-- Políticas para Usuários
DROP POLICY IF EXISTS "Permitir leitura pública" ON "Usuários";
DROP POLICY IF EXISTS "Permitir inserção pública" ON "Usuários";
DROP POLICY IF EXISTS "Permitir atualização própria" ON "Usuários";
DROP POLICY IF EXISTS "Permitir deleção própria" ON "Usuários";

CREATE POLICY "Permitir leitura pública" ON "Usuários" 
    FOR SELECT USING (true);

CREATE POLICY "Permitir inserção pública" ON "Usuários" 
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Permitir atualização própria" ON "Usuários" 
    FOR UPDATE USING (true);

CREATE POLICY "Permitir deleção própria" ON "Usuários" 
    FOR DELETE USING (true);

-- Políticas para Aulas
DROP POLICY IF EXISTS "Permitir leitura pública de aulas" ON aulas;
DROP POLICY IF EXISTS "Permitir todas operações em aulas" ON aulas;

CREATE POLICY "Permitir leitura pública de aulas" ON aulas 
    FOR SELECT USING (true);

CREATE POLICY "Permitir todas operações em aulas" ON aulas 
    FOR ALL USING (true);

-- Políticas para Materiais
DROP POLICY IF EXISTS "Permitir leitura pública de materiais" ON materiais;
DROP POLICY IF EXISTS "Permitir todas operações em materiais" ON materiais;

CREATE POLICY "Permitir leitura pública de materiais" ON materiais 
    FOR SELECT USING (true);

CREATE POLICY "Permitir todas operações em materiais" ON materiais 
    FOR ALL USING (true);

-- Políticas para Orientações
DROP POLICY IF EXISTS "Permitir leitura pública de orientações" ON orientacoes;
DROP POLICY IF EXISTS "Permitir todas operações em orientações" ON orientacoes;

CREATE POLICY "Permitir leitura pública de orientações" ON orientacoes 
    FOR SELECT USING (true);

CREATE POLICY "Permitir todas operações em orientações" ON orientacoes 
    FOR ALL USING (true);

-- 5. DADOS INICIAIS
-- ================================================

-- Inserir usuário administrador
-- Email: admin@ibes.edu.br
-- Senha: admin123 (hash SHA-256)
INSERT INTO "Usuários" ("e-mail", hash_da_senha, nome, papel, curso)
VALUES (
    'admin@ibes.edu.br',
    '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9',
    'Administrador IBES',
    'admin',
    NULL
)
ON CONFLICT ("e-mail") DO NOTHING;

-- Inserir professor exemplo
-- Email: prof@ibes.edu.br
-- Senha: prof123 (hash SHA-256)
INSERT INTO "Usuários" ("e-mail", hash_da_senha, nome, papel, curso)
VALUES (
    'prof@ibes.edu.br',
    '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
    'Professor Exemplo',
    'professor',
    NULL
)
ON CONFLICT ("e-mail") DO NOTHING;

-- Inserir aluno exemplo
-- Email: aluno@ibes.edu.br
-- Senha: aluno123 (hash SHA-256)
INSERT INTO "Usuários" ("e-mail", hash_da_senha, nome, papel, curso)
VALUES (
    'aluno@ibes.edu.br',
    '53d2e51e7c2bb6f8e7d9d5e8eebe4f54834f5e7f2e14e80fbb9d9e7e9e2e8f1e',
    'Aluno Exemplo',
    'student',
    'mestrado'
)
ON CONFLICT ("e-mail") DO NOTHING;

-- 6. TRIGGERS E FUNÇÕES
-- ================================================

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para orientações
DROP TRIGGER IF EXISTS update_orientacoes_updated_at ON orientacoes;
CREATE TRIGGER update_orientacoes_updated_at 
    BEFORE UPDATE ON orientacoes 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 7. VIEWS ÚTEIS (OPCIONAL)
-- ================================================

-- View de estatísticas gerais
CREATE OR REPLACE VIEW estatisticas_gerais AS
SELECT 
    (SELECT COUNT(*) FROM "Usuários" WHERE papel = 'professor') as total_professores,
    (SELECT COUNT(*) FROM "Usuários" WHERE papel = 'student') as total_alunos,
    (SELECT COUNT(*) FROM aulas) as total_turmas,
    (SELECT COUNT(*) FROM materiais WHERE tipo = 'video') as total_videos,
    (SELECT COUNT(*) FROM materiais WHERE tipo = 'document') as total_documentos;

-- View de turmas com informações do professor
CREATE OR REPLACE VIEW aulas_detalhadas AS
SELECT 
    a.id,
    a.nome as turma,
    a.curso,
    a.created_at as criada_em,
    u.nome as professor_nome,
    u."e-mail" as professor_email
FROM aulas a
LEFT JOIN "Usuários" u ON a.professor_id = u.id;

-- ================================================
-- FIM DO SCRIPT
-- ================================================

-- Para verificar se tudo foi criado corretamente:
SELECT 'Tabelas criadas:' as status;
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('Usuários', 'aulas', 'materiais', 'orientacoes');

SELECT 'Usuários iniciais:' as status;
SELECT nome, "e-mail", papel FROM "Usuários";
