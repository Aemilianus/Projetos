import streamlit as st
import pandas as pd
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, RecognizerRegistry, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

# --- Configuração do Presidio ---
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
    
    # --- CORREÇÃO APLICADA AQUI ---
    # Reintroduzimos o motor de linguagem (NLP Engine) que é necessário para a análise
    provider_config = {"nlp_engine_name": "spacy", "models": [{"lang_code": "pt", "model_name": "pt_core_news_lg"}]}
    provider = NlpEngineProvider(nlp_configuration=provider_config)
    nlp_engine = provider.create_engine()
    
    analyzer = AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=["pt"]
    )
    anonymizer = AnonymizerEngine()
    
    return analyzer, anonymizer

analyzer, anonymizer = get_analyzer_and_anonymizer()

# --- Interface do Aplicativo ---
st.set_page_config(layout="wide", page_title="Privacy Partner - Excel Mockup")

st.markdown("##### Arquivo | Página Inicial | Inserir | Fórmulas | Dados | Revisão")
tabs = st.tabs(["▶️ **Suplementos**", "Ajuda", "Power Pivot"])
excel_tab = tabs[0]

data = {
    'Nome': ['Ana da Silva Santos', 'Maria Da Silva', 'João Dos Santos', 'José da Silva Santos'],
    'CPF': ['123.456.789-11', '123.456.789-11', '123.456.789-11', '123.456.789-11'],
    'Data': ['08/08/2025', '08/08/2025', '08/08/2025', '08/08/2025'],
    'Produto': ['Shampoo', 'Shampoo', 'Shampoo', 'Shampoo'],
    'Marca': ['Kerastase', "L'Oreal Professionnel", 'Redken', 'Redken'],
    'Valor': [150, 120, 130, 130]
}
df = pd.DataFrame(data)

if 'df_data' not in st.session_state:
    st.session_state.df_data = df

with st.container():
    st.markdown("###### Teste_Sensivel.csv")
    edited_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", key="data_editor")

with excel_tab:
    st.markdown("---")
    col1, col2, col3 = st.columns([2,2,8])
    with col1:
        if st.button("🚀 Privacy Partner Scan", help="Clique para analisar a planilha em busca de dados sensíveis."):
            with st.spinner("Analisando planilha..."):
                findings = []
                current_df = edited_df
                for index, row in current_df.iterrows():
                    for col_name, cell_value in row.items():
                        if cell_value and isinstance(cell_value, str):
                            results = analyzer.analyze(text=cell_value, language="pt")
                            if results:
                                findings.append({'row': index, 'col': col_name, 'text': cell_value, 'type': results[0].entity_type})
                st.session_state.findings = findings

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
            anonymized_df = edited_df.copy()
            for find in st.session_state.findings:
                anonymized_df.at[find['row'], find['col']] = f"<{find['type']}>"
            st.session_state.df_data = anonymized_df
            st.session_state.findings = []
            st.success("Dados anonimizados!")
            st.rerun()
    else:
        st.success("Nenhum dado sensível detectado na planilha.")