import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# 1. Configuração da página
st.set_page_config(page_title="Sistema de Gestão Escolar", layout="wide")

# 2. Conexão com o Supabase
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["SUPABASE_URL"]
    key = st.secrets["supabase"]["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# 3. Gerenciamento de Sessão (Login)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# --- TELA DE LOGIN ---
if not st.session_state.logged_in:
    st.title("🔐 Login - Gestão Escolar")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        usuario_input = st.text_input("Usuário")
        senha_input = st.text_input("Senha", type="password")
        
        if st.button("Entrar", use_container_width=True):
            response = supabase.table("usuarios").select("*").eq("usuario", usuario_input).eq("senha", senha_input).execute()
            if response.data:
                st.session_state.logged_in = True
                st.session_state.user = response.data[0]
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

# --- SISTEMA APÓS LOGIN ---
else:
    user = st.session_state.user
    st.sidebar.title(f"Bem-vindo, {user['nome']}")
    st.sidebar.caption(f"Perfil: {user['perfil']}")
    
    if st.sidebar.button("Sair"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    menu = st.sidebar.radio("Navegação", ["Dashboard", "Cadastrar Aluno", "Importar Planilha", "Listar Alunos"])

    # --- DASHBOARD ---
    if menu == "Dashboard":
        st.title("📊 Dashboard")
        res = supabase.table("alunos").select("*").execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            col1, col2 = st.columns(2)
            col1.metric("Total de Alunos", len(df))
            col2.metric("Escolas Cadastradas", df["escola_origem"].nunique() if "escola_origem" in df else 0)

            if "escola_origem" in df and not df["escola_origem"].isna().all():
                fig = px.bar(df["escola_origem"].value_counts().reset_index(), 
                             x="escola_origem", y="count", 
                             title="Alunos por Escola de Origem",
                             labels={"escola_origem": "Escola", "count": "Quantidade"})
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum aluno cadastrado até o momento.")

    # --- CADASTRO DE ALUNOS (INDIVIDUAL) ---
    elif menu == "Cadastrar Aluno":
        st.title("📝 Cadastrar Novo Aluno (Individual)")
        
        with st.form("form_aluno"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome Completo *")
                cpf = st.text_input("CPF")
                data_nasc = st.text_input("Data de Nascimento (DD/MM/AAAA)")
            with col2:
                escola = st.text_input("Escola de Origem")
                turma = st.text_input("Turma")
                endereco = st.text_input("Endereço Completo")
                
            obs = st.text_area("Observações")
            
            submitted = st.form_submit_button("Salvar Aluno")
            if submitted:
                if not nome:
                    st.error("O campo Nome é obrigatório.")
                else:
                    dados = {
                        "nome": nome,
                        "cpf": cpf,
                        "data_nasc": data_nasc,
                        "escola_origem": escola,
                        "turma": turma,
                        "endereco": endereco,
                        "observacoes": obs
                    }
                    supabase.table("alunos").insert(dados).execute()
                    st.success(f"Aluno {nome} cadastrado com sucesso!")

    # --- IMPORTAR PLANILHA (EM LOTE) ---
    elif menu == "Importar Planilha":
        st.title("📂 Importação de Alunos em Lote")
        st.info("Envie um arquivo **.xlsx** ou **.csv** com as seguintes colunas: `nome`, `cpf`, `data_nasc`, `escola_origem`, `turma`, `endereco`, `observacoes`")

        arquivo = st.file_uploader("Selecione a planilha", type=["xlsx", "csv"])

        if arquivo is not None:
            try:
                if arquivo.name.endswith(".csv"):
                    df_import = pd.read_csv(arquivo)
                else:
                    df_import = pd.read_excel(arquivo)

                # Tratar valores vazios
                df_import = df_import.fillna("")

                st.subheader("Pré-visualização dos dados:")
                st.dataframe(df_import, use_container_width=True)

                if st.button("Confirmar Importação para o Supabase"):
                    registros = df_import.to_dict(orient="records")
                    supabase.table("alunos").insert(registros).execute()
                    st.success(f"Sucesso! {len(registros)} alunos foram importados para o banco de dados.")
            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {e}")

    # --- LISTAGEM E EDIÇÃO ---
    elif menu == "Listar Alunos":
        st.title("📋 Lista de Alunos Cadastrados")
        res = supabase.table("alunos").select("*").execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            st.dataframe(df, use_container_width=True)
            
            if user["perfil"] == "Administrador":
                st.subheader("🗑️ Excluir Registro")
                aluno_id = st.selectbox("Selecione o ID do aluno para excluir:", df["id"])
                if st.button("Excluir Aluno"):
                    supabase.table("alunos").delete().eq("id", aluno_id).execute()
                    st.warning("Aluno removido!")
                    st.rerun()
        else:
            st.info("Nenhum registro encontrado.")
