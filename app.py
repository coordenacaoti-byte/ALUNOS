import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io
from supabase import create_client, Client

# Configuração da página
st.set_page_config(
    page_title="Sistema de Gestão Escolar",
    page_icon="🏫",
    layout="wide"
)

# ---------------------------------------------------------
# CONEXÃO COM O SUPABASE
# ---------------------------------------------------------
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["SUPABASE_URL"]
    key = st.secrets["supabase"]["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Funções de Interação com o Supabase
def carregar_alunos():
    response = supabase.table("alunos").select("*").execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        renames = {
            "nome": "Nome",
            "cpf": "CPF",
            "data_nasc": "Data Nasc.",
            "escola_origem": "Escola Origem",
            "turma": "Turma",
            "observacoes": "Observações"
        }
        if "endereco" in df.columns:
            renames["endereco"] = "Endereço"
        df = df.rename(columns=renames)
    else:
        df = pd.DataFrame(columns=["Nome", "CPF", "Data Nasc.", "Escola Origem", "Turma", "Endereço", "Observações"])
    return df

def salvar_aluno(nome, cpf, data_nasc, escola_origem, turma, endereco, observacoes):
    dados = {
        "nome": nome,
        "cpf": cpf,
        "data_nasc": str(data_nasc),
        "escola_origem": escola_origem,
        "turma": turma,
        "endereco": endereco,
        "observacoes": observacoes
    }
    supabase.table("alunos").insert(dados).execute()

def salvar_alunos_em_lote(df_lote):
    renames = {
        "Nome": "nome",
        "CPF": "cpf",
        "Data Nasc.": "data_nasc",
        "Escola Origem": "escola_origem",
        "Turma": "turma",
        "Observações": "observacoes"
    }
    if "Endereço" in df_lote.columns:
        renames["Endereço"] = "endereco"
    elif "Endereco" in df_lote.columns:
        renames["Endereco"] = "endereco"
        
    df_lote = df_lote.rename(columns=renames)
    if "data_nasc" in df_lote.columns:
        df_lote["data_nasc"] = df_lote["data_nasc"].astype(str)
        
    registros = df_lote.fillna("").to_dict(orient="records")
    supabase.table("alunos").insert(registros).execute()

def carregar_usuarios():
    response = supabase.table("usuarios").select("*").execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        df = df.rename(columns={
            "usuario": "Usuario",
            "senha": "Senha",
            "nome": "Nome",
            "perfil": "Perfil"
        })
    return df

def salvar_usuario(usr, pwd, nome, perfil):
    dados = {
        "usuario": usr,
        "senha": pwd,
        "nome": nome,
        "perfil": perfil
    }
    supabase.table("usuarios").insert(dados).execute()

def remover_usuario(usr):
    supabase.table("usuarios").delete().eq("usuario", usr).execute()

# ---------------------------------------------------------
# ESTILIZAÇÃO CSS
# ---------------------------------------------------------
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc !important; color: #0f172a !important; }
    h1, h2, h3, h4, label, .stMarkdown { color: #0f172a !important; font-family: 'Inter', sans-serif; }
    
    [data-testid="stForm"] {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 16px !important;
        padding: 25px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05) !important;
        margin-bottom: 20px !important;
    }

    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea, .stDateInput input {
        background-color: #ffffff !important;
        border: 1.5px solid #94a3b8 !important;
        border-radius: 8px !important;
        color: #0f172a !important;
        font-weight: 500 !important;
    }

    .stFormSubmitButton > button, .stButton > button, .stDownloadButton > button {
        background-color: #4f46e5 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.3) !important;
    }

    .kpi-card {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .kpi-title { font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; }
    .kpi-value { font-size: 1.875rem; font-weight: 800; color: #0f172a; margin: 4px 0; }
    .kpi-subtitle { font-size: 0.75rem; font-weight: 600; }
    .kpi-icon { width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
    .icon-purple { background-color: #e0e7ff; color: #4f46e5; }
    .icon-green { background-color: #d1fae5; color: #10b981; }
    .icon-yellow { background-color: #fef3c7; color: #f59e0b; }
    .icon-blue { background-color: #e0f2fe; color: #0284c7; }

    .import-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
        margin-bottom: 12px;
    }
    .step-badge {
        display: inline-block;
        background-color: #e0e7ff;
        color: #4f46e5;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
        margin-bottom: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# Lista de Escolas
ESCOLAS = [
    "Adélia Carneiro Pedrosa", "Arcendrino César de Albuquerque", "Capela de São Sebastião",
    "Cônego Fernando Passos", "Creche Municipal Profª Etenile Urbano Pessoa", "Diogo Dias",
    "Dr. Araújo Filho", "Dr. Benigno Araújo", "Dr. Clóvis Fontenelle Guimarães",
    "Dr. Ludovico Correia", "Dr. Manoel Borba", "Edith Gadelha", "Eufrásio Vilarim",
    "Francisco Nicolau da Silva", "Heroínas de Tejucupapo", "Iracema Nogueira Rabelo",
    "Irmã Marie Armelle Falguières", "IV Centenário", "João Carneiro de Melo",
    "João Gonçalves de Azevedo", "José Maciel da Silva", "Lourenço de Albuquerque Gadelha (DISTRITO)",
    "Lourenço de Albuquerque Gadelha (SEDE)", "Major Manoel Gadelha", "Manuel César de Albuquerque",
    "Nossa Senhora das Maravilhas", "Prefeito Ângelo Jordão", "Presidente Costa e Silva",
    "Profª. Belisana Pinto Abreu de Araújo", "Profª. Cynira Florianna dos Prazeres",
    "Profª. Lizete Maria de Souza Rodrigues", "Profª. Mª Emília Valença da Silveira",
    "Profª. Tarcila Coutinho Amaral", "Profª. Zilma Gemir Baracho", "Santa Maria",
    "Santo Antônio de Pádua", "São Thomaz de Aquino", "Creche Criança Feliz",
    "CMEI - Vereador Jose Batista dos Santos", "CMEI - Prefeito Osvaldo Rabelo Filho",
    "CMEI - Carlos Alberto dos Santos Viegas",
    "Centro de Atendimento de Educação Especial Professora Margarida Braga",
    "Edjanete Maria Valença da Silveira"
]

def gerar_planilha_modelo():
    buffer = io.BytesIO()
    df_modelo = pd.DataFrame({
        "Nome": ["Exemplo Nome Aluno"],
        "CPF": ["000.000.000-00"],
        "Data Nasc.": ["2015-01-01"],
        "Escola Origem": ["Escola Municipal Dom Pedro II"],
        "Turma": ["1º Ano A"],
        "Endereço": ["Rua Exemplo, Nº 100, Bairro Centenário"],
        "Observações": ["Sem observações"]
    })
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_modelo.to_excel(writer, index=False, sheet_name='Modelo_Importacao')
    return buffer.getvalue()

# Estado de Login na Sessão
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

# ---------------------------------------------------------
# TELA DE ACESSO (LOGIN)
# ---------------------------------------------------------
if st.session_state["usuario_logado"] is None:
    col_logo, col_login, col_espaco = st.columns([1, 1.5, 1])
    with col_login:
        st.markdown("<h2 style='text-align: center;'>🏫 Sistema de Gestão Escolar</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>Acesse com suas credenciais para continuar</p>", unsafe_allow_html=True)
        
        with st.form("form_login"):
            usr_input = st.text_input("Usuário")
            pwd_input = st.text_input("Senha", type="password")
            btn_entrar = st.form_submit_button("🔒 Entrar no Sistema", use_container_width=True)
            
            if btn_entrar:
                df_usr = carregar_usuarios()
                match = df_usr[(df_usr["Usuario"] == usr_input) & (df_usr["Senha"] == pwd_input)]
                
                if not match.empty:
                    st.session_state["usuario_logado"] = match.iloc[0].to_dict()
                    st.success("Login efetuado com sucesso!")
                    st.rerun()
                else:
                    st.error("⚠️ Usuário ou senha incorretos.")

# ---------------------------------------------------------
# ÁREA LOGADA DO SISTEMA
# ---------------------------------------------------------
else:
    usr = st.session_state["usuario_logado"]
    col_title, col_user = st.columns([3, 1])
    
    with col_title:
        st.title("🏫 Sistema de Gestão Escolar & Transferências")
    with col_user:
        st.write(f"👤 **{usr['Nome']}**")
        st.caption(f"Perfil: {usr['Perfil']}")
        if st.button("🚪 Sair", key="btn_logout"):
            st.session_state["usuario_logado"] = None
            st.rerun()

    # Abas por perfil
    if usr["Perfil"] == "Administrador":
        aba_cadastro, aba_admin, aba_gestao_usuarios = st.tabs([
            "📝 Cadastro de Alunos", 
            "📊 Área do Administrador (Dashboard)",
            "👥 Gestão de Usuários"
        ])
    else:
        aba_cadastro, = st.tabs(["📝 Cadastro de Alunos"])
        aba_admin = None
        aba_gestao_usuarios = None

    # ---------------------------------------------------------
    # ABA 1: CADASTRO E IMPORTAÇÃO
    # ---------------------------------------------------------
    with aba_cadastro:
        st.subheader("📝 Cadastro Individual de Aluno")
        
        with st.form("form_cadastro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome Completo do Aluno *")
                cpf = st.text_input("CPF do Aluno *", placeholder="000.000.000-00")
                data_nasc = st.date_input("Data de Nascimento")
            with col2:
                escola_origem = st.selectbox("Escola de Origem *", options=ESCOLAS)
                turma = st.text_input("Série / Turma *", placeholder="Ex: 5º Ano A")
                endereco = st.text_input("Endereço Completo")

            observacoes = st.text_area("Observações")

            st.markdown("<br>", unsafe_allow_html=True)
            btn_salvar = st.form_submit_button("💾 Salvar Cadastro")
            
            if btn_salvar:
                if nome and cpf and escola_origem:
                    salvar_aluno(nome, cpf, str(data_nasc), escola_origem, turma, endereco, observacoes)
                    st.success(f"✅ Aluno(a) **{nome}** salvo no Supabase com sucesso!")
                else:
                    st.error("⚠️ Preencha todos os campos obrigatórios (*).")

        st.markdown("---")

        # IMPORTAÇÃO EM LOTE
        st.markdown("<h3 style='margin-top: 20px; margin-bottom: 20px;'>📥 Importação de Alunos em Lote</h3>", unsafe_allow_html=True)

        col_left, col_right = st.columns(2, gap="medium")

        with col_left:
            st.markdown("""
            <div class="import-card">
                <div>
                    <span class="step-badge">Passo 1</span>
                    <div class="card-header-title">📄 Baixar Planilha Modelo</div>
                    <div class="card-description">
                        Baixe o modelo oficial para preencher as informações dos alunos.
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.download_button(
                label="📥 Baixar Modelo (.xlsx)",
                data=gerar_planilha_modelo(),
                file_name="modelo_importacao_alunos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col_right:
            st.markdown("""
            <div class="import-card">
                <div>
                    <span class="step-badge" style="background-color: #d1fae5; color: #059669;">Passo 2</span>
                    <div class="card-header-title">📤 Upload da Planilha Preenchida</div>
                    <div class="card-description">
                        Envie o arquivo (.XLSX ou .CSV) para salvar todos os registros no Supabase.
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            arquivo_enviado = st.file_uploader("Arraste ou selecione seu arquivo", type=["xlsx", "csv"], key="uploader_lote_novo", label_visibility="collapsed")

        if arquivo_enviado is not None:
            st.markdown("<br>", unsafe_allow_html=True)
            try:
                df_upload = pd.read_csv(arquivo_enviado) if arquivo_enviado.name.endswith('.csv') else pd.read_excel(arquivo_enviado)
                st.success(f"✅ **Arquivo carregado com sucesso!** Foram encontrados **{len(df_upload)}** registros.")
                
                with st.expander("🔍 Pré-visualizar dados importados", expanded=True):
                    st.dataframe(df_upload, use_container_width=True)
                
                if st.button("🚀 Confirmar e Integrar Registros no Supabase", use_container_width=True):
                    salvar_alunos_em_lote(df_upload)
                    st.balloons()
                    st.success(f"🎉 Todos os {len(df_upload)} alunos foram salvos no banco de dados Supabase!")
            except Exception as e:
                st.error(f"❌ Erro ao processar o arquivo: {e}")

    # ---------------------------------------------------------
    # ABA 2: DASHBOARD DO ADMINISTRADOR
    # ---------------------------------------------------------
    if aba_admin:
        with aba_admin:
            df = carregar_alunos()
            
            total_alunos = len(df)
            escolas_ativas = df["Escola Origem"].nunique() if not df.empty and "Escola Origem" in df.columns else 0
            
            if not df.empty and "Data Nasc." in df.columns:
                df['Data_dt'] = pd.to_datetime(df['Data Nasc.'], errors='coerce')
                ano_atual = datetime.now().year
                df['Idade'] = ano_atual - df['Data_dt'].dt.year
                media_idade = round(df['Idade'].mean(), 1) if not df['Idade'].isna().all() else 0.0
            else:
                media_idade = 0.0

            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                st.markdown(f"""
                    <div class="kpi-card">
                        <div>
                            <div class="kpi-title">TOTAL DE ALUNOS</div>
                            <div class="kpi-value">{total_alunos}</div>
                            <div class="kpi-subtitle" style="color: #10b981;">📈 Supabase Nuvem</div>
                        </div>
                        <div class="kpi-icon icon-purple">👥</div>
                    </div>
                """, unsafe_allow_html=True)
                
            with c2:
                st.markdown(f"""
                    <div class="kpi-card">
                        <div>
                            <div class="kpi-title">ESCOLAS ATIVAS</div>
                            <div class="kpi-value">{escolas_ativas}</div>
                            <div class="kpi-subtitle" style="color: #64748b;">Instituições cadastradas</div>
                        </div>
                        <div class="kpi-icon icon-green">🏫</div>
                    </div>
                """, unsafe_allow_html=True)
                
            with c3:
                st.markdown(f"""
                    <div class="kpi-card">
                        <div>
                            <div class="kpi-title">MÉDIA DE IDADE</div>
                            <div class="kpi-value">{media_idade} <span style="font-size:1rem; font-weight:normal;">anos</span></div>
                            <div class="kpi-subtitle" style="color: #64748b;">Calculado por data nasc.</div>
                        </div>
                        <div class="kpi-icon icon-yellow">🎂</div>
                    </div>
                """, unsafe_allow_html=True)

            with c4:
                st.markdown("""
                    <div class="kpi-card">
                        <div>
                            <div class="kpi-title">STATUS DO BANCO</div>
                            <div class="kpi-value">Ativo</div>
                            <div class="kpi-subtitle" style="color: #10b981;">Conectado ao PostgreSQL</div>
                        </div>
                        <div class="kpi-icon icon-blue">⚡</div>
                    </div>
                """, unsafe_allow_html=True)

            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.markdown("### 📊 Cadastros por Escola")
                if not df.empty and "Escola Origem" in df.columns:
                    df_escola = df['Escola Origem'].value_counts().reset_index()
                    df_escola.columns = ['Escola', 'Qtd']
                    
                    fig_barras = px.bar(df_escola, x='Escola', y='Qtd', color_discrete_sequence=['#4f46e5'])
                    fig_barras.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), xaxis_title=None, yaxis_title=None)
                    st.plotly_chart(fig_barras, use_container_width=True)
                    
            with col_g2:
                st.markdown("### 🍕 Distribuição por Faixa Etária")
                if not df.empty and 'Idade' in df.columns:
                    def faixa_etaria(idade):
                        if idade <= 10: return 'Até 10 anos'
                        elif 11 <= idade <= 14: return '11 a 14 anos'
                        else: return '15+ anos'
                        
                    df['Faixa'] = df['Idade'].apply(faixa_etaria)
                    df_faixa = df['Faixa'].value_counts().reset_index()
                    df_faixa.columns = ['Faixa', 'Qtd']
                    
                    fig_donut = px.pie(df_faixa, names='Faixa', values='Qtd', hole=0.6, color_discrete_sequence=['#10b981', '#3b82f6', '#f59e0b'])
                    fig_donut.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), showlegend=True)
                    st.plotly_chart(fig_donut, use_container_width=True)

            st.markdown("---")
            st.markdown("### 📋 Base de Dados do Supabase")
            
            cols_exibicao = [c for c in ["Nome", "CPF", "Data Nasc.", "Escola Origem", "Turma", "Endereço", "Observações"] if c in df.columns]
            st.dataframe(df[cols_exibicao] if not df.empty else df, use_container_width=True)
            
            if not df.empty:
                csv = df[cols_exibicao].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Exportar CSV do Supabase",
                    data=csv,
                    file_name="base_alunos_supabase.csv",
                    mime="text/csv"
                )

    # ---------------------------------------------------------
    # ABA 3: GESTÃO DE USUÁRIOS
    # ---------------------------------------------------------
    if aba_gestao_usuarios:
        with aba_gestao_usuarios:
            st.subheader("👥 Controle de Acessos e Usuários (Supabase)")
            
            col_novo, col_lista = st.columns([1, 1.5])
            
            with col_novo:
                st.markdown("#### ➕ Cadastrar Novo Usuário")
                with st.form("form_novo_usuario", clear_on_submit=True):
                    novo_nome = st.text_input("Nome Completo *")
                    novo_usr = st.text_input("Nome de Usuário (Login) *")
                    nova_senha = st.text_input("Senha *", type="password")
                    novo_perfil = st.selectbox("Perfil de Acesso *", ["Usuário Comum", "Administrador"])
                    
                    btn_cad_usr = st.form_submit_button("➕ Criar Usuário")
                    if btn_cad_usr:
                        if novo_nome and novo_usr and nova_senha:
                            df_usrs = carregar_usuarios()
                            if not df_usrs.empty and novo_usr in df_usrs["Usuario"].values:
                                st.error("⚠️ Este nome de usuário já existe.")
                            else:
                                salvar_usuario(novo_usr, nova_senha, novo_nome, novo_perfil)
                                st.success(f"✅ Usuário **{novo_usr}** salvo no Supabase!")
                                st.rerun()
                        else:
                            st.error("⚠️ Preencha todos os campos obrigatórios.")
            
            with col_lista:
                st.markdown("#### 📋 Usuários Cadastrados")
                df_usrs_atual = carregar_usuarios()
                if not df_usrs_atual.empty:
                    st.dataframe(df_usrs_atual[["Nome", "Usuario", "Perfil"]], use_container_width=True)
                
                st.markdown("#### 🗑️ Remover Usuário")
                if not df_usrs_atual.empty:
                    usuarios_existentes = [u for u in df_usrs_atual["Usuario"].tolist() if u != "admin"]
                    if usuarios_existentes:
                        usr_para_remover = st.selectbox("Selecione o usuário para remover", usuarios_existentes)
                        if st.button("❌ Confirmar Remoção"):
                            remover_usuario(usr_para_remover)
                            st.success(f"Usuário **{usr_para_remover}** removido do Supabase!")
                            st.rerun()
                    else:
                        st.caption("Nenhum usuário secundário disponível para remoção.")
