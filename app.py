# ---------------------------------------------------------
        # SEÇÃO: Importação em Lote (Planilhas) - Layout Moderno
        # ---------------------------------------------------------
        st.markdown("""
        <style>
        /* Card Container Principal para Importação */
        .import-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .import-card:hover {
            border-color: #cbd5e1;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.06);
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
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .card-header-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card-description {
            font-size: 0.875rem;
            color: #64748b;
            line-height: 1.5;
            margin-bottom: 20px;
        }
        .info-pill {
            background-color: #f8fafc;
            border: 1px dashed #cbd5e1;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 0.8rem;
            color: #475569;
            margin-bottom: 16px;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("<h3 style='margin-top: 30px; margin-bottom: 20px;'>📥 Importação de Alunos em Lote</h3>", unsafe_allow_html=True)

        col_left, col_right = st.columns(2, gap="medium")

        # PASSO 1: Baixar Modelo
        with col_left:
            st.markdown("""
            <div class="import-card">
                <div>
                    <span class="step-badge">Passo 1</span>
                    <div class="card-header-title">📄 Baixar Planilha Modelo</div>
                    <div class="card-description">
                        Baixe o modelo oficial padronizado em Excel para preencher as informações dos alunos com a formatação correta antes de realizar a importação.
                    </div>
                    <div class="info-pill">
                        💡 <b>Campos inclusos:</b> Nome, CPF, Data Nasc., Escola Origem, Turma e Observações.
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Botão de Download estilizado
            st.download_button(
                label="📥 Baixar Modelo (.xlsx)",
                data=gerar_planilha_modelo(),
                file_name="modelo_importacao_alunos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        # PASSO 2: Enviar Planilha Preenchida
        with col_right:
            st.markdown("""
            <div class="import-card">
                <div>
                    <span class="step-badge" style="background-color: #d1fae5; color: #059669;">Passo 2</span>
                    <div class="card-header-title">📤 Upload da Planilha Preenchida</div>
                    <div class="card-description">
                        Envie o arquivo preenchido contendo os dados dos alunos. Suportamos arquivos nos formatos <b>.XLSX</b> ou <b>.CSV</b>.
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            arquivo_enviado = st.file_uploader(
                "Arraste ou selecione seu arquivo", 
                type=["xlsx", "csv"],
                key="uploader_lote_novo",
                label_visibility="collapsed"
            )

        # Processamento do Arquivo Enviado
        if arquivo_enviado is not None:
            st.markdown("<br>", unsafe_allow_html=True)
            try:
                df_upload = pd.read_csv(arquivo_enviado) if arquivo_enviado.name.endswith('.csv') else pd.read_excel(arquivo_enviado)
                
                st.success(f"✅ **Arquivo carregado com sucesso!** Foram encontrados **{len(df_upload)}** registros.")
                
                with st.expander("🔍 Pré-visualizar dados importados", expanded=True):
                    st.dataframe(df_upload, use_container_width=True)
                
                if st.button("🚀 Confirmar e Integrar Registros", use_container_width=True):
                    st.session_state["alunos_db"] = pd.concat([st.session_state["alunos_db"], df_upload], ignore_index=True)
                    st.balloons()
                    st.success(f"🎉 Todos os {len(df_upload)} alunos foram salvos no banco de dados!")
            except Exception as e:
                st.error(f"❌ Erro ao ler o arquivo: {e}")
