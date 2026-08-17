import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E DESIGN CUSTOMIZADO (CSS)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Gestão Escolar",
    page_icon="🏫",
    layout="wide"
)

# Estilização do visual (Cores, Cards e Bordas)
st.markdown("""
    <style>
    /* Fundo da aplicação e estilo do container */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Personalização das Abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        font-weight: 600;
        box-shadow: 0px -2px 5px rgba(0,0,0,0.03);
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A8A !important;
        color: white !important;
    }
    
    /* Estilo dos Cards de Métricas */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-left: 5px solid #1E3A8A;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Títulos e Subtítulos */
    h1 {
        color: #1E3A8A;
        font-weight: 700;
    }
    h2, h3 {
        color: #1F2937;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# BANCO DE DADOS EM MEMÓRIA
# ---------------------------------------------------------
if "alunos_db" not in st.session_state:
    # Dados de exemplo para inicializar o Dashboard
    st.session_state["alunos_db"] = pd.DataFrame([
        {"Nome": "Ana Silva", "CPF": "111.222.333-00", "Data Nasc.": "2015-05-10", "Escola Origem": "Adélia Carneiro Pedrosa", "Turma": "5º Ano A", "Observações": "Transferência regular"},
        {"Nome": "Bruno Souza", "CPF": "222.333.444-11", "Data Nasc.": "2014-08-20", "Escola Origem": "Diogo Dias", "Turma": "6º Ano B", "Observações": ""},
        {"Nome": "Carla Santos", "CPF": "333.444.555-22", "Data Nasc.": "2016-02-15", "Escola Origem": "Adélia Carneiro Pedrosa", "Turma": "4º Ano A", "Observações": ""},
        {"Nome": "Diego Lima", "CPF": "444.555.666-33", "Data Nasc.": "2015-11-30", "Escola Origem": "Creche Criança Feliz", "Turma": "Infantil V", "Observações": ""}
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

# ---------------------------------------------------------
# CABEÇALHO DA APLICAÇÃO
# ---------------------------------------------------------
st.title("🏫 Sistema de Gestão Escolar & Transferências")
st.markdown("---")

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
    st.subheader("🔒 Acesso Restrito ao Painel de Controle")
    senha_digitada = st.text_input("Digite a senha do administrador:", type="password")
    
    # Senha padrão: admin123
    if senha_digitada == "admin123":
        st.success("🔓 Acesso liberado!")
        st.markdown("---")
        
        df_total = st.session_state["alunos_db"]
        
        # 1. CARDS DE MÉTRICAS (INDICADORES)
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total de Alunos", len(df_total))
        col_m2.metric("Escolas Registradas", df_total["Escola Origem"].nunique())
        col_m3.metric("Turmas Atendidas", df_total["Turma"].nunique())
        
        st.markdown("---")
        
        # 2. DASHBOARD GRÁFICO
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.write("### 🏫 Alunos por Escola de Origem")
            if not df_total.empty:
                grafico_escolas = df_total["Escola Origem"].value_counts()
                st.bar_chart(grafico_escolas)
                
        with col_g2:
            st.write("### 📚 Distribuição por Turma")
            if not df_total.empty:
                grafico_turmas = df_total["Turma"].value_counts()
                st.bar_chart(grafico_turmas)
                
        st.markdown("---")
        
        # 3. TABELA COM FILTROS E EXPORTAÇÃO
        st.write("### 📋 Tabela de Dados Completa")
        
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
                label="📥 Baixar Relatório em CSV/Excel",
                data=csv,
                file_name="relatorio_geral_alunos.csv",
                mime="text/csv"
            )
            
    elif senha_digitada != "":
        st.error("❌ Senha incorreta!")
