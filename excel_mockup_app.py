import streamlit as st
import pandas as pd
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, RecognizerRegistry, Pattern

# --- Configuração do Presidio ---
@st.cache_resource
def get_analyzer():
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
    return analyzer

analyzer = get_analyzer()

# --- Interface do Aplicativo ---
st.set_page_config(layout="wide", page_title="Privacy Partner - Excel Mockup")

# Barra Verde do Excel
st.markdown(
    """<div style='background-color:#1D6F42;padding:10px;border-radius:5px 5px 0 0;'>
       <h1 style='color:white;text-align:left;font-size:18px;font-weight:normal;margin:0;'>
       Excel - Sensitive_Test.csv</h1></div>""",
    unsafe_allow_html=True
)

# Simulação da "Faixa de Opções" (Ribbon)
tabs = st.tabs(["File", "Home", "Insert", "▶️ Add-ins"])
excel_tab = tabs[3]

# Dados de exemplo
data = {
    'Nome': ['Ana da Silva Santos', 'Maria Da Silva', 'João Dos Santos', 'José da Silva Santos'],
    'CPF': ['123.456.789-11', '148.258.127-24', '111.444.777-35', '987.654.321-00'],
}
df = pd.DataFrame(data)

# Inicializa o estado da sessão
if 'df_data' not in st.session_state:
    st.session_state.df_data = df.copy()
if 'original_df' not in st.session_state:
    st.session_state.original_df = df.copy()

# Container principal para a "planilha"
edited_df = st.data_editor(st.session_state.df_data, num_rows="dynamic", key="data_editor", height=250)

# Lógica do Add-in
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
            # Salva o estado atual da planilha para a reversão
            st.session_state.pseudonymized_df = edited_df.copy()

# --- Sidebar que atua como o painel do Add-in ---
with st.sidebar:
    st.title("Privacy Partner")
    st.markdown("Your privacy assistant for Excel.")
    st.markdown("---")

    if 'findings' in st.session_state and st.session_state.findings:
        st.warning(f"**Alert!** {len(st.session_state.findings)} sensitive data point(s) found.")
        
        # Mostra um resumo dos achados
        summary = {}
        for find in st.session_state.findings:
            summary.setdefault(find['col'], []).append(find['type'])
        for col, types in summary.items():
            st.markdown(f"- **Column '{col}'**: Found **{', '.join(set(types))}**.")

        st.markdown("---")
        st.markdown("**Recommended Actions:**")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Anonymize"):
                anonymized_df = edited_df.copy()
                for find in st.session_state.findings:
                    anonymized_df.at[find['row'], find['col']] = f"<{find['type']}>"
                st.session_state.df_data = anonymized_df
                st.session_state.findings = []
                st.success("Data has been anonymized!")
                st.rerun()

        with col2:
            if st.button("Pseudonymize"):
                pseudo_df = edited_df.copy()
                # Guarda o mapa de reversão
                st.session_state.pseudonym_map = {}
                for find in st.session_state.findings:
                    original_text = find['text']
                    pseudo_text = f"{find['type']}_{abs(hash(original_text)) % 10000}"
                    pseudo_df.at[find['row'], find['col']] = pseudo_text
                    st.session_state.pseudonym_map[pseudo_text] = original_text
                
                st.session_state.df_data = pseudo_df
                st.session_state.findings = []
                st.success("Data has been pseudonymized!")
                st.rerun()
                
        # Funcionalidade para reverter a pseudo-anonimização
        if 'pseudonym_map' in st.session_state and st.session_state.pseudonym_map:
            st.markdown("---")
            if st.checkbox("Simulate Admin View: Reveal Original Data"):
                st.session_state.df_data = st.session_state.original_df
                st.rerun()

    else:
        st.success("No sensitive data detected.")
