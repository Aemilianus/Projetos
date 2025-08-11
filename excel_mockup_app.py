import streamlit as st
import pandas as pd
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, RecognizerRegistry, Pattern
from presidio_anonymizer import AnonymizerEngine

# --- Presidio Configuration ---
@st.cache_resource
def get_analyzer_and_anonymizer():
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

# --- Application Interface ---
st.set_page_config(layout="wide", page_title="Privacy Partner - Excel Mockup")

# Green Excel Header Bar
st.markdown(
    """<div style='background-color:#1D6F42;padding:10px;border-radius:5px 5px 0 0;'>
       <h1 style='color:white;text-align:left;font-size:18px;font-weight:normal;margin:0;'>
       Excel - Sensitive_Test.csv</h1></div>""",
    unsafe_allow_html=True
)

# Simulation of Excel's Ribbon
tabs = st.tabs(["File", "Home", "Insert", "▶️ Add-ins"])
excel_tab = tabs[3]

# Sample data
data = {
    'Nome': ['Ana da Silva Santos', 'Maria Da Silva', 'João Dos Santos', 'José da Silva Santos'],
    'CPF': ['123.456.789-11', '148.258.127-24', '111.444.777-35', '987.654.321-00'],
}
df = pd.DataFrame(data)

# Initialize session state
if 'df_data' not in st.session_state:
    st.session_state.df_data = df.copy()
if 'original_df' not in st.session_state:
    st.session_state.original_df = df.copy()
if 'findings' not in st.session_state:
    st.session_state.findings = []
if 'pseudonym_map' not in st.session_state:
    st.session_state.pseudonym_map = {}

# Main container for the "spreadsheet"
edited_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", key="data_editor", height=250)

# Logic for the Add-in in the "Add-ins" tab
with excel_tab:
    if st.button("🚀 Privacy Partner Scan", help="Click to scan the spreadsheet for sensitive data."):
        with st.spinner("Analyzing spreadsheet..."):
            findings = []
            for index, row in edited_df.iterrows():
                for col_name, cell_value in row.items():
                    if cell_value and isinstance(cell_value, str):
                        results = analyzer.analyze(text=cell_value, language="pt")
                        if results:
                            findings.append({'row': index, 'col': col_name, 'text': cell_value, 'type': results[0].entity_type})
            st.session_state.findings = findings
            st.session_state.pseudonym_map = {} # Reset map on new scan

# --- Sidebar acting as the Add-in's task pane ---
with st.sidebar:
    st.title("Privacy Partner")
    st.markdown("Your privacy assistant for Excel.")
    st.markdown("---")

    if st.session_state.findings:
        st.warning(f"**Alert!** {len(st.session_state.findings)} sensitive data point(s) found.")
        
        problematic_cols = sorted(list(set([find['col'] for find in st.session_state.findings])))
        
        st.markdown("**1. Select Columns to Action:**")
        selected_cols = st.multiselect("Columns with sensitive data:", options=problematic_cols, default=problematic_cols)

        st.markdown("**2. Choose Action:**")
        col_anon, col_pseudo = st.columns(2)
        with col_anon:
            if st.button("Anonymize Selected"):
                anonymized_df = edited_df.copy()
                for find in st.session_state.findings:
                    if find['col'] in selected_cols:
                        anonymized_df.at[find['row'], find['col']] = f"<{find['type']}>"
                st.session_state.df_data = anonymized_df
                st.session_state.findings = [] # Clear findings after action
                st.rerun()

        with col_pseudo:
            if st.button("Pseudonymize Selected"):
                pseudo_df = edited_df.copy()
                temp_map = {}
                for find in st.session_state.findings:
                    if find['col'] in selected_cols:
                        original_text = find['text']
                        pseudo_text = f"{find['type']}_{abs(hash(original_text)) % 10000}"
                        pseudo_df.at[find['row'], find['col']] = pseudo_text
                        temp_map[pseudo_text] = original_text
                
                st.session_state.df_data = pseudo_df
                st.session_state.pseudonym_map = temp_map # Save the map
                st.session_state.findings = [] # Clear findings
                st.rerun()

    else:
        st.success("No sensitive data detected.")

    # --- Reversion Logic ---
    if st.session_state.pseudonym_map:
        st.markdown("---")
        st.info("Data has been pseudonymized.")
        if st.checkbox("Simulate Admin View: Reveal Original Data"):
            st.session_state.df_data = st.session_state.original_df.copy()
            st.session_state.pseudonym_map = {} # Clear map after reverting
            st.rerun()
