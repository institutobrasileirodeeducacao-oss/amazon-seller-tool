// =========================
// SUPABASE CONFIGURATION
// =========================

const SUPABASE_URL = 'https://swxtpahohrwwnooxuqbh.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN3eHRwYWhvaHJ3d25vb3h1cWJoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAyMzU5MjQsImV4cCI6MjA4NTgxMTkyNH0.zlKtCQp71UangGLG8aX7cX8b5NTYTE5W8lZHotg_GxM';

let supabase = null;

function initSupabase() {
    if (typeof window.supabase === 'undefined') {
        console.error('[IBES] Supabase library não carregada!');
        alert('Erro ao carregar Supabase. Verifique sua conexão com a internet.');
        return false;
    }
    console.log('[IBES] Inicializando conexão com Supabase...');
    supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    console.log('[IBES] Cliente Supabase criado com sucesso');
    return true;
}

let currentUser = null;
let currentClass = null;

// =========================
// HELPER FUNCTIONS
// =========================

async function hashPassword(password) {
    console.log('[HASH] Gerando hash para senha...');
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hash = await crypto.subtle.digest('SHA-256', data);
    const hashHex = Array.from(new Uint8Array(hash))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
    console.log('[HASH] Hash gerado:', hashHex);
    return hashHex;
}

function showError(elementId, message) {
    console.error('[ERRO]', message);
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = message;
        el.classList.remove('hidden');
        setTimeout(() => el.classList.add('hidden'), 5000);
    }
}

function showSuccess(elementId, message) {
    console.log('[SUCESSO]', message);
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = message;
        el.classList.remove('hidden');
        setTimeout(() => el.classList.add('hidden'), 3000);
    }
}

function showModal(modalId) {
    document.getElementById(modalId).classList.add('show');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}

function updateFileName(elementId, input) {
    const el = document.getElementById(elementId);
    if (input.files && input.files[0]) {
        el.textContent = input.files[0].name;
    }
}

// =========================
// AUTHENTICATION
// =========================

document.getElementById('regType').addEventListener('change', function() {
    document.getElementById('courseGroup').style.display = 
        this.value === 'student' ? 'block' : 'none';
});

document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    console.log('[LOGIN] Iniciando processo de login...');
    
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    console.log('[LOGIN] Email:', email);
    
    try {
        const passwordHash = await hashPassword(password);
        console.log('[LOGIN] Buscando usuário no banco de dados...');
        
        const { data, error } = await supabase
            .from('Usuários')
            .select('*')
            .eq('e-mail', email)
            .eq('hash_da_senha', passwordHash)
            .maybeSingle();
        
        console.log('[LOGIN] Resposta do banco:', { data, error });
        
        if (error) {
            console.error('[LOGIN] Erro na query:', error);
            showError('loginError', 'Erro ao conectar com o banco de dados.');
            return;
        }
        
        if (!data) {
            console.warn('[LOGIN] Usuário não encontrado ou senha incorreta');
            showError('loginError', 'Email ou senha incorretos!');
            return;
        }
        
        console.log('[LOGIN] Login bem-sucedido! Usuário:', data.nome);
        currentUser = data;
        showApp();
    } catch (err) {
        console.error('[LOGIN] Erro inesperado:', err);
        showError('loginError', 'Erro ao fazer login. Tente novamente.');
    }
});

document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    console.log('[CADASTRO] Iniciando cadastro de novo usuário...');
    
    const name = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value;
    const role = document.getElementById('regType').value;
    const course = role === 'student' ? document.getElementById('regCourse').value : null;
    
    console.log('[CADASTRO] Dados:', { name, email, role, course });
    
    try {
        console.log('[CADASTRO] Verificando se email já existe...');
        const { data: existingUser, error: checkError } = await supabase
            .from('Usuários')
            .select('e-mail')
            .eq('e-mail', email)
            .maybeSingle();
        
        console.log('[CADASTRO] Verificação:', { existingUser, checkError });
        
        if (existingUser) {
            console.warn('[CADASTRO] Email já cadastrado');
            showError('registerError', 'Este email já está cadastrado!');
            return;
        }
        
        const passwordHash = await hashPassword(password);
        console.log('[CADASTRO] Inserindo novo usuário no banco...');
        
        const { data: newUser, error: insertError } = await supabase
            .from('Usuários')
            .insert([{
                'e-mail': email,
                hash_da_senha: passwordHash,
                nome: name,
                papel: role,
                curso: course
            }])
            .select()
            .single();
        
        console.log('[CADASTRO] Resultado da inserção:', { newUser, insertError });
        
        if (insertError) {
            console.error('[CADASTRO] Erro ao inserir:', insertError);
            throw insertError;
        }
        
        console.log('[CADASTRO] Usuário cadastrado com sucesso!');
        showSuccess('registerSuccess', 'Cadastro realizado com sucesso! Faça login para continuar.');
        
        setTimeout(() => {
            showLoginForm();
        }, 2000);
    } catch (err) {
        console.error('[CADASTRO] Erro inesperado:', err);
        showError('registerError', 'Erro ao criar conta. Tente novamente.');
    }
});

function showLoginForm() {
    console.log('[NAV] Mostrando tela de login');
    document.getElementById('registerPage').classList.add('hidden');
    document.getElementById('loginPage').classList.remove('hidden');
    document.getElementById('registerForm').reset();
}

function showRegisterForm() {
    console.log('[NAV] Mostrando tela de cadastro');
    document.getElementById('loginPage').classList.add('hidden');
    document.getElementById('registerPage').classList.remove('hidden');
    document.getElementById('loginForm').reset();
}

function logout() {
    console.log('[LOGOUT] Saindo da aplicação');
    currentUser = null;
    currentClass = null;
    document.getElementById('appPage').classList.add('hidden');
    document.getElementById('loginPage').classList.remove('hidden');
    document.getElementById('loginForm').reset();
}

function showApp() {
    console.log('[APP] Carregando aplicação para usuário:', currentUser.papel);
    document.getElementById('loginPage').classList.add('hidden');
    document.getElementById('appPage').classList.remove('hidden');
    
    document.getElementById('userInfo').innerHTML = `
        <strong>${currentUser.nome}</strong><br>
        <small>${getUserRoleLabel()}</small>
    `;
    
    setupNavigation();
}

function getUserRoleLabel() {
    if (currentUser.papel === 'admin') return 'Administrador';
    if (currentUser.papel === 'professor') return 'Professor';
    return `Aluno - ${currentUser.curso === 'mestrado' ? 'Mestrado' : 'Doutorado'}`;
}

function setupNavigation() {
    console.log('[NAV] Configurando navegação para:', currentUser.papel);
    const tabs = document.getElementById('tabs');
    
    if (currentUser.papel === 'admin') {
        tabs.innerHTML = '<button class="tab active" onclick="showPage(\'admin\')">Gerenciar Turmas</button>';
        showPage('admin');
    } else if (currentUser.papel === 'professor') {
        tabs.innerHTML = `
            <button class="tab active" onclick="showPage('turmas')">Minhas Turmas</button>
            <button class="tab" onclick="showPage('orientacoes')">Orientações</button>
        `;
        showPage('turmas');
    } else {
        tabs.innerHTML = `
            <button class="tab active" onclick="showPage('materiais')">Materiais</button>
            <button class="tab" onclick="showPage('enviar')">Enviar Material</button>
            <button class="tab" onclick="showPage('orientacao')">Orientação</button>
        `;
        showPage('materiais');
    }
}

function showPage(page) {
    console.log('[NAV] Navegando para página:', page);
    document.querySelectorAll('.content').forEach(el => el.classList.add('hidden'));
    document.getElementById(`page-${page}`).classList.remove('hidden');
    
    document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
    const clickedTab = Array.from(document.querySelectorAll('.tab')).find(tab => 
        tab.onclick && tab.onclick.toString().includes(page)
    );
    if (clickedTab) clickedTab.classList.add('active');
    
    loadContent(page);
}

function loadContent(page) {
    console.log('[CONTENT] Carregando conteúdo para:', page);
    if (currentUser.papel === 'admin') {
        loadAdminClasses();
    } else if (currentUser.papel === 'professor') {
        if (page === 'turmas') loadProfessorClasses();
        if (page === 'orientacoes') loadProfessorOrientations();
    } else {
        if (page === 'materiais') loadStudentMaterials();
        if (page === 'enviar') loadStudentSendArea();
        if (page === 'orientacao') loadOrientation();
    }
}

// =========================
// ADMINISTRADOR
// =========================

async function loadAdminClasses() {
    console.log('[ADMIN] Carregando dados administrativos...');
    await loadProfessorList();
    await loadStudentList();
    
    try {
        console.log('[ADMIN] Buscando turmas...');
        const { data: classes, error } = await supabase
            .from('aulas')
            .select('*')
            .order('created_at', { ascending: false });
        
        if (error) {
            console.error('[ADMIN] Erro ao buscar turmas:', error);
            throw error;
        }
        
        console.log('[ADMIN] Turmas encontradas:', classes?.length || 0);
        const container = document.getElementById('classList');
        
        if (!classes || classes.length === 0) {
            container.innerHTML = '<p>Nenhuma turma cadastrada ainda.</p>';
            return;
        }
        
        container.innerHTML = classes.map(c => `
            <div class="card">
                <span class="badge badge-${c.curso}">${c.curso.toUpperCase()}</span>
                <h3>${c.nome}</h3>
                <p><strong>Professor ID:</strong> ${c.professor_id}</p>
                <p><strong>Criada em:</strong> ${new Date(c.created_at).toLocaleDateString()}</p>
            </div>
        `).join('');
    } catch (err) {
        console.error('[ADMIN] Erro ao carregar turmas:', err);
    }
    
    await loadProfessorSelect();
}

async function loadProfessorList() {
    try {
        console.log('[ADMIN] Buscando professores...');
        const { data: professors, error } = await supabase
            .from('Usuários')
            .select('*')
            .eq('papel', 'professor')
            .order('nome');
        
        if (error) throw error;
        
        console.log('[ADMIN] Professores encontrados:', professors?.length || 0);
        const container = document.getElementById('professorList');
        
        if (!professors || professors.length === 0) {
            container.innerHTML = '<p>Nenhum professor cadastrado ainda.</p>';
            return;
        }
        
        container.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Nome</th>
                        <th>Email</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    ${professors.map(p => `
                        <tr>
                            <td>${p.nome}</td>
                            <td>${p['e-mail']}</td>
                            <td>
                                <button class="btn" style="padding:6px 12px; background:#ff4444; color:white;" 
                                        onclick="deleteProfessor('${p.id}')">Remover</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (err) {
        console.error('[ADMIN] Erro ao carregar professores:', err);
    }
}

async function deleteProfessor(professorId) {
    if (!confirm('Tem certeza que deseja remover este professor?')) return;
    
    try {
        console.log('[ADMIN] Removendo professor:', professorId);
        const { error } = await supabase
            .from('Usuários')
            .delete()
            .eq('id', professorId);
        
        if (error) throw error;
        
        console.log('[ADMIN] Professor removido com sucesso');
        alert('Professor removido com sucesso!');
        loadAdminClasses();
    } catch (err) {
        console.error('[ADMIN] Erro ao remover professor:', err);
        alert('Erro ao remover professor.');
    }
}

async function loadStudentList() {
    try {
        console.log('[ADMIN] Buscando alunos...');
        const { data: students, error } = await supabase
            .from('Usuários')
            .select('*')
            .eq('papel', 'student')
            .order('nome');
        
        if (error) throw error;
        
        console.log('[ADMIN] Alunos encontrados:', students?.length || 0);
        const container = document.getElementById('studentList');
        
        if (!students || students.length === 0) {
            container.innerHTML = '<p>Nenhum aluno cadastrado ainda.</p>';
            return;
        }
        
        container.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Nome</th>
                        <th>Email</th>
                        <th>Curso</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    ${students.map(s => `
                        <tr>
                            <td>${s.nome}</td>
                            <td>${s['e-mail']}</td>
                            <td>${s.curso === 'mestrado' ? 'Mestrado' : 'Doutorado'}</td>
                            <td>
                                <button class="btn" style="padding:6px 12px; background:#ff4444; color:white;" 
                                        onclick="deleteStudent('${s.id}')">Remover</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (err) {
        console.error('[ADMIN] Erro ao carregar alunos:', err);
    }
}

async function deleteStudent(studentId) {
    if (!confirm('Tem certeza que deseja remover este aluno?')) return;
    
    try {
        console.log('[ADMIN] Removendo aluno:', studentId);
        const { error } = await supabase
            .from('Usuários')
            .delete()
            .eq('id', studentId);
        
        if (error) throw error;
        
        console.log('[ADMIN] Aluno removido com sucesso');
        alert('Aluno removido com sucesso!');
        loadAdminClasses();
    } catch (err) {
        console.error('[ADMIN] Erro ao remover aluno:', err);
        alert('Erro ao remover aluno.');
    }
}

async function loadProfessorSelect() {
    try {
        console.log('[ADMIN] Carregando select de professores...');
        const { data: professors, error } = await supabase
            .from('Usuários')
            .select('*')
            .eq('papel', 'professor')
            .order('nome');
        
        if (error) throw error;
        
        const select = document.getElementById('newClassProfessor');
        select.innerHTML = '<option value="">Selecione um professor</option>' + 
            (professors || []).map(p => `<option value="${p.id}">${p.nome}</option>`).join('');
    } catch (err) {
        console.error('[ADMIN] Erro ao carregar professores:', err);
    }
}

document.getElementById('createProfessorForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    console.log('[ADMIN] Cadastrando novo professor...');
    
    const name = document.getElementById('newProfName').value.trim();
    const email = document.getElementById('newProfEmail').value.trim();
    const password = document.getElementById('newProfPassword').value;
    
    try {
        console.log('[ADMIN] Verificando email duplicado...');
        const { data: existingUser } = await supabase
            .from('Usuários')
            .select('e-mail')
            .eq('e-mail', email)
            .maybeSingle();
        
        if (existingUser) {
            showError('professorModalError', 'Este email já está cadastrado!');
            return;
        }
        
        const passwordHash = await hashPassword(password);
        console.log('[ADMIN] Inserindo professor...');
        
        const { error } = await supabase
            .from('Usuários')
            .insert([{
                'e-mail': email,
                hash_da_senha: passwordHash,
                nome: name,
                papel: 'professor'
            }]);
        
        if (error) throw error;
        
        console.log('[ADMIN] Professor cadastrado com sucesso');
        showSuccess('professorModalSuccess', 'Professor cadastrado com sucesso!');
        
        setTimeout(() => {
            closeModal('createProfessorModal');
            loadAdminClasses();
        }, 1500);
    } catch (err) {
        console.error('[ADMIN] Erro ao cadastrar professor:', err);
        showError('professorModalError', 'Erro ao cadastrar professor.');
    }
});

document.getElementById('newStudentCourse').addEventListener('change', async function() {
    await updateStudentClassesSelect(this.value);
});

async function updateStudentClassesSelect(course) {
    try {
        console.log('[ADMIN] Carregando turmas para curso:', course);
        
        if (!course) {
            console.log('[ADMIN] Nenhum curso selecionado');
            document.getElementById('newStudentClasses').innerHTML = '<option value="">Selecione um curso primeiro</option>';
            return;
        }
        
        const { data: classes, error } = await supabase
            .from('aulas')
            .select('*')
            .eq('curso', course)
            .order('nome');
        
        if (error) {
            console.error('[ADMIN] Erro ao buscar turmas:', error);
            throw error;
        }
        
        console.log('[ADMIN] Turmas encontradas:', classes?.length || 0);
        
        const select = document.getElementById('newStudentClasses');
        
        if (!classes || classes.length === 0) {
            select.innerHTML = '<option value="">Nenhuma turma disponível para este curso</option>';
            console.log('[ADMIN] Nenhuma turma disponível para:', course);
        } else {
            select.innerHTML = classes.map(c => 
                `<option value="${c.id}">${c.nome}</option>`
            ).join('');
            console.log('[ADMIN] Turmas carregadas com sucesso');
        }
    } catch (err) {
        console.error('[ADMIN] Erro ao carregar turmas:', err);
        document.getElementById('newStudentClasses').innerHTML = '<option value="">Erro ao carregar turmas</option>';
    }
}

document.getElementById('createStudentForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    console.log('[ADMIN] Cadastrando novo aluno...');
    
    const name = document.getElementById('newStudentName').value.trim();
    const email = document.getElementById('newStudentEmail').value.trim();
    const password = document.getElementById('newStudentPassword').value;
    const course = document.getElementById('newStudentCourse').value;
    
    try {
        console.log('[ADMIN] Verificando email duplicado...');
        const { data: existingUser } = await supabase
            .from('Usuários')
            .select('e-mail')
            .eq('e-mail', email)
            .maybeSingle();
        
        if (existingUser) {
            showError('studentModalError', 'Este email já está cadastrado!');
            return;
        }
        
        const passwordHash = await hashPassword(password);
        console.log('[ADMIN] Inserindo aluno...');
        
        const { error } = await supabase
            .from('Usuários')
            .insert([{
                'e-mail': email,
                hash_da_senha: passwordHash,
                nome: name,
                papel: 'student',
                curso: course
            }]);
        
        if (error) throw error;
        
        console.log('[ADMIN] Aluno cadastrado com sucesso');
        showSuccess('studentModalSuccess', 'Aluno cadastrado com sucesso!');
        
        setTimeout(() => {
            closeModal('createStudentModal');
            loadAdminClasses();
        }, 1500);
    } catch (err) {
        console.error('[ADMIN] Erro ao cadastrar aluno:', err);
        showError('studentModalError', 'Erro ao cadastrar aluno.');
    }
});

document.getElementById('createClassForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    console.log('[ADMIN] Criando nova turma...');
    
    const name = document.getElementById('newClassName').value.trim();
    const course = document.getElementById('newClassCourse').value;
    const professorId = document.getElementById('newClassProfessor').value;
    
    if (!professorId) {
        alert('Selecione um professor!');
        return;
    }
    
    try {
        console.log('[ADMIN] Inserindo turma:', { name, course, professorId });
        const { error } = await supabase
            .from('aulas')
            .insert([{
                nome: name,
                curso: course,
                professor_id: professorId
            }]);
        
        if (error) throw error;
        
        console.log('[ADMIN] Turma criada com sucesso');
        closeModal('createClassModal');
        loadAdminClasses();
        alert('Turma criada com sucesso!');
    } catch (err) {
        console.error('[ADMIN] Erro ao criar turma:', err);
        alert('Erro ao criar turma.');
    }
});

// =========================
// PROFESSOR
// =========================

async function loadProfessorClasses() {
    try {
        console.log('[PROFESSOR] Carregando turmas do professor:', currentUser.id);
        const { data: classes, error } = await supabase
            .from('aulas')
            .select('*')
            .eq('professor_id', currentUser.id)
            .order('nome');
        
        if (error) throw error;
        
        console.log('[PROFESSOR] Turmas encontradas:', classes?.length || 0);
        const container = document.getElementById('professorClasses');
        
        if (!classes || classes.length === 0) {
            container.innerHTML = '<p>Você ainda não tem turmas atribuídas.</p>';
            return;
        }
        
        container.innerHTML = classes.map(c => `
            <div class="card">
                <span class="badge badge-${c.curso}">${c.curso.toUpperCase()}</span>
                <h3>${c.nome}</h3>
                <button class="btn-card" onclick="openClass('${c.id}')">Abrir Turma</button>
            </div>
        `).join('');
    } catch (err) {
        console.error('[PROFESSOR] Erro ao carregar turmas:', err);
    }
}

async function openClass(classId) {
    try {
        console.log('[PROFESSOR] Abrindo turma:', classId);
        const { data: classData, error } = await supabase
            .from('aulas')
            .select('*')
            .eq('id', classId)
            .single();
        
        if (error) throw error;
        
        currentClass = classData;
        console.log('[PROFESSOR] Turma carregada:', currentClass.nome);
        document.getElementById('className').textContent = currentClass.nome;
        
        await loadClassVideos();
        await loadClassMaterials();
        await loadClassStudents();
        
        document.getElementById('page-turmas').classList.add('hidden');
        document.getElementById('page-turma-detalhe').classList.remove('hidden');
    } catch (err) {
        console.error('[PROFESSOR] Erro ao abrir turma:', err);
    }
}

async function loadClassVideos() {
    try {
        console.log('[PROFESSOR] Carregando vídeos da turma:', currentClass.id);
        const { data: videos, error } = await supabase
            .from('materiais')
            .select('*')
            .eq('aula_id', currentClass.id)
            .eq('tipo', 'video')
            .order('created_at', { ascending: false });
        
        if (error) throw error;
        
        console.log('[PROFESSOR] Vídeos encontrados:', videos?.length || 0);
        const container = document.getElementById('classVideos');
        
        if (!videos || videos.length === 0) {
            container.innerHTML = '<p>Nenhuma vídeo-aula enviada ainda.</p>';
            return;
        }
        
        container.innerHTML = videos.map(v => `
            <div class="card">
                <h3>🎥 ${v.titulo}</h3>
                <p>${v.descricao || ''}</p>
                <p style="font-size:12px; color:#999;">Enviado em ${new Date(v.created_at).toLocaleDateString()}</p>
            </div>
        `).join('');
    } catch (err) {
        console.error('[PROFESSOR] Erro ao carregar vídeos:', err);
    }
}

async function loadClassMaterials() {
    try {
        console.log('[PROFESSOR] Carregando materiais da turma:', currentClass.id);
        const { data: materials, error } = await supabase
            .from('materiais')
            .select('*')
            .eq('aula_id', currentClass.id)
            .eq('tipo', 'document')
            .order('created_at', { ascending: false });
        
        if (error) throw error;
        
        console.log('[PROFESSOR] Materiais encontrados:', materials?.length || 0);
        const container = document.getElementById('classMaterials');
        
        if (!materials || materials.length === 0) {
            container.innerHTML = '<p>Nenhum material enviado ainda.</p>';
            return;
        }
        
        container.innerHTML = materials.map(m => `
            <div class="card">
                <h3>📄 ${m.titulo}</h3>
                <p>${m.descricao || ''}</p>
                <p style="font-size:12px; color:#999;">Enviado em ${new Date(m.created_at).toLocaleDateString()}</p>
            </div>
        `).join('');
    } catch (err) {
        console.error('[PROFESSOR] Erro ao carregar materiais:', err);
    }
}

async function loadClassStudents() {
    try {
        console.log('[PROFESSOR] Carregando alunos da turma:', currentClass.id);
        const { data: students, error } = await supabase
            .from('Usuários')
            .select('*')
            .eq('papel', 'student')
            .eq('curso', currentClass.curso)
            .order('nome');
        
        if (error) throw error;
        
        console.log('[PROFESSOR] Alunos encontrados:', students?.length || 0);
        const container = document.getElementById('classStudents');
        
        if (!students || students.length === 0) {
            container.innerHTML = '<p>Nenhum aluno matriculado ainda.</p>';
            return;
        }
        
        container.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Nome</th>
                        <th>Email</th>
                        <th>Curso</th>
                    </tr>
                </thead>
                <tbody>
                    ${students.map(s => `
                        <tr>
                            <td>${s.nome}</td>
                            <td>${s['e-mail']}</td>
                            <td>${s.curso === 'mestrado' ? 'Mestrado' : 'Doutorado'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (err) {
        console.error('[PROFESSOR] Erro ao carregar alunos:', err);
    }
}

document.getElementById('uploadVideoForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    console.log('[PROFESSOR] Enviando vídeo-aula...');
    
    const title = document.getElementById('videoTitleInput').value.trim();
    const description = document.getElementById('videoDescriptionInput').value.trim();
    const fileInput = document.getElementById('videoFile');
    
    if (!fileInput.files[0]) {
        alert('Selecione um arquivo de vídeo!');
        return;
    }
    
    try {
        const fileName = fileInput.files[0].name;
        console.log('[PROFESSOR] Inserindo vídeo:', { title, fileName });
        
        const { error } = await supabase
            .from('materiais')
            .insert([{
                aula_id: currentClass.id,
                professor_id: currentUser.id,
                titulo: title,
                tipo: 'video',
                arquivo: fileName,
                descricao: description
            }]);
        
        if (error) throw error;
        
        console.log('[PROFESSOR] Vídeo enviado com sucesso');
        closeModal('uploadVideoModal');
        loadClassVideos();
        alert('Vídeo-aula enviada com sucesso!');
    } catch (err) {
        console.error('[PROFESSOR] Erro ao enviar vídeo:', err);
        alert('Erro ao enviar vídeo.');
    }
});

document.getElementById('uploadMaterialForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    console.log('[PROFESSOR] Enviando material...');
    
    const title = document.getElementById('materialTitle').value.trim();
    const description = document.getElementById('materialDescription').value.trim();
    const fileInput = document.getElementById('materialFile');
    
    if (!fileInput.files[0]) {
        alert('Selecione um arquivo!');
        return;
    }
    
    try {
        const fileName = fileInput.files[0].name;
        console.log('[PROFESSOR] Inserindo material:', { title, fileName });
        
        const { error } = await supabase
            .from('materiais')
            .insert([{
                aula_id: currentClass.id,
                professor_id: currentUser.id,
                titulo: title,
                tipo: 'document',
                arquivo: fileName,
                descricao: description
            }]);
        
        if (error) throw error;
        
        console.log('[PROFESSOR] Material enviado com sucesso');
        closeModal('uploadMaterialModal');
        loadClassMaterials();
        alert('Material enviado com sucesso!');
    } catch (err) {
        console.error('[PROFESSOR] Erro ao enviar material:', err);
        alert('Erro ao enviar material.');
    }
});

async function loadProfessorOrientations() {
    try {
        console.log('[PROFESSOR] Carregando orientações...');
        const { data: students, error } = await supabase
            .from('Usuários')
            .select('*')
            .eq('papel', 'student')
            .order('nome');
        
        if (error) throw error;
        
        console.log('[PROFESSOR] Orientandos encontrados:', students?.length || 0);
        const container = document.getElementById('professorOrientations');
        
        if (!students || students.length === 0) {
            container.innerHTML = '<p>Nenhum orientando ainda.</p>';
            return;
        }
        
        container.innerHTML = students.map(s => `
            <div class="card">
                <h3>${s.nome}</h3>
                <p><strong>Curso:</strong> ${s.curso === 'mestrado' ? 'Mestrado' : 'Doutorado'}</p>
                <p><strong>Email:</strong> ${s['e-mail']}</p>
            </div>
        `).join('');
    } catch (err) {
        console.error('[PROFESSOR] Erro ao carregar orientações:', err);
    }
}

// =========================
// ALUNO
// =========================

async function loadStudentMaterials() {
    try {
        console.log('[ALUNO] Carregando materiais disponíveis...');
        const { data: materials, error } = await supabase
            .from('materiais')
            .select('*, aulas(nome, curso)')
            .order('created_at', { ascending: false });
        
        if (error) throw error;
        
        console.log('[ALUNO] Materiais encontrados:', materials?.length || 0);
        const container = document.getElementById('studentMaterials');
        
        if (!materials || materials.length === 0) {
            container.innerHTML = '<p>Nenhum material disponível.</p>';
            return;
        }
        
        const filteredMaterials = materials.filter(m => 
            m.aulas && m.aulas.curso === currentUser.curso
        );
        
        console.log('[ALUNO] Materiais filtrados por curso:', filteredMaterials.length);
        
        if (filteredMaterials.length === 0) {
            container.innerHTML = '<p>Nenhum material disponível para seu curso.</p>';
            return;
        }
        
        container.innerHTML = filteredMaterials.map(m => {
            const classInfo = m.aulas;
            return `
                <div class="card">
                    <span class="badge badge-${classInfo?.curso || 'mestrado'}">${classInfo?.nome || 'Turma'}</span>
                    <h3>${m.tipo === 'video' ? '🎥' : '📄'} ${m.titulo}</h3>
                    <p>${m.descricao || ''}</p>
                    <p style="font-size:12px; color:#999;">Enviado em ${new Date(m.created_at).toLocaleDateString()}</p>
                    ${m.tipo === 'video' 
                        ? `<button class="btn-card" onclick="watchVideo('${m.id}')">Assistir Aula</button>`
                        : `<button class="btn-card">Baixar Material</button>`
                    }
                </div>
            `;
        }).join('');
    } catch (err) {
        console.error('[ALUNO] Erro ao carregar materiais:', err);
    }
}

async function watchVideo(materialId) {
    try {
        console.log('[ALUNO] Carregando vídeo:', materialId);
        const { data: material, error } = await supabase
            .from('materiais')
            .select('*')
            .eq('id', materialId)
            .single();
        
        if (error) throw error;
        
        console.log('[ALUNO] Vídeo carregado:', material.titulo);
        document.getElementById('videoTitle').textContent = material.titulo;
        document.getElementById('videoDescription').innerHTML = `
            <p>${material.descricao || ''}</p>
            <p style="color:#666; font-size:14px; margin-top:10px;">
                Enviado em ${new Date(material.created_at).toLocaleDateString()}
            </p>
        `;
        
        document.getElementById('videoPlayerContainer').innerHTML = `
            <div class="video-player">
                <p style="padding:100px; text-align:center; color:white;">
                    Vídeo: ${material.arquivo}<br>
                    (Player será carregado quando o arquivo real for enviado)
                </p>
            </div>
        `;
        
        document.getElementById('page-materiais').classList.add('hidden');
        document.getElementById('page-assistir').classList.remove('hidden');
    } catch (err) {
        console.error('[ALUNO] Erro ao carregar vídeo:', err);
    }
}

async function loadStudentSendArea() {
    try {
        console.log('[ALUNO] Carregando turmas disponíveis...');
        const { data: classes, error } = await supabase
            .from('aulas')
            .select('*')
            .eq('curso', currentUser.curso)
            .order('nome');
        
        if (error) throw error;
        
        console.log('[ALUNO] Turmas encontradas:', classes?.length || 0);
        const select = document.getElementById('selectClassToSend');
        
        if (!classes || classes.length === 0) {
            select.innerHTML = '<option value="">Nenhuma turma disponível</option>';
        } else {
            select.innerHTML = '<option value="">Selecione uma turma</option>' + 
                classes.map(c => `<option value="${c.id}">${c.nome}</option>`).join('');
        }
    } catch (err) {
        console.error('[ALUNO] Erro ao carregar turmas:', err);
    }
}

async function sendStudentFile() {
    const classId = document.getElementById('selectClassToSend').value;
    const title = document.getElementById('studentFileTitle').value.trim();
    const description = document.getElementById('studentFileDesc').value.trim();
    const fileInput = document.getElementById('studentFileInput');
    
    if (!classId || !title || !fileInput.files[0]) {
        alert('Preencha todos os campos e selecione um arquivo!');
        return;
    }
    
    try {
        console.log('[ALUNO] Enviando arquivo para turma:', classId);
        const { data: classData } = await supabase
            .from('aulas')
            .select('professor_id')
            .eq('id', classId)
            .single();
        
        const fileName = fileInput.files[0].name;
        console.log('[ALUNO] Inserindo material:', { title, fileName });
        
        const { error } = await supabase
            .from('materiais')
            .insert([{
                aula_id: classId,
                professor_id: classData?.professor_id,
                titulo: title,
                tipo: 'student_submission',
                arquivo: fileName,
                descricao: description
            }]);
        
        if (error) throw error;
        
        console.log('[ALUNO] Material enviado com sucesso');
        document.getElementById('studentFileTitle').value = '';
        document.getElementById('studentFileDesc').value = '';
        fileInput.value = '';
        document.getElementById('studentFileName').textContent = 'Nenhum arquivo selecionado';
        
        alert('Material enviado com sucesso!');
    } catch (err) {
        console.error('[ALUNO] Erro ao enviar arquivo:', err);
        alert('Erro ao enviar arquivo.');
    }
}

async function loadOrientation() {
    console.log('[ALUNO] Carregando área de orientação...');
    await loadChatMessages();
    await loadOrientationDocuments();
}

async function loadChatMessages() {
    try {
        console.log('[ALUNO] Carregando mensagens de chat...');
        const { data: orientations, error } = await supabase
            .from('orientacoes')
            .select('*')
            .eq('aluno_id', currentUser.id)
            .order('created_at', { ascending: false })
            .limit(1);
        
        if (error) throw error;
        
        const container = document.getElementById('chatMessages');
        
        if (!orientations || orientations.length === 0 || !orientations[0].mensagens) {
            container.innerHTML = '<p style="text-align:center; padding:20px; color:#666;">Nenhuma mensagem ainda. Comece a conversa!</p>';
            return;
        }
        
        const messages = orientations[0].mensagens || [];
        console.log('[ALUNO] Mensagens encontradas:', messages.length);
        
        container.innerHTML = messages.map(m => `
            <div class="chat-message ${m.remetente === currentUser.id ? 'sent' : 'received'}">
                <p>${m.texto}</p>
                <small style="opacity:0.7;">${new Date(m.timestamp).toLocaleTimeString()}</small>
            </div>
        `).join('');
        
        container.scrollTop = container.scrollHeight;
    } catch (err) {
        console.error('[ALUNO] Erro ao carregar mensagens:', err);
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    try {
        console.log('[ALUNO] Enviando mensagem de chat...');
        const { data: existingOrientations } = await supabase
            .from('orientacoes')
            .select('*')
            .eq('aluno_id', currentUser.id)
            .limit(1);
        
        const newMessage = {
            remetente: currentUser.id,
            texto: message,
            timestamp: new Date().toISOString()
        };
        
        if (existingOrientations && existingOrientations.length > 0) {
            console.log('[ALUNO] Atualizando orientação existente');
            const orientation = existingOrientations[0];
            const messages = orientation.mensagens || [];
            messages.push(newMessage);
            
            const { error } = await supabase
                .from('orientacoes')
                .update({ mensagens: messages })
                .eq('id', orientation.id);
            
            if (error) throw error;
        } else {
            console.log('[ALUNO] Criando nova orientação');
            const { error } = await supabase
                .from('orientacoes')
                .insert([{
                    aluno_id: currentUser.id,
                    mensagens: [newMessage]
                }]);
            
            if (error) throw error;
        }
        
        input.value = '';
        loadChatMessages();
    } catch (err) {
        console.error('[ALUNO] Erro ao enviar mensagem:', err);
        alert('Erro ao enviar mensagem.');
    }
}

async function loadOrientationDocuments() {
    console.log('[ALUNO] Função loadOrientationDocuments ainda não implementada');
}

// =========================
// INICIALIZAÇÃO
// =========================

window.addEventListener('DOMContentLoaded', function() {
    console.log('[IBES] DOM carregado, inicializando aplicação...');
    
    if (!initSupabase()) {
        console.error('[IBES] Falha ao inicializar Supabase');
        return;
    }
    
    console.log('[IBES] Aplicação inicializada com sucesso');
});
