import streamlit as st
import pandas as pd
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, RecognizerRegistry, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

# --- Presidio Configuration ---
@st.cache_resource
def get_analyzer_and_anonymizer():
    # Cria um registro para o idioma português
    registry = RecognizerRegistry(supported_languages=["pt"])
    
    # --- CORREÇÃO APLICADA AQUI ---
    # Carrega os reconhecedores padrão (incluindo o de Nomes - PERSON)
    registry.load_predefined_recognizers(languages=["pt"])

    # Define e adiciona nosso reconhecedor customizado de CPF
    cpf_recognizer = PatternRecognizer(
        supported_entity="BR_CPF",
        name="CPF Recognizer",
        patterns=[Pattern(name="cpf", regex=r"\b(\d{3}\.?\d{3}\.?\d{3}-?\d{2}|\d{11})\b", score=0.9)],
        supported_language="pt"
    )
    registry.add_recognizer(cpf_recognizer)
    
    # Configura o motor de linguagem que alimenta os reconhecedores
    provider_config = {"nlp_engine_name": "spacy", "models": [{"lang_code": "pt", "model_name": "pt_core_news_lg"}]}
    provider = NlpEngineProvider(nlp_configuration=provider_config)
    nlp_engine = provider.create_engine()
    
    # Cria o motor de análise com o registro completo
    analyzer = AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=["pt"]
    )
    anonymizer = AnonymizerEngine()
    
    return analyzer, anonymizer

analyzer, anonymizer = get_analyzer_and_anonymizer()

# --- Application Interface ---
st.set_page_config(layout="wide", page_title="Privacy Partner - Excel Mockup")

st.markdown(
    """<div style="background-color:#1D6F42;padding:10px;border-top-left-radius:5px;border-top-right-radius:5px;"><h1 style="color:white;text-align:left;font-size:18px;font-weight:normal;margin:0;">
       Excel - Sensitive_Test.csv</h1></div>""",
    unsafe_allow_html=True
)

st.markdown("##### File | Home | Insert | Formulas | Data | Review")
tabs = st.tabs(["▶️ **Add-ins**", "Help", "Power Pivot"])
excel_tab = tabs[0]

data = {
    'Nome': ['Ana da Silva Santos', 'Maria Da Silva', 'João Dos Santos', 'José da Silva Santos'],
    'CPF': ['123.456.789-11', '148.258.127-24', '111.444.777-35', '987.654.321-00']
}
df = pd.DataFrame(data)

if 'df_data' not in st.session_state:
    st.session_state.df_data = df.copy()
if 'original_df' not in st.session_state:
    st.session_state.original_df = df.copy()
if 'findings' not in st.session_state:
    st.session_state.findings = []

with st.container():
    edited_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", key="data_editor", height=250)

with excel_tab:
    if st.button("🚀 Privacy Partner Scan", help="Click to scan the spreadsheet for sensitive data."):
        with st.spinner("Analyzing spreadsheet..."):
            findings = []
            current_df = edited_df
            for index, row in current_df.iterrows():
                for col_name, cell_value in row.items():
                    if cell_value and isinstance(cell_value, str):
                        results = analyzer.analyze(text=cell_value, language="pt")
                        if results:
                            findings.append({'row': index, 'col': col_name, 'text': cell_value, 'type': results[0].entity_type})
            st.session_state.findings = findings
            st.session_state.last_edited_df = edited_df.copy()

with st.sidebar:
    st.title("Privacy Partner")
    st.markdown("Your privacy assistant for Excel.")
    st.markdown("---")
    
    if st.button("Reset to Original Data"):
        st.session_state.df_data = st.session_state.original_df.copy()
        st.session_state.findings = []
        st.rerun()

    if 'findings' in st.session_state and st.session_state.findings:
        st.warning(f"**Alert!** {len(st.session_state.findings)} sensitive data point(s) found.")
        
        summary = {}
        for find in st.session_state.findings:
            summary.setdefault(find['col'], []).append(find['type'])
        for col, types in summary.items():
            st.markdown(f"- **Column '{col}'**: Found **{', '.join(set(types))}**.")

        st.markdown("---")
        st.markdown("**Recommended Actions:**")

        col_anon, col_pseudo = st.columns(2)
        with col_anon:
            if st.button("Anonymize"):
                anonymized_df = st.session_state.last_edited_df.copy()
                for find in st.session_state.findings:
                    anonymized_df.at[find['row'], find['col']] = f"<{find['type']}>"
                st.session_state.df_data = anonymized_df
                st.session_state.findings = []
                st.rerun()

        with col_pseudo:
            if st.button("Pseudonymize"):
                pseudo_df = st.session_state.last_edited_df.copy()
                st.session_state.pseudonym_map = {}
                for find in st.session_state.findings:
                    original_text = find['text']
                    pseudo_text = f"{find['type']}_{abs(hash(original_text)) % 10000}"
                    pseudo_df.at[find['row'], find['col']] = pseudo_text
                    st.session_state.pseudonym_map[pseudo_text] = original_text
                st.session_state.df_data = pseudo_df
                st.session_state.findings = []
                st.rerun()
                
        if 'pseudonym_map' in st.session_state and st.session_state.pseudonym_map:
            st.markdown("---")
            if st.checkbox("Simulate Admin View: Reveal Original Data"):
                st.session_state.df_data = st.session_state.original_df
                st.session_state.pseudonym_map = {}
                st.rerun()

    else:
        st.success("No sensitive data detected.")
