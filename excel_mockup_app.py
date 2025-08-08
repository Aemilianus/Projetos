import streamlit as st
import pandas as pd
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, RecognizerRegistry, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# --- Configuração do Presidio (Nossos "Especialistas") ---
@st.cache_resource
def get_analyzer_and_anonymizer():
    # Reconhecedor de CPF
    cpf_recognizer = PatternRecognizer(
        supported_entity="BR_CPF",
        name="CPF Recognizer",
        patterns=[Pattern(name="cpf", regex=r"\b(\d{3}\.?\d{3}\.?\d{3}-?\d{2}|\d{11})\b", score=0.9)],
        supported_language="pt"
    )
    
    registry = RecognizerRegistry(supported_languages=["pt"])
    registry.add_recognizer(cpf_recognizer)
    
    analyzer = AnalyzerEngine(registry=registry, supported_languages=["pt"])
    anonymizer = AnonymizerEngine()
    
    return analyzer, anonymizer

analyzer, anonymizer = get_analyzer_and_anonymizer()

# --- Interface do Aplicativo ---
st.set_page_config(layout="wide", page_title="Privacy Partner - Excel Mockup")

# Simulação da "Faixa de Opções" (Ribbon) do Excel
st.markdown("##### Arquivo | Página Inicial | Inserir | Fórmulas | Dados | Revisão")
tabs = st.tabs(["▶️ **Suplementos**", "Ajuda", "Power Pivot"])
excel_tab = tabs[0]

# Dados de exemplo do seu print
data = {
    'Nome': ['Ana da Silva Santos', 'Maria Da Silva', 'João Dos Santos', 'José da Silva Santos'],
    'CPF': ['123.456.789-11', '123.456.789-11', '123.456.789-11', '123.456.789-11'],
    'Data': ['08/08/2025', '08/08/2025', '08/08/2025', '08/08/2025'],
    'Produto': ['Shampoo', 'Shampoo', 'Shampoo', 'Shampoo'],
    'Marca': ['Kerastase', "L'Oreal Professionnel", 'Redken', 'Redken'],
    'Valor': [150, 120, 130, 130]
}
df = pd.DataFrame(data)

# Inicializa o estado da sessão para guardar os dados
if 'df_data' not in st.session_state:
    st.session_state.df_data = df

# Container principal para a "planilha"
with st.container():
    st.markdown("###### Teste_Sensivel.csv")
    edited_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", key="data_editor")

# Lógica do Add-in na aba "Suplementos"
with excel_tab:
    st.markdown("---")
    col1, col2, col3 = st.columns([2,2,8])
    with col1:
        if st.button("🚀 Privacy Partner Scan", help="Clique para analisar a planilha em busca de dados sensíveis."):
            with st.spinner("Analisando planilha..."):
                findings = []
                # --- CORREÇÃO APLICADA AQUI ---
                # Usamos a variável 'edited_df' diretamente
                for index, row in edited_df.iterrows():
                    for col_name, cell_value in row.items():
                        if cell_value and isinstance(cell_value, str):
                            results = analyzer.analyze(text=cell_value, language="pt")
                            if results:
                                findings.append({'row': index, 'col': col_name, 'text': cell_value, 'type': results[0].entity_type})
                
                st.session_state.findings = findings

# --- Sidebar que atua como o painel do Add-in ---
with st.sidebar:
    st.title("Privacy Partner")
    st.markdown("Seu assistente de privacidade para o Excel.")
    st.markdown("---")

    if 'findings' in st.session_state and st.session_state.findings:
        st.warning(f"**Alerta!** {len(st.session_state.findings)} dado(s) sensível(is) encontrado(s).")
        
        for find in st.session_state.findings:
            st.markdown(f"- **Coluna '{find['col']}'**: Encontrado **{find['type']}**.")

        st.markdown("---")
        st.markdown("**Ações Recomendadas:**")

        if st.button("Anonimizar Dados"):
            # Usamos a variável 'edited_df' aqui também para anonimizar o estado atual
            anonymized_df = edited_df.copy()
            for find in st.session_state.findings:
                anonymized_df.at[find['row'], find['col']] = f"<{find['type']}>"
            
            st.session_state.df_data = anonymized_df
            st.session_state.findings = []
            st.success("Dados anonimizados!")
            st.rerun()

    else:
        st.success("Nenhum dado sensível detectado na planilha.")