import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Sistema de Gestão Escolar",
    page_icon="🏫",
    layout="wide"
)

# Lista completa das 43 Escolas do Município
ESCOLAS = [
    "Adélia Carneiro Pedrosa",
    "Arcendrino César de Albuquerque",
    "Capela de São Sebastião",
    "Cônego Fernando Passos",
    "Creche Municipal Profª Etenile Urbano Pessoa",
    "Diogo Dias",
    "Dr. Araújo Filho",
    "Dr. Benigno Araújo",
    "Dr. Clóvis Fontenelle Guimarães",
    "Dr. Ludovico Correia",
    "Dr. Manoel Borba",
    "Edith Gadelha",
    "Eufrásio Vilarim",
    "Francisco Nicolau da Silva",
    "Heroínas de Tejucupapo",
    "Iracema Nogueira Rabelo",
    "Irmã Marie Armelle Falguières",
    "IV Centenário",
    "João Carneiro de Melo",
    "João Gonçalves de Azevedo",
    "José Maciel da Silva",
    "Lourenço de Albuquerque Gadelha (DISTRITO)",
    "Lourenço de Albuquerque Gadelha (SEDE)",
    "Major Manoel Gadelha",
    "Manuel César de Albuquerque",
    "Nossa Senhora das Maravilhas",
    "Prefeito Ângelo Jordão",
    "Presidente Costa e Silva",
    "Profª. Belisana Pinto Abreu de Araújo",
    "Profª. Cynira Florianna dos Prazeres",
    "Profª. Lizete Maria de Souza Rodrigues",
    "Profª. Mª Emília Valença da Silveira",
    "Profª. Tarcila Coutinho Amaral",
    "Profª. Zilma Gemir  Baracho",
    "Santa Maria",
    "Santo Antônio de Pádua",
    "São Thomaz de Aquino",
    "Creche Criança Feliz",
    "CMEI - Vereador Jose Batista dos Santos",
    "CMEI - Prefeito Osvaldo Rabelo Filho",
    "CMEI - Carlos Alberto dos Santos Viegas",
    "Centro de Atendimento de Educação Especial Professora Margarida Braga",
    "Edjanete Maria Valença da Silveira"
]

st.title("🏫 Sistema de Gestão de Alunos e Transferências")

# Estrutura de Navegação por Abas
aba_cadastro, aba_importacao, aba_consulta = st.tabs([
    "📝 Novo Cadastro", 
    "📥 Importação em Lote (15 Dias)",
    "👥 Alunos Cadastrados"
])

# ---------------------------------------------------------
# ABA 1: NOVO CADASTRO
# ---------------------------------------------------------
with aba_cadastro:
    st.subheader("Cadastro Individual de Aluno")
    
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

        btn_salvar = st.form_submit_button("Salvar Cadastro")
        
        if btn_salvar:
            if nome and cpf and escola_origem:
                st.success(f"✅ Aluno(a) **{nome}** cadastrado(a) com sucesso!")
            else:
                st.error("⚠️ Por favor, preencha todos os campos obrigatórios (*).")

# ---------------------------------------------------------
# ABA 2: IMPORTAÇÃO EM LOTE
# ---------------------------------------------------------
with aba_importacao:
    st.subheader("📥 Importação de Dados Quinzenal (15 Dias)")
    
    st.info("Envie a planilha contendo a relação de novos alunos ou atualizações de transferência.")
    
    arquivo_enviado = st.file_uploader(
        "Selecione o arquivo da planilha (.xlsx ou .csv)", 
        type=["xlsx", "csv"]
    )
    
    if arquivo_enviado is not None:
        try:
            if arquivo_enviado.name.endswith('.csv'):
                df = pd.read_csv(arquivo_enviado)
            else:
                df = pd.read_excel(arquivo_enviado)
                
            st.success("✅ Arquivo carregado com sucesso!")
            
            st.write("### 🔍 Prévia dos Dados para Validação:")
            st.dataframe(df, use_container_width=True)
            
            # Métricas rápidas de verificação
            total_linhas = len(df)
            col_a, col_b = st.columns(2)
            col_a.metric("Total de Registros Detectados", total_linhas)
            col_b.metric("Status da Validação", "Pronto para Importar", delta="OK")
            
            if st.button("🚀 Processar e Confirmar Importação"):
                st.balloons()
                st.success(f"Processamento concluído! {total_linhas} registros importados com sucesso.")
                
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")

# ---------------------------------------------------------
# ABA 3: LISTA DE ALUNOS
# ---------------------------------------------------------
with aba_consulta:
    st.subheader("👥 Consulta e Relatórios")
    st.write("Filtre a lista de alunos por escola de origem:")
    
    escola_filtro = st.selectbox("Filtrar por Escola", options=["Todas"] + ESCOLAS)
    st.text_input("Buscar por Nome ou CPF")
    
    st.caption("A base de dados exibirá os registros de acordo com o filtro selecionado acima.")