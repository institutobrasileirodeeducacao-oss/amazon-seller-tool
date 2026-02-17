-- IBES - PLATAFORMA EDUCACIONAL
-- Script de Configuração do Banco de Dados Supabase

-- 1. CRIAR TABELAS
CREATE TABLE IF NOT EXISTS "Usuários" (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    "e-mail" TEXT UNIQUE NOT NULL,
    hash_da_senha TEXT NOT NULL,
    nome TEXT NOT NULL,
    papel TEXT NOT NULL CHECK (papel IN ('admin', 'professor', 'student')),
    curso TEXT CHECK (curso IN ('mestrado', 'doutorado', NULL)),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS aulas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nome TEXT NOT NULL,
    curso TEXT NOT NULL CHECK (curso IN ('mestrado', 'doutorado')),
    professor_id UUID REFERENCES "Usuários"(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

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

CREATE TABLE IF NOT EXISTS orientacoes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    aluno_id UUID REFERENCES "Usuários"(id) ON DELETE CASCADE,
    professor_id UUID REFERENCES "Usuários"(id) ON DELETE SET NULL,
    mensagens JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. CRIAR ÍNDICES
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON "Usuários"("e-mail");
CREATE INDEX IF NOT EXISTS idx_usuarios_papel ON "Usuários"(papel);
CREATE INDEX IF NOT EXISTS idx_aulas_professor ON aulas(professor_id);
CREATE INDEX IF NOT EXISTS idx_aulas_curso ON aulas(curso);
CREATE INDEX IF NOT EXISTS idx_materiais_aula ON materiais(aula_id);
CREATE INDEX IF NOT EXISTS idx_materiais_tipo ON materiais(tipo);
CREATE INDEX IF NOT EXISTS idx_orientacoes_aluno ON orientacoes(aluno_id);

-- 3. HABILITAR RLS
ALTER TABLE "Usuários" ENABLE ROW LEVEL SECURITY;
ALTER TABLE aulas ENABLE ROW LEVEL SECURITY;
ALTER TABLE materiais ENABLE ROW LEVEL SECURITY;
ALTER TABLE orientacoes ENABLE ROW LEVEL SECURITY;

-- 4. POLÍTICAS DE SEGURANÇA
DROP POLICY IF EXISTS "Permitir leitura pública" ON "Usuários";
DROP POLICY IF EXISTS "Permitir inserção pública" ON "Usuários";
DROP POLICY IF EXISTS "Permitir atualização própria" ON "Usuários";
DROP POLICY IF EXISTS "Permitir deleção própria" ON "Usuários";

CREATE POLICY "Permitir leitura pública" ON "Usuários" FOR SELECT USING (true);
CREATE POLICY "Permitir inserção pública" ON "Usuários" FOR INSERT WITH CHECK (true);
CREATE POLICY "Permitir atualização própria" ON "Usuários" FOR UPDATE USING (true);
CREATE POLICY "Permitir deleção própria" ON "Usuários" FOR DELETE USING (true);

DROP POLICY IF EXISTS "Permitir leitura pública de aulas" ON aulas;
DROP POLICY IF EXISTS "Permitir todas operações em aulas" ON aulas;

CREATE POLICY "Permitir leitura pública de aulas" ON aulas FOR SELECT USING (true);
CREATE POLICY "Permitir todas operações em aulas" ON aulas FOR ALL USING (true);

DROP POLICY IF EXISTS "Permitir leitura pública de materiais" ON materiais;
DROP POLICY IF EXISTS "Permitir todas operações em materiais" ON materiais;

CREATE POLICY "Permitir leitura pública de materiais" ON materiais FOR SELECT USING (true);
CREATE POLICY "Permitir todas operações em materiais" ON materiais FOR ALL USING (true);

DROP POLICY IF EXISTS "Permitir leitura pública de orientações" ON orientacoes;
DROP POLICY IF EXISTS "Permitir todas operações em orientações" ON orientacoes;

CREATE POLICY "Permitir leitura pública de orientações" ON orientacoes FOR SELECT USING (true);
CREATE POLICY "Permitir todas operações em orientações" ON orientacoes FOR ALL USING (true);

-- 5. DADOS INICIAIS
INSERT INTO "Usuários" ("e-mail", hash_da_senha, nome, papel, curso)
VALUES (
    'admin@ibes.edu.br',
    '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9',
    'Administrador IBES',
    'admin',
    NULL
) ON CONFLICT ("e-mail") DO NOTHING;

INSERT INTO "Usuários" ("e-mail", hash_da_senha, nome, papel, curso)
VALUES (
    'prof@ibes.edu.br',
    '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5',
    'Professor Exemplo',
    'professor',
    NULL
) ON CONFLICT ("e-mail") DO NOTHING;

INSERT INTO "Usuários" ("e-mail", hash_da_senha, nome, papel, curso)
VALUES (
    'aluno@ibes.edu.br',
    '53d2e51e7c2bb6f8e7d9d5e8eebe4f54834f5e7f2e14e80fbb9d9e7e9e2e8f1e',
    'Aluno Exemplo',
    'student',
    'mestrado'
) ON CONFLICT ("e-mail") DO NOTHING;

-- 6. TRIGGERS E FUNÇÕES
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_orientacoes_updated_at ON orientacoes;
CREATE TRIGGER update_orientacoes_updated_at 
    BEFORE UPDATE ON orientacoes 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 7. VERIFICAÇÃO
SELECT 'Banco configurado com sucesso!' as mensagem;
