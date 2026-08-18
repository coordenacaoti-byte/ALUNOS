import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import io
import base64
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

# ---------------------------------------------------------
# FUNÇÕES DE CONFIGURAÇÕES DE PERSONALIZAÇÃO (TITULOS E LOGO)
# ---------------------------------------------------------
def carregar_configuracoes():
    """Carrega as configurações do sistema (Títulos e Logo em Base64) do Supabase"""
    config_padrao = {
        "titulo_login": "Sistema de Gestão Escolar",
        "subtitulo_login": "Acesse com suas credenciais para continuar",
        "titulo_interno": "Sistema de Gestão Escolar & Transferências",
        "logo_base64": None
    }
    try:
        response = supabase.table("configuracoes_sistema").select("*").eq("id", 1).execute()
        if response.data and len(response.data) > 0:
            dados = response.data[0]
            return {
                "titulo_login": dados.get("titulo_login") or config_padrao["titulo_login"],
                "subtitulo_login": dados.get("subtitulo_login") or config_padrao["subtitulo_login"],
                "titulo_interno": dados.get("titulo_interno") or config_padrao["titulo_interno"],
                "logo_base64": dados.get("logo_base64")
            }
    except Exception:
        pass
    return config_padrao

def salvar_configuracoes(titulo_login, subtitulo_login, titulo_interno, logo_base64=None, atualizar_logo=False):
    """Salva os títulos e/ou imagem no Supabase"""
    try:
        dados_update = {
            "id": 1,
            "titulo_login": titulo_login,
            "subtitulo_login": subtitulo_login,
            "titulo_interno": titulo_interno
        }
        if atualizar_logo:
            dados_update["logo_base64"] = logo_base64

        supabase.table("configuracoes_sistema").upsert(dados_update).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar configurações do sistema: {e}")
        return False

# Carrega as configurações visuais ativas
config_sys = carregar_configuracoes()

# ---------------------------------------------------------
# FUNÇÃO DE LOGS DE AUDITORIA (TABELA SEPARADA)
# ---------------------------------------------------------
def registrar_log(usuario: str, acao: str, detalhes: str = ""):
    """Grava logs em uma tabela independente 'logs_auditoria' no Supabase"""
    try:
        dados_log = {
            "usuario": usuario,
            "acao": acao,
            "detalhes": detalhes
        }
        supabase.table("logs_auditoria").insert(dados_log).execute()
    except Exception as e:
        st.error(f"Erro ao registrar log de auditoria: {e}")

def carregar_logs():
    """Carrega o histórico de logs gravados na tabela logs_auditoria"""
    try:
        response = supabase.table("logs_auditoria").select("*").order("data_hora", desc=True).execute()
        df_logs = pd.DataFrame(response.data)
        if not df_logs.empty:
            renames = {
                "usuario": "Usuário Responsável",
                "acao": "Ação / Evento",
                "detalhes": "Detalhes do Registro",
                "data_hora": "Data/Hora"
            }
            df_logs = df_logs.rename(columns=renames)
            if "Data/Hora" in df_logs.columns:
                df_logs["Data/Hora"] = pd.to_datetime(df_logs["Data/Hora"], errors='coerce').dt.strftime('%d/%m/%Y %H:%M:%S')
            cols_ordem = [c for c in ["Data/Hora", "Usuário Responsável", "Ação / Evento", "Detalhes do Registro"] if c in df_logs.columns]
            return df_logs[cols_ordem]
        else:
            return pd.DataFrame(columns=["Data/Hora", "Usuário Responsável", "Ação / Evento", "Detalhes do Registro"])
    except Exception as e:
        return pd.DataFrame(columns=["Data/Hora", "Usuário Responsável", "Ação / Evento", "Detalhes do Registro"])

def limpar_tabela_logs():
    """Limpa o histórico de logs separadamente"""
    try:
        supabase.table("logs_auditoria").delete().neq("id", -1).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao limpar histórico de logs: {e}")
        return False

# ---------------------------------------------------------
# FUNÇÕES DA BASE DE ALUNOS
# ---------------------------------------------------------
def carregar_alunos():
    try:
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
            
            # Formatando a data de nascimento para DD/MM/YYYY
            if "Data Nasc." in df.columns:
                df["Data Nasc."] = pd.to_datetime(df["Data Nasc."], errors='coerce').dt.strftime('%d/%m/%Y')
        else:
            df = pd.DataFrame(columns=["Nome", "CPF", "Data Nasc.", "Escola Origem", "Turma", "Endereço", "Observações"])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar alunos: {e}")
        return pd.DataFrame(columns=["Nome", "CPF", "Data Nasc.", "Escola Origem", "Turma", "Endereço", "Observações"])

def salvar_aluno(nome, cpf, data_nasc, escola_origem, turma, endereco, observacoes, usuario_logado):
    try:
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
        
        # Registrar Log Independente
        detalhes = f"Aluno: {nome} | CPF: {cpf} | Escola: {escola_origem} | Turma: {turma}"
        registrar_log(usuario_logado, "Cadastro Individual", detalhes)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar aluno: {e}")
        return False

def salvar_alunos_em_lote(df_lote, usuario_logado):
    try:
        total_registros = len(df_lote)
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
        
        # Registrar Log Independente
        registrar_log(usuario_logado, "Importação em Lote", f"Importados {total_registros} alunos via planilha.")
        return True
    except Exception as e:
        st.error(f"Erro na importação em lote: {e}")
        return False

def limpar_tabela_alunos(usuario_logado, quantidade_deletada):
    try:
        # Exclui todos os registros do banco de dados Supabase
        supabase.table("alunos").delete().neq("id", -1).execute()
        
        # Registrar Log Independente sobre a exclusão da base
        registrar_log(usuario_logado, "Exclusão da Base de Alunos", f"A base de dados contendo {quantidade_deletada} aluno(s) foi zerada.")
        return True
    except Exception as e:
        st.error(f"Erro ao limpar banco de dados de alunos: {e}")
        return False

# ---------------------------------------------------------
# FUNÇÕES DE USUÁRIOS
# ---------------------------------------------------------
def carregar_usuarios():
    try:
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
    except Exception:
        pass
    return pd.DataFrame(columns=["Usuario", "Senha", "Nome", "Perfil"])

def salvar_usuario(usr, pwd, nome, perfil):
    try:
        dados = {
            "usuario": usr,
            "senha": pwd,
            "nome": nome,
            "perfil": perfil
        }
        supabase.table("usuarios").insert(dados).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar usuário no banco: {e}")
        return False

def atualizar_perfil_usuario(usr, novo_perfil):
    try:
        supabase.table("usuarios").update({"perfil": novo_perfil}).eq("usuario", usr).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar perfil do usuário: {e}")
        return False

def remover_usuario(usr):
    try:
        supabase.table("usuarios").delete().eq("usuario", usr).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao remover usuário: {e}")
        return False

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
    
    .custom-logo {
        max-height: 90px;
        max-width: 260px;
        object-fit: contain;
        display: block;
        margin: 0 auto 15px auto;
    }
    </style>
""", unsafe_allow_html=True)

# Lista de Escolas de Goiana
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

OPCOES_PERFIL = ["Usuário Comum", "Gestor / Visualizador", "Administrador"]

def gerar_planilha_modelo():
    buffer = io.BytesIO()
    df_modelo = pd.DataFrame({
        "Nome": ["Exemplo Nome Aluno"],
        "CPF": ["000.000.000-00"],
        "Data Nasc.": ["2015-01-01"],
        "Escola Origem": ["Adélia Carneiro Pedrosa"],
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
        # Exibição da Logo na Tela de Login
        if config_sys.get("logo_base64"):
            st.markdown(f'<img src="{config_sys["logo_base64"]}" class="custom-logo">', unsafe_allow_html=True)
        else:
            st.markdown("<h1 style='text-align: center; font-size: 50px; margin-bottom: 0;'>🏫</h1>", unsafe_allow_html=True)

        st.markdown(f"<h2 style='text-align: center;'>{config_sys['titulo_login']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #64748b;'>{config_sys['subtitulo_login']}</p>", unsafe_allow_html=True)
        
        with st.form("form_login"):
            usr_input = st.text_input("Usuário")
            pwd_input = st.text_input("Senha", type="password")
            btn_entrar = st.form_submit_button("🔒 Entrar no Sistema", use_container_width=True)
            
            if btn_entrar:
                df_usr = carregar_usuarios()
                if not df_usr.empty and "Usuario" in df_usr.columns and "Senha" in df_usr.columns:
                    match = df_usr[(df_usr["Usuario"] == usr_input) & (df_usr["Senha"] == pwd_input)]
                    if not match.empty:
                        st.session_state["usuario_logado"] = match.iloc[0].to_dict()
                        st.success("Login efetuado com sucesso!")
                        st.rerun()
                    else:
                        st.error("⚠️ Usuário ou senha incorretos.")
                elif usr_input == "admin" and pwd_input == "123":
                    st.session_state["usuario_logado"] = {
                        "Usuario": "admin",
                        "Nome": "Administrador",
                        "Perfil": "Administrador"
                    }
                    st.success("Login realizado com acesso master!")
                    st.rerun()
                else:
                    st.error("⚠️ Usuário ou senha incorretos.")

# ---------------------------------------------------------
# ÁREA LOGADA DO SISTEMA
# ---------------------------------------------------------
else:
    usr = st.session_state["usuario_logado"]
    
    col_head_logo, col_title, col_user = st.columns([1, 3.5, 1.2])
    
    with col_head_logo:
        if config_sys.get("logo_base64"):
            st.markdown(f'<img src="{config_sys["logo_base64"]}" style="max-height: 60px; max-width: 100%; object-fit: contain;">', unsafe_allow_html=True)
        else:
            st.markdown("<h1 style='font-size: 40px; margin: 0;'>🏫</h1>", unsafe_allow_html=True)

    with col_title:
        st.markdown(f"<h2 style='margin:0;'>{config_sys['titulo_interno']}</h2>", unsafe_allow_html=True)
        
    with col_user:
        st.write(f"👤 **{usr['Nome']}**")
        st.caption(f"Perfil: {usr['Perfil']}")
        if st.button("🚪 Sair", key="btn_logout"):
            st.session_state["usuario_logado"] = None
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Controle de navegação e abas conforme o perfil
    perfil = usr["Perfil"]
    
    if perfil == "Administrador":
        aba_cadastro, aba_admin, aba_gestao_usuarios = st.tabs([
            "📝 Cadastro de Alunos", 
            "📊 Dashboard Geral",
            "⚙️ Configurações & Usuários"
        ])
    elif perfil == "Gestor / Visualizador":
        aba_cadastro, aba_admin = st.tabs([
            "📝 Cadastro de Alunos", 
            "📊 Dashboard Geral"
        ])
        aba_gestao_usuarios = None
    else:  # Usuário Comum
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
                
                # DATA DE NASCIMENTO: Formato DD/MM/YYYY e Limite 1980 a 2026
                data_nasc = st.date_input(
                    "Data de Nascimento *",
                    value=date(2015, 1, 1),
                    min_value=date(1980, 1, 1),
                    max_value=date(2026, 12, 31),
                    format="DD/MM/YYYY"
                )
            with col2:
                escola_origem = st.selectbox("Escola de Origem *", options=ESCOLAS)
                turma = st.text_input("Série / Turma *", placeholder="Ex: 5º Ano A")
                endereco = st.text_input("Endereço Completo")

            observacoes = st.text_area("Observações")

            st.markdown("<br>", unsafe_allow_html=True)
            btn_salvar = st.form_submit_button("💾 Salvar Cadastro")
            
            if btn_salvar:
                if nome and cpf and escola_origem:
                    usuario_responsavel = f"{usr['Nome']} ({usr['Usuario']})"
                    if salvar_aluno(nome, cpf, str(data_nasc), escola_origem, turma, endereco, observacoes, usuario_responsavel):
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
                    usuario_responsavel = f"{usr['Nome']} ({usr['Usuario']})"
                    if salvar_alunos_em_lote(df_upload, usuario_responsavel):
                        st.balloons()
                        st.success(f"🎉 Todos os {len(df_upload)} alunos foram salvos no banco de dados Supabase!")
            except Exception as e:
                st.error(f"❌ Erro ao processar o arquivo: {e}")

    # ---------------------------------------------------------
    # ABA 2: DASHBOARD (ADMINISTRADOR E GESTOR/VISUALIZADOR)
    # ---------------------------------------------------------
    if aba_admin:
        with aba_admin:
            df = carregar_alunos()
            
            total_alunos = len(df)
            escolas_ativas = df["Escola Origem"].nunique() if not df.empty and "Escola Origem" in df.columns else 0
            
            if not df.empty and "Data Nasc." in df.columns:
                df['Data_dt'] = pd.to_datetime(df['Data Nasc.'], format='%d/%m/%Y', errors='coerce')
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
                        if pd.isna(idade): return 'Não informada'
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
            st.markdown("### 📋 Base de Dados Completa (Alunos)")
            
            cols_exibicao = [c for c in ["Nome", "CPF", "Data Nasc.", "Escola Origem", "Turma", "Endereço", "Observações"] if c in df.columns]
            st.dataframe(df[cols_exibicao] if not df.empty else df, use_container_width=True)
            
            # BOTÕES EXPORTAR E LIMPAR ALUNOS
            col_exp, col_limp, col_vazio = st.columns([1, 1, 2])
            
            with col_exp:
                if not df.empty:
                    csv = df[cols_exibicao].to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Exportar CSV dos Alunos",
                        data=csv,
                        file_name="base_alunos_supabase.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            # EXCLUSÃO DA BASE DE ALUNOS (Apenas para o Administrador)
            if perfil == "Administrador":
                with col_limp:
                    if not df.empty:
                        if st.checkbox("⚠️ Confirmar exclusão total dos ALUNOS"):
                            if st.button("🗑️ Limpar Base de Alunos", type="primary", use_container_width=True):
                                usuario_responsavel = f"{usr['Nome']} ({usr['Usuario']})"
                                if limpar_tabela_alunos(usuario_responsavel, len(df)):
                                    st.success("Base de dados de alunos limpa com sucesso! O histórico de logs foi mantido.")
                                    st.rerun()

            # ---------------------------------------------------------
            # AUDITORIA E HISTÓRICO DE LOGS (EXCLUSIVO PARA ADMINISTRADOR)
            # ---------------------------------------------------------
            if perfil == "Administrador":
                st.markdown("---")
                st.markdown("### 🛡️ Histórico e Logs de Auditoria (Sistema Independente)")
                st.caption("Esta tabela registra todas as ações de usuários (cadastros, importações e exclusões) e PERMANECE INTACTA mesmo quando a base de alunos é zerada.")
                
                df_logs = carregar_logs()
                st.dataframe(df_logs, use_container_width=True, hide_index=True)

                col_log_exp, col_log_limp, col_log_vazio = st.columns([1, 1, 2])
                
                with col_log_exp:
                    if not df_logs.empty:
                        csv_logs = df_logs.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Exportar Logs em CSV",
                            data=csv_logs,
                            file_name="logs_auditoria_sistema.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                with col_log_limp:
                    if not df_logs.empty:
                        if st.checkbox("⚠️ Confirmar exclusão dos LOGS"):
                            if st.button("🗑️ Limpar Histórico de Logs", use_container_width=True):
                                if limpar_tabela_logs():
                                    st.success("Histórico de logs zerado com sucesso!")
                                    st.rerun()

    # ---------------------------------------------------------
    # ABA 3: GESTÃO DE USUÁRIOS E CONFIGURAÇÕES (EXCLUSIVO PARA ADMINISTRADOR)
    # ---------------------------------------------------------
    if aba_gestao_usuarios and perfil == "Administrador":
        with aba_gestao_usuarios:
            st.subheader("🎨 Personalização da Marca & Títulos do Sistema")
            
            with st.form("form_configuracoes_marca"):
                col_cfg1, col_cfg2 = st.columns(2)
                
                with col_cfg1:
                    novo_tit_login = st.text_input("Título na Tela de Login", value=config_sys['titulo_login'])
                    novo_subtit_login = st.text_input("Subtítulo na Tela de Login", value=config_sys['subtitulo_login'])
                    novo_tit_interno = st.text_input("Título Interno (Área Logada)", value=config_sys['titulo_interno'])
                    
                with col_cfg2:
                    st.markdown("#### 🖼️ Logo do Sistema")
                    if config_sys.get("logo_base64"):
                        st.markdown("**Logo Atual:**")
                        st.markdown(f'<img src="{config_sys["logo_base64"]}" style="max-height: 80px;">', unsafe_allow_html=True)
                    
                    logo_upload = st.file_uploader("Enviar Nova Logo (PNG, JPG, SVG)", type=["png", "jpg", "jpeg", "svg"])
                    remover_logo = st.checkbox("❌ Remover Logo e Usar Ícone Padrão")

                btn_salvar_config = st.form_submit_button("💾 Salvar Personalizações da Marca")
                
                if btn_salvar_config:
                    logo_base64_final = config_sys.get("logo_base64")
                    atualizou_logo = False
                    
                    if remover_logo:
                        logo_base64_final = None
                        atualizou_logo = True
                    elif logo_upload is not None:
                        bytes_data = logo_upload.getvalue()
                        encoded = base64.b64encode(bytes_data).decode('utf-8')
                        mime_type = logo_upload.type
                        logo_base64_final = f"data:{mime_type};base64,{encoded}"
                        atualizou_logo = True

                    if salvar_configuracoes(novo_tit_login, novo_subtit_login, novo_tit_interno, logo_base64_final, atualizou_logo):
                        st.success("✅ Configurações visuais e títulos atualizados com sucesso!")
                        st.rerun()

            st.markdown("---")
            st.subheader("👥 Controle de Acessos e Perfis de Usuários")
            
            df_usrs_atual = carregar_usuarios()
            
            col_novo, col_alterar, col_lista = st.columns([1, 1, 1.2], gap="large")
            
            # 1. CRIAR NOVO USUÁRIO
            with col_novo:
                st.markdown("#### ➕ Novo Usuário")
                with st.form("form_novo_usuario", clear_on_submit=True):
                    novo_nome = st.text_input("Nome Completo *")
                    novo_usr = st.text_input("Login *")
                    nova_senha = st.text_input("Senha *", type="password")
                    novo_perfil = st.selectbox("Perfil *", OPCOES_PERFIL)
                    
                    btn_cad_usr = st.form_submit_button("➕ Criar Usuário")
                    if btn_cad_usr:
                        if novo_nome and novo_usr and nova_senha:
                            if not df_usrs_atual.empty and novo_usr in df_usrs_atual["Usuario"].values:
                                st.error("⚠️ Este login já existe.")
                            else:
                                if salvar_usuario(novo_usr, nova_senha, novo_nome, novo_perfil):
                                    st.success(f"✅ Usuário **{novo_usr}** criado!")
                                    st.rerun()
                        else:
                            st.error("⚠️ Preencha todos os campos.")

            # 2. EDITAR PERFIL DO USUÁRIO
            with col_alterar:
                st.markdown("#### 🔄 Alterar Perfil")
                if not df_usrs_atual.empty:
                    usr_edit = st.selectbox("Selecione o Usuário", df_usrs_atual["Usuario"].tolist(), key="select_edit_usr")
                    
                    # Pega perfil atual
                    perfil_atual = df_usrs_atual[df_usrs_atual["Usuario"] == usr_edit]["Perfil"].values[0]
                    st.info(f"Perfil Atual: **{perfil_atual}**")
                    
                    novo_perfil_sel = st.selectbox("Novo Perfil", OPCOES_PERFIL, key="select_novo_perfil")
                    
                    if st.button("✏️ Atualizar Perfil", use_container_width=True):
                        if atualizar_perfil_usuario(usr_edit, novo_perfil_sel):
                            st.success(f"Perfil de **{usr_edit}** alterado para **{novo_perfil_sel}**!")
                            st.rerun()
                else:
                    st.caption("Nenhum usuário disponível para edição.")

            # 3. LISTAR E REMOVER USUÁRIOS
            with col_lista:
                st.markdown("#### 📋 Usuários Ativos")
                if not df_usrs_atual.empty:
                    st.dataframe(df_usrs_atual[["Nome", "Usuario", "Perfil"]], use_container_width=True, hide_index=True)
                    
                    st.markdown("---")
                    st.markdown("#### 🗑️ Remover Usuário")
                    usuarios_removiveis = [u for u in df_usrs_atual["Usuario"].tolist() if u != "admin"]
                    if usuarios_removiveis:
                        usr_remover = st.selectbox("Selecione para remover", usuarios_removiveis, key="select_rem_usr")
                        if st.button("❌ Confirmar Remoção", use_container_width=True):
                            if remover_usuario(usr_remover):
                                st.success(f"Usuário **{usr_remover}** removido!")
                                st.rerun()
                    else:
                        st.caption("Sem usuários secundários para remoção.")
                else:
                    st.info("Nenhum usuário cadastrado no banco.")
