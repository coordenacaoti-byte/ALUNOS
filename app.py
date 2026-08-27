import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import io
import base64
from supabase import create_client, Client

# Importações do ReportLab para geração de PDF
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ---------------------------------------------------------
# FUSO HORÁRIO LOCAL (UTC-3 / PERNAMBUCO)
# ---------------------------------------------------------
FUSO_RECIFE = ZoneInfo("America/Recife")

def obter_data_hora_atual() -> str:
    """Retorna a data e hora atual formatada no fuso horário local de Pernambuco."""
    return datetime.now(FUSO_RECIFE).strftime("%d/%m/%Y %H:%M:%S")

def obter_iso_atual() -> str:
    """Retorna o timestamp ISO 8601 com offset para gravação precisa no Supabase."""
    return datetime.now(FUSO_RECIFE).isoformat()

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
# FUNÇÕES DE CONFIGURAÇÕES DE PERSONALIZAÇÃO (TÍTULOS E LOGO)
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
# FUNÇÃO DE LOGS DE AUDITORIA (COM CORREÇÃO DE HORÁRIO)
# ---------------------------------------------------------
def registrar_log(usuario: str, acao: str, detalhes: str = ""):
    """Grava logs em uma tabela independente 'logs_auditoria' com timezone local"""
    try:
        dados_log = {
            "usuario": usuario,
            "acao": acao,
            "detalhes": detalhes,
            "data_hora": obter_iso_atual()
        }
        supabase.table("logs_auditoria").insert(dados_log).execute()
    except Exception as e:
        st.error(f"Erro ao registrar log de auditoria: {e}")

def carregar_logs(data_inicio=None, data_fim=None):
    """Carrega o histórico de logs ajustando o fuso horário para UTC-3"""
    try:
        query = supabase.table("logs_auditoria").select("*")
        
        if data_inicio:
            iso_inicio = f"{data_inicio}T00:00:00-03:00"
            query = query.gte("data_hora", iso_inicio)
        if data_fim:
            iso_fim = f"{data_fim}T23:59:59-03:00"
            query = query.lte("data_hora", iso_fim)
            
        response = query.order("data_hora", desc=True).execute()
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
                df_logs["Data/Hora"] = (
                    pd.to_datetime(df_logs["Data/Hora"], errors='coerce')
                    .dt.tz_convert('America/Recife')
                    .dt.strftime('%d/%m/%Y %H:%M:%S')
                )
            cols_ordem = [c for c in ["Data/Hora", "Usuário Responsável", "Ação / Evento", "Detalhes do Registro"] if c in df_logs.columns]
            return df_logs[cols_ordem]
        else:
            return pd.DataFrame(columns=["Data/Hora", "Usuário Responsável", "Ação / Evento", "Detalhes do Registro"])
    except Exception:
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
# GERADOR DE PDF PARA LOGS DE AUDITORIA
# ---------------------------------------------------------
def gerar_pdf_logs_bytes(df_logs, data_ini, data_fim, usuario_solicitante):
    """Gera um documento PDF em formato Paisagem contendo o relatório de logs"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor("#4F46E5"),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15
    )
    
    style_cell = ParagraphStyle('CellText', parent=styles['Normal'], fontSize=8, fontName='Helvetica', leading=10)
    style_header = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=colors.white)

    elements.append(Paragraph(f"{config_sys['titulo_interno']} - Relatório de Auditoria", title_style))
    
    periodo_str = f"<b>Período:</b> {data_ini.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}"
    emissao_str = f"<b>Emissão:</b> {obter_data_hora_atual()} por {usuario_solicitante}"
    elements.append(Paragraph(f"{periodo_str} | {emissao_str}", subtitle_style))
    
    data = [["Data/Hora", "Usuário Responsável", "Ação / Evento", "Detalhes do Registro"]]
    data[0] = [Paragraph(col, style_header) for col in data[0]]

    for _, row in df_logs.iterrows():
        data.append([
            Paragraph(str(row.get("Data/Hora", "")), style_cell),
            Paragraph(str(row.get("Usuário Responsável", "")), style_cell),
            Paragraph(str(row.get("Ação / Evento", "")), style_cell),
            Paragraph(str(row.get("Detalhes do Registro", "")), style_cell),
        ])

    col_widths = [110, 140, 150, 332]
    
    tabela = Table(data, colWidths=col_widths, repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    
    elements.append(tabela)
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ---------------------------------------------------------
# FUNÇÕES DA BASE DE ALUNOS
# ---------------------------------------------------------
def carregar_alunos():
    """Carrega as colunas da tabela e faz a conversão flexível da data de nascimento."""
    try:
        response = supabase.table("alunos").select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            renames = {
                "nome": "Nome",
                "cpf": "CPF",
                "data_nasc": "Data Nasc.",
                "tipo_busca": "Tipo de Busca",
                "escola_origem": "Escola Origem",
                "turma": "Turma",
                "observacoes": "Observações"
            }
            if "endereco" in df.columns:
                renames["endereco"] = "Endereço"
                
            df = df.rename(columns=renames)
            
            # Conversão robusta aceitando múltiplos formatos de data
            if "Data Nasc." in df.columns:
                data_parsed = pd.to_datetime(df["Data Nasc."], format='mixed', errors='coerce')
                df["Data Nasc."] = data_parsed.dt.strftime('%d/%m/%Y').fillna('-')

            cols_desejadas = ["Nome", "CPF", "Data Nasc.", "Tipo de Busca", "Escola Origem", "Turma", "Endereço", "Observações"]
            cols_finais = [c for c in cols_desejadas if c in df.columns]
            return df[cols_finais]
        else:
            return pd.DataFrame(columns=["Nome", "CPF", "Data Nasc.", "Tipo de Busca", "Escola Origem", "Turma", "Endereço", "Observações"])
    except Exception as e:
        st.error(f"Erro ao carregar alunos: {e}")
        return pd.DataFrame(columns=["Nome", "CPF", "Data Nasc.", "Tipo de Busca", "Escola Origem", "Turma", "Endereço", "Observações"])

def salvar_aluno(nome, cpf, data_nasc, tipo_busca, escola_origem, turma, endereco, observacoes, usuario_logado):
    try:
        dados = {
            "nome": nome,
            "cpf": cpf,
            "data_nasc": str(data_nasc),
            "tipo_busca": tipo_busca,
            "escola_origem": escola_origem,
            "turma": turma,
            "endereco": endereco,
            "observacoes": observacoes,
            "created_at": obter_iso_atual()
        }
        supabase.table("alunos").insert(dados).execute()
        
        detalhes = f"Aluno: {nome} | CPF: {cpf} | Tipo Busca: {tipo_busca} | Escola: {escola_origem} | Turma: {turma}"
        registrar_log(usuario_logado, "Cadastro Individual", detalhes)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar aluno: {e}")
        return False

def salvar_alunos_em_lote(df_lote, usuario_logado):
    try:
        total_registros = len(df_lote)
        
        mapa_colunas = {
            "Nome": "nome",
            "CPF": "cpf",
            "Data Nasc.": "data_nasc",
            "Tipo de Busca": "tipo_busca",
            "Escola Origem": "escola_origem",
            "Turma": "turma",
            "Endereço": "endereco",
            "Endereco": "endereco",
            "Observações": "observacoes",
            "Observacoes": "observacoes"
        }
        
        df_lote = df_lote.rename(columns=mapa_colunas)
        
        colunas_validas = ["nome", "cpf", "data_nasc", "tipo_busca", "escola_origem", "turma", "endereco", "observacoes"]
        cols_presentes = [c for c in colunas_validas if c in df_lote.columns]
        df_lote = df_lote[cols_presentes]

        if "data_nasc" in df_lote.columns:
            df_lote["data_nasc"] = pd.to_datetime(df_lote["data_nasc"], errors='coerce').dt.strftime('%Y-%m-%d')
            
        df_lote["created_at"] = obter_iso_atual()
        registros = df_lote.fillna("").to_dict(orient="records")
        supabase.table("alunos").insert(registros).execute()
        
        registrar_log(usuario_logado, "Importação em Lote", f"Importados {total_registros} alunos via planilha.")
        return True
    except Exception as e:
        st.error(f"Erro na importação em lote: {e}")
        return False

def limpar_tabela_alunos(usuario_logado, quantidade_deletada):
    try:
        supabase.table("alunos").delete().neq("id", -1).execute()
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

def salvar_usuarios_em_lote(df_lote_usr, usuario_logado):
    try:
        renames = {
            "Usuario": "usuario",
            "Senha": "senha",
            "Nome": "nome",
            "Perfil": "perfil"
        }
        df_lote_usr = df_lote_usr.rename(columns=renames)
        df_lote_usr["perfil"] = df_lote_usr["perfil"].apply(
            lambda p: p if p in OPCOES_PERFIL else "Usuário Comum"
        )
        
        registros = df_lote_usr[["usuario", "senha", "nome", "perfil"]].fillna("").to_dict(orient="records")
        supabase.table("usuarios").insert(registros).execute()
        
        registrar_log(usuario_logado, "Importação de Usuários em Lote", f"Importados {len(registros)} usuários via planilha.")
        return True
    except Exception as e:
        st.error(f"Erro ao salvar usuários em lote: {e}")
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

    /* Estilo do Rodapé */
    .footer {
        margin-top: 50px;
        padding: 20px;
        border-top: 1px solid #e2e8f0;
        text-align: center;
        font-size: 0.85rem;
        color: #64748b;
        line-height: 1.5;
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

OPCOES_BUSCA = ["Busca Ativa", "Sistema Presença (ENI)"]
OPCOES_PERFIL = ["Usuário Comum", "Gestor / Visualizador", "Administrador"]

# Modelos de Planilhas
def gerar_planilha_modelo():
    buffer = io.BytesIO()
    df_modelo = pd.DataFrame({
        "Nome": ["Exemplo Nome Aluno"],
        "CPF": ["000.000.000-00"],
        "Data Nasc.": ["2015-01-01"],
        "Tipo de Busca": ["Busca Ativa"],
        "Escola Origem": ["Adélia Carneiro Pedrosa"],
        "Turma": ["1º Ano A"],
        "Endereço": ["Rua Exemplo, Nº 100, Bairro Centenário"],
        "Observações": ["Sem observações"]
    })
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_modelo.to_excel(writer, index=False, sheet_name='Modelo_Importacao')
    return buffer.getvalue()

def gerar_planilha_modelo_usuarios():
    buffer = io.BytesIO()
    df_modelo_usr = pd.DataFrame({
        "Nome": ["João da Silva", "Maria Oliveira"],
        "Usuario": ["joao.silva", "maria.gestora"],
        "Senha": ["senha123", "senha456"],
        "Perfil": ["Usuário Comum", "Gestor / Visualizador"]
    })
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_modelo_usr.to_excel(writer, index=False, sheet_name='Modelo_Usuarios')
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
                
                data_nasc = st.date_input(
                    "Data de Nascimento *",
                    value=date(2015, 1, 1),
                    min_value=date(1980, 1, 1),
                    max_value=date(2026, 12, 31),
                    format="DD/MM/YYYY"
                )
                
                tipo_busca = st.selectbox("Tipo de Busca *", options=OPCOES_BUSCA)

            with col2:
                escola_origem = st.selectbox("Escola de Origem *", options=ESCOLAS)
                turma = st.text_input("Série / Turma *", placeholder="Ex: 5º Ano A")
                endereco = st.text_input("Endereço Completo *", placeholder="Rua, Número, Bairro")

            observacoes = st.text_area("Observações")

            st.markdown("<br>", unsafe_allow_html=True)
            btn_salvar = st.form_submit_button("💾 Salvar Cadastro")
            
            if btn_salvar:
                if nome and cpf and escola_origem and tipo_busca and endereco.strip():
                    usuario_responsavel = f"{usr['Nome']} ({usr['Usuario']})"
                    if salvar_aluno(nome, cpf, str(data_nasc), tipo_busca, escola_origem, turma, endereco, observacoes, usuario_responsavel):
                        st.success(f"✅ Aluno(a) **{nome}** salvo no Supabase com sucesso!")
                else:
                    st.error("⚠️ Preencha todos os campos obrigatórios (*), incluindo o **Endereço Completo**.")

        st.markdown("---")

        # IMPORTAÇÃO EM LOTE DE ALUNOS
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
                    st.dataframe(df_upload, use_container_width=True, height=300)
                
                if st.button("🚀 Confirmar e Integrar Registros no Supabase", use_container_width=True):
                    usuario_responsavel = f"{usr['Nome']} ({usr['Usuario']})"
                    if salvar_alunos_em_lote(df_upload, usuario_responsavel):
                        st.balloons()
                        st.success(f"🎉 Todos os {len(df_upload)} alunos foram salvos no banco de dados Supabase!")
            except Exception as e:
                st.error(f"❌ Erro ao processar o arquivo: {e}")

    # ---------------------------------------------------------
    # ABA 2: DASHBOARD E LOGS (ADMINISTRADOR E GESTOR/VISUALIZADOR)
    # ---------------------------------------------------------
    if aba_admin:
        with aba_admin:
            df = carregar_alunos()
            
            total_alunos = len(df)
            escolas_ativas = df["Escola Origem"].nunique() if not df.empty and "Escola Origem" in df.columns else 0
            
            # Cálculo de idade feito em DataFrame auxiliar para evitar alteração da exibição da tabela original
            if not df.empty and "Data Nasc." in df.columns:
                df_calc = df.copy()
                df_calc['Data_dt'] = pd.to_datetime(df_calc['Data Nasc.'], format='%d/%m/%Y', errors='coerce')
                ano_atual = datetime.now(FUSO_RECIFE).year
                df_calc['Idade'] = ano_atual - df_calc['Data_dt'].dt.year
                media_idade = round(df_calc['Idade'].mean(), 1) if not df_calc['Idade'].isna().all() else 0.0
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

            st.markdown("<br>", unsafe_allow_html=True)

            # GRÁFICOS
            if not df.empty:
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    fig_escola = px.bar(
                        df['Escola Origem'].value_counts().reset_index(),
                        x='count', y='Escola Origem', orientation='h',
                        title="Alunos por Escola de Origem",
                        labels={'count': 'Quantidade', 'Escola Origem': 'Escola'},
                        color_discrete_sequence=['#4f46e5']
                    )
                    fig_escola.update_layout(height=350, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig_escola, use_container_width=True)

                with col_g2:
                    fig_busca = px.pie(
                        df['Tipo de Busca'].value_counts().reset_index(),
                        names='Tipo de Busca', values='count',
                        title="Distribuição por Tipo de Busca",
                        color_discrete_sequence=['#4f46e5', '#06b6d4']
                    )
                    fig_busca.update_layout(height=350, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig_busca, use_container_width=True)
            
            st.markdown("---")
            st.subheader("📊 Tabela Completa de Alunos Cadastrados")
            st.dataframe(df, use_container_width=True)

            # SESSÃO DE LOGS E AUDITORIA
            st.markdown("---")
            st.subheader("🛡️ Histórico e Logs de Auditoria do Sistema")

            c_data1, c_data2 = st.columns(2)
            hoje = datetime.now(FUSO_RECIFE).date()
            inicio_mes = hoje.replace(day=1)

            with c_data1:
                dt_ini = st.date_input("Data Inicial do Filtro", value=inicio_mes, format="DD/MM/YYYY")
            with c_data2:
                dt_fim = st.date_input("Data Final do Filtro", value=hoje, format="DD/MM/YYYY")

            df_logs = carregar_logs(data_inicio=dt_ini, data_fim=dt_fim)
            st.dataframe(df_logs, use_container_width=True)

            c_btn1, c_btn2, c_btn3 = st.columns([1, 1, 1])
            with c_btn1:
                if not df_logs.empty:
                    pdf_bytes = gerar_pdf_logs_bytes(df_logs, dt_ini, dt_fim, f"{usr['Nome']} ({usr['Usuario']})")
                    st.download_button(
                        label="📄 Baixar Relatório em PDF",
                        data=pdf_bytes,
                        file_name=f"relatorio_auditoria_{dt_ini}_{dt_fim}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            with c_btn2:
                if not df_logs.empty:
                    csv_bytes = df_logs.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Exportar Logs em CSV",
                        data=csv_bytes,
                        file_name=f"logs_auditoria_{dt_ini}_{dt_fim}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            with c_btn3:
                if perfil == "Administrador":
                    confirmar_limpeza = st.checkbox("⚠️ Confirmar exclusão dos LOGS")
                    if st.button("🗑️ Limpar Logs", use_container_width=True, disabled=not confirmar_limpeza):
                        if limpar_tabela_logs():
                            st.success("Histórico de logs limpo com sucesso!")
                            st.rerun()

    # ---------------------------------------------------------
    # ABA 3: GESTÃO DE USUÁRIOS E CONFIGURAÇÕES (APENAS ADMINISTRADOR)
    # ---------------------------------------------------------
    if aba_gestao_usuarios:
        with aba_gestao_usuarios:
            st.subheader("⚙️ Personalização do Sistema")
            with st.form("form_config_visuais"):
                c_conf1, c_conf2 = st.columns(2)
                with c_conf1:
                    tit_login = st.text_input("Título da Tela de Login", value=config_sys["titulo_login"])
                    sub_login = st.text_input("Subtítulo da Tela de Login", value=config_sys["subtitulo_login"])
                with c_conf2:
                    tit_interno = st.text_input("Título Interno (Cabeçalho)", value=config_sys["titulo_interno"])
                    logo_file = st.file_uploader("Upload da Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])

                btn_salvar_config = st.form_submit_button("💾 Salvar Personalização")
                if btn_salvar_config:
                    b64_str = config_sys.get("logo_base64")
                    alt_logo = False
                    if logo_file is not None:
                        encoded = base64.b64encode(logo_file.read()).decode('utf-8')
                        b64_str = f"data:{logo_file.type};base64,{encoded}"
                        alt_logo = True

                    if salvar_configuracoes(tit_login, sub_login, tit_interno, b64_str, alt_logo):
                        st.success("Configurações atualizadas com sucesso!")
                        st.rerun()

            st.markdown("---")
            st.subheader("👥 Gestão de Usuários")

            df_usuarios = carregar_usuarios()
            st.dataframe(df_usuarios, use_container_width=True)

            with st.expander("➕ Cadastrar Novo Usuário"):
                with st.form("form_novo_usuario", clear_on_submit=True):
                    c_u1, c_u2 = st.columns(2)
                    with c_u1:
                        novo_nome = st.text_input("Nome Completo")
                        novo_usr = st.text_input("Nome de Usuário (Login)")
                    with c_u2:
                        nova_senha = st.text_input("Senha", type="password")
                        novo_perfil = st.selectbox("Perfil de Acesso", options=OPCOES_PERFIL)

                    if st.form_submit_button("💾 Cadastrar Usuário"):
                        if novo_nome and novo_usr and nova_senha:
                            if salvar_usuario(novo_usr, nova_senha, novo_nome, novo_perfil):
                                registrar_log(f"{usr['Nome']} ({usr['Usuario']})", "Cadastro de Usuário", f"Criou o usuário {novo_usr} ({novo_perfil})")
                                st.success(f"Usuário {novo_usr} criado!")
                                st.rerun()
                        else:
                            st.error("Preencha todos os campos obrigatórios.")

            with st.expander("📥 Importar Usuários em Lote"):
                st.download_button(
                    label="📄 Baixar Modelo de Usuários (.xlsx)",
                    data=gerar_planilha_modelo_usuarios(),
                    file_name="modelo_usuarios.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                file_usr = st.file_uploader("Enviar Planilha de Usuários", type=["xlsx", "csv"], key="upload_usr")
                if file_usr:
                    try:
                        df_u_up = pd.read_csv(file_usr) if file_usr.name.endswith('.csv') else pd.read_excel(file_usr)
                        st.dataframe(df_u_up, use_container_width=True)
                        if st.button("🚀 Confirmar Importação de Usuários"):
                            if salvar_usuarios_em_lote(df_u_up, f"{usr['Nome']} ({usr['Usuario']})"):
                                st.success("Usuários importados com sucesso!")
                                st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao processar arquivo: {e}")

            with st.expander("🗑️ Remover ou Editar Usuário"):
                if not df_usuarios.empty:
                    lista_usrs = df_usuarios["Usuario"].tolist()
                    usr_selecionado = st.selectbox("Selecione o Usuário", options=lista_usrs)
                    
                    c_ed1, c_ed2 = st.columns(2)
                    with c_ed1:
                        novo_p_edit = st.selectbox("Novo Perfil", options=OPCOES_PERFIL, key="edit_perfil")
                        if st.button("✏️ Atualizar Perfil"):
                            if atualizar_perfil_usuario(usr_selecionado, novo_p_edit):
                                registrar_log(f"{usr['Nome']} ({usr['Usuario']})", "Alteração de Perfil", f"Alterou perfil de {usr_selecionado} para {novo_p_edit}")
                                st.success("Perfil atualizado!")
                                st.rerun()
                    with c_ed2:
                        if st.button("❌ Excluir Usuário", type="primary"):
                            if remover_usuario(usr_selecionado):
                                registrar_log(f"{usr['Nome']} ({usr['Usuario']})", "Exclusão de Usuário", f"Removeu o usuário {usr_selecionado}")
                                st.success("Usuário removido!")
                                st.rerun()

            st.markdown("---")
            st.subheader("🧹 Limpeza do Banco de Dados")
            with st.expander("⚠️ Zerar Base de Alunos"):
                st.warning("Esta ação apaga permanentemente todos os cadastros de alunos.")
                confirmar_del_alunos = st.checkbox("Estou ciente de que os dados serão deletados.")
                if st.button("🗑️ Deletar Todos os Alunos", disabled=not confirmar_del_alunos):
                    df_atual = carregar_alunos()
                    qtd = len(df_atual)
                    if limpar_tabela_alunos(f"{usr['Nome']} ({usr['Usuario']})", qtd):
                        st.success("Base de alunos zerada com sucesso!")
                        st.rerun()

# ---------------------------------------------------------
# RODAPÉ INSTITUCIONAL
# ---------------------------------------------------------
st.markdown("""
    <div class="footer">
        © 2026 Secretaria de Educação e Inovação Pedagógica de Goiana - PE<br>
        <strong>Desenvolvimento:</strong> Coordenação de Tecnologia<br>
        Todos os direitos reservados.
    </div>
""", unsafe_allow_html=True)
