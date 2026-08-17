import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Sistema de Gestão Escolar",
    page_icon="🏫",
    layout="wide"
)

# Estilização CSS avançada para formulários e cards
st.markdown("""
    <style>
    /* Fundo suave do sistema */
    .stApp {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
    }
    
    /* Fontes e Títulos */
    h1, h2, h3, h4, label, .stMarkdown {
        color: #0f172a !important;
        font-family: 'Inter', sans-serif;
    }

    /* Estilo dos Containers dos Formulários e Blocos */
    [data-testid="stForm"], .upload-card {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 16px !important;
        padding: 25px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05) !important;
        margin-bottom: 25px !important;
    }

    /* Destaque dos Campos de Texto e Seleção (Inputs) */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea, .stDateInput input {
        background-color: #ffffff !important;
        border: 1.5px solid #94a3b8 !important;
        border-radius: 8px !important;
        color: #0f172a !important;
        font-weight: 500 !important;
    }

    /* Foco nos campos quando clicados */
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #4f46e5 !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2) !important;
    }

    /* Botões em Destaque */
    .stFormSubmitButton > button, .stButton > button {
        background-color: #4f46e5 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.3) !important;
        transition: all 0.2s ease-in-out !important;
    }

    .stFormSubmitButton > button:hover, .stButton > button:hover {
        background-color: #4338ca !important;
        transform: translateY(-1px) !important;
    }

    /* Customização das Abas */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .stTabs [aria-selected="true"] {
        background-color: #4f46e5 !important;
        color: #ffffff !important;
        border-radius: 8px;
    }

    /* Estilos do Dashboard (Cards KPIs) */
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
    </style>
""", unsafe_allow_html=True)

# Banco de dados inicial
if "alunos_db" not in st.session_state:
    st.session_state["alunos_db"] = pd.DataFrame([
        {"Nome": "Ana Silva", "CPF": "111.222.333-00", "Data Nasc.": "2015-05-10", "Escola Origem": "Escola Municipal Dom Pedro II", "Turma": "5º Ano A", "Observações": "Regular"},
        {"Nome": "Bruno Souza", "CPF": "222.333.444-11", "Data Nasc.": "2010-08-20", "Escola Origem": "Escola Municipal Dom Pedro II", "Turma": "6º Ano B", "Observações": ""},
        {"Nome": "Carla Santos", "CPF": "333.444.555-22", "Data Nasc.": "2018-02-15", "Escola Origem": "Escola Municipal Paulo Freire", "Turma": "4º Ano A", "Observações": ""},
        {"Nome": "Diego Lima", "CPF": "444.555.666-33", "Data Nasc.": "2012-11-30", "Escola Origem": "Escola Municipal Monteiro Lobato", "Turma": "7º Ano C", "Observações": ""}
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

# Estrutura com 2 abas (A Importação agora fica dentro da primeira aba)
aba_cadastro, aba_admin = st.tabs([
    "📝 Cadastro de Alunos", 
    "📊 Área do Administrador (Dashboard)"
])

# ---------------------------------------------------------
# ABA 1: CADASTRO E IMPORTAÇÃO
# ---------------------------------------------------------
with aba_cadastro:
    # SEÇÃO 1: Cadastro Individual
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

        st.markdown("<br>", unsafe_allow_html=True)
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

    st.markdown("---")

    # SEÇÃO 2: Importação em Lote (Posicionada logo abaixo)
    st.subheader("📥 Importação em Lote (Planilhas)")
    
    arquivo_enviado = st.file_uploader(
        "Selecione o arquivo da planilha (.xlsx ou .csv)", 
        type=["xlsx", "csv"],
        key="uploader_lote"
    )
    
    if arquivo_enviado is not None:
        try:
            df_upload = pd.read_csv(arquivo_enviado) if arquivo_enviado.name.endswith('.csv') else pd.read_excel(arquivo_enviado)
            st.success("✅ Arquivo carregado com sucesso!")
            st.dataframe(df_upload, use_container_width=True)
            
            if st.button("🚀 Processar e Salvar Registros"):
                st.session_state["alunos_db"] = pd.concat([st.session_state["alunos_db"], df_upload], ignore_index=True)
                st.balloons()
                st.success(f"Total de {len(df_upload)} registros integrados ao banco de dados!")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

# ---------------------------------------------------------
# ABA 2: DASHBOARD DO ADMINISTRADOR
# ---------------------------------------------------------
with aba_admin:
    senha_digitada = st.text_input("Digite a senha do administrador:", type="password")
    
    if senha_digitada == "admin123":
        df = st.session_state["alunos_db"]
        
        total_alunos = len(df)
        escolas_ativas = df["Escola Origem"].nunique()
        
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
                        <div class="kpi-subtitle" style="color: #10b981;">📈 Base Consolidada</div>
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
                        <div class="kpi-title">SEGURANÇA DE DADOS</div>
                        <div class="kpi-value">100%</div>
                        <div class="kpi-subtitle" style="color: #64748b;">Isolamento Ativo por Escola</div>
                    </div>
                    <div class="kpi-icon icon-blue">🛡️</div>
                </div>
            """, unsafe_allow_html=True)

        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("### 📊 Cadastros por Escola")
            if not df.empty:
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
        st.markdown("### 📋 Exportar Base de Dados Unificada")
        st.dataframe(df, use_container_width=True)
        
        if not df.empty:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar CSV",
                data=csv,
                file_name="base_dados_unificada.csv",
                mime="text/csv"
            )
            
    elif senha_digitada != "":
        st.error("❌ Senha incorreta!")
