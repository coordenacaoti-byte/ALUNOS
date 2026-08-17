import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Sistema de Gestão Escolar",
    page_icon="🏫",
    layout="wide"
)

# Estilização CSS avançada (Cores escuras, bordas e destaque)
st.markdown("""
    <style>
    /* Fundo geral da página */
    .stApp {
        background-color: #0f172a !important;
        color: #f8fafc !important;
    }
    
    /* Textos, Títulos e Labels */
    h1, h2, h3, h4, label, .stMarkdown, p {
        color: #f8fafc !important;
    }

    /* Estilo dos Containers/Forms */
    [data-testid="stForm"], div[data-testid="stVerticalBlock"] > div[style*="background-color"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }

    /* Estilo das Abas */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-radius: 6px;
    }

    /* Cards do Dashboard (Metrics) */
    div[data-testid="stMetric"] {
        background-color: #1e293b !important;
        border-left: 5px solid #2563eb !important;
        padding: 15px !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Botões */
    .stButton>button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
    }
    .stButton>button:hover {
        background-color: #1d4ed8 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Banco de dados temporário
if "alunos_db" not in st.session_state:
    st.session_state["alunos_db"] = pd.DataFrame([
        {"Nome": "Ana Silva", "CPF": "111.222.333-00", "Data Nasc.": "2015-05-10", "Escola Origem": "Adélia Carneiro Pedrosa", "Turma": "5º Ano A", "Observações": "Regular"},
        {"Nome": "Bruno Souza", "CPF": "222.333.444-11", "Data Nasc.": "2014-08-20", "Escola Origem": "Diogo Dias", "Turma": "6º Ano B", "Observações": ""},
        {"Nome": "Carla Santos", "CPF": "333.444.555-22", "Data Nasc.": "2016-02-15", "Escola Origem": "Adélia Carneiro Pedrosa", "Turma": "4º Ano A", "Observações": ""}
    ])

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

st.title("🏫 Sistema de Gestão Escolar & Transferências")

aba_cadastro, aba_importacao, aba_admin = st.tabs([
    "📝 Novo Cadastro", 
    "📥 Importação em Lote",
    "📊 Área do Administrador (Dashboard)"
])

# ---------------------------------------------------------
# ABA 1: NOVO CADASTRO
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
            observacoes = st.text_area("Observações")

        btn_salvar = st.form_submit_button("💾 Salvar Cadastro")
        
        if btn_salvar:
            if nome and cpf and escola_origem:
                novo_aluno = pd.DataFrame([{
                    "Nome": nome, "CPF": cpf, "Data Nasc.": str(data_nasc),
                    "Escola Origem": escola_origem, "Turma": turma, "Observações": observacoes
                }])
                st.session_state["alunos_db"] = pd.concat([st.session_state["alunos_db"], novo_aluno], ignore_index=True)
                st.success(f"✅ Aluno(a) **{nome}** cadastrado(a) com sucesso!")
            else:
                st.error("⚠️ Preencha todos os campos obrigatórios (*).")

# ---------------------------------------------------------
# ABA 2: IMPORTAÇÃO EM LOTE
# ---------------------------------------------------------
with aba_importacao:
    st.subheader("📥 Importação de Dados Quinzenal")
    arquivo_enviado = st.file_uploader("Selecione o arquivo da planilha (.xlsx ou .csv)", type=["xlsx", "csv"])
    
    if arquivo_enviado is not None:
        try:
            df = pd.read_csv(arquivo_enviado) if arquivo_enviado.name.endswith('.csv') else pd.read_excel(arquivo_enviado)
            st.success("✅ Arquivo carregado com sucesso!")
            st.dataframe(df, use_container_width=True)
            
            if st.button("🚀 Processar e Salvar Registros"):
                st.session_state["alunos_db"] = pd.concat([st.session_state["alunos_db"], df], ignore_index=True)
                st.balloons()
                st.success(f"Total de {len(df)} registros integrados ao banco de dados!")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

# ---------------------------------------------------------
# ABA 3: DASHBOARD DO ADMINISTRADOR
# ---------------------------------------------------------
with aba_admin:
    st.subheader("🔒 Painel de Controle e Métricas")
    senha_digitada = st.text_input("Digite a senha do administrador:", type="password")
    
    # Senha padrão: admin123
    if senha_digitada == "admin123":
        st.success("🔓 Acesso liberado!")
        
        df_total = st.session_state["alunos_db"]
        
        # 1. CARDS DE MÉTRICAS
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total de Alunos", len(df_total))
        col_m2.metric("Escolas Registradas", df_total["Escola Origem"].nunique())
        col_m3.metric("Turmas Atendidas", df_total["Turma"].nunique())
        
        st.divider()
        
        # 2. DASHBOARD GRÁFICO
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.write("### 🏫 Alunos por Escola")
            if not df_total.empty:
                st.bar_chart(df_total["Escola Origem"].value_counts())
                
        with col_g2:
            st.write("### 📚 Distribuição por Turma")
            if not df_total.empty:
                st.bar_chart(df_total["Turma"].value_counts())
                
        st.divider()
        
        # 3. TABELA DE DADOS
        st.write("### 📋 Base de Dados Completa")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_escola = st.selectbox("Filtrar por Escola", options=["Todas"] + ESCOLAS)
        with col_f2:
            busca_texto = st.text_input("Buscar por Nome ou CPF")
            
        df_exibir = df_total.copy()
        if filtro_escola != "Todas":
            df_exibir = df_exibir[df_exibir["Escola Origem"] == filtro_escola]
        if busca_texto:
            df_exibir = df_exibir[
                df_exibir["Nome"].astype(str).str.contains(busca_texto, case=False, na=False) |
                df_exibir["CPF"].astype(str).str.contains(busca_texto, case=False, na=False)
            ]
            
        st.dataframe(df_exibir, use_container_width=True)
        
        if not df_exibir.empty:
            csv = df_exibir.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Relatório em CSV",
                data=csv,
                file_name="relatorio_alunos.csv",
                mime="text/csv"
            )
            
    elif senha_digitada != "":
        st.error("❌ Senha incorreta!")
