import streamlit as st
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# --- Configuração dos Motores (Corrigida) ---
@st.cache_resource
def get_analyzer():
    """Cria e configura o motor de análise do Presidio."""
    provider_config = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "pt", "model_name": "pt_core_news_lg"}]
    }
    provider = NlpEngineProvider(nlp_configuration=provider_config)
    nlp_engine = provider.create_engine()
    
    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=["pt"]
    )
    return analyzer

@st.cache_resource
def get_anonymizer():
    """Cria o motor de anonimização."""
    return AnonymizerEngine()

# --- Carregamento dos Motores ---
try:
    analyzer = get_analyzer()
    anonymizer = get_anonymizer()
    st.set_page_config(page_title="Privacy Partner Demo", layout="wide")
except Exception as e:
    st.error(f"Ocorreu um erro ao carregar os modelos de IA. Verifique se o download do 'pt_core_news_lg' foi concluído com sucesso. Erro: {e}")
    st.stop()


# --- Interface da Aplicação ---
st.title("🚀 Privacy Partner: Demonstração Interativa")
st.markdown("Esta é uma prova de conceito para demonstrar como o Privacy Partner pode identificar e proteger dados pessoais em tempo real.")

# --- Parte 1: Análise de Texto Livre ---
st.header("1. Teste de Detecção em Tempo Real")
st.write("Cole qualquer texto abaixo para ver o motor de IA (Microsoft Presidio) identificar informações pessoais.")

text_to_analyze = st.text_area("Insira o texto aqui:", """
Olá, Ana Silva.
Conforme conversamos, o CPF do cliente Carlos Souza é 123.456.789-00.
Por favor, envie o contrato para o endereço Rua das Flores, 123, São Paulo.
O telefone dele é (11) 99999-8888.
""", height=150)

if st.button("Analisar e Proteger Texto"):
    if text_to_analyze:
        with st.spinner("Analisando o texto..."):
            analyzer_results = analyzer.analyze(text=text_to_analyze, language="pt")
            
            st.subheader("Resultados da Análise:")
            if analyzer_results:
                st.write(f"🚨 **{len(analyzer_results)} riscos de privacidade foram detectados!**")
                
                # Anonimizar o texto para exibição segura
                anonymized_result = anonymizer.anonymize(
                    text=text_to_analyze,
                    analyzer_results=analyzer_results,
                    operators={"DEFAULT": OperatorConfig("replace", {"new_value": "******"})}
                )
                
                st.text_area("Texto Protegido:", anonymized_result.text, height=150)

                st.write("Detalhes dos riscos encontrados:")
                for result in analyzer_results:
                    # CORREÇÃO APLICADA AQUI:
                    texto_encontrado = text_to_analyze[result.start:result.end]
                    st.info(f"- **Tipo de Risco:** {result.entity_type}\n"
                            f"  **Texto Encontrado:** '{texto_encontrado}'\n"
                            f"  **Nível de Confiança:** {result.score:.2f}")
            else:
                st.success("✅ Análise concluída. Nenhum risco de privacidade evidente foi detectado.")
    else:
        st.warning("Por favor, insira um texto para analisar.")

st.divider()

# --- Parte 2: Demonstração de Pseudonimização Customizada ---
st.header("2. Demonstração de Customização e Escalabilidade")
st.write("""
Aqui demonstramos o poder da **Pseudonimização Reversível**. 
A ferramenta substitui um termo específico por um 'token' (um pseudônimo). 
A 'chave' para reverter isso ficaria guardada em um cofre seguro na L'Oréal. 
Isso prova que qualquer departamento, em qualquer país, poderia customizar o Privacy Partner para proteger seus próprios termos de negócio (nomes de projetos, fórmulas, etc.), garantindo escalabilidade global.
""")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Texto Original")
    custom_text = st.text_input("Dado a ser protegido:", "Privacy Partner, o seu parceiro de privacidade.")
    
    if st.button("Pseudonimizar 🕵️"):
        # Simula a criação de um "token" - na vida real, seria um hash ou ID único
        pseudonym = f"<PROJETO_CONFIDENCIAL_{hash(custom_text)}>"
        st.session_state.pseudonym = pseudonym
        st.session_state.original_text = custom_text

    if 'pseudonym' in st.session_state and st.session_state.pseudonym:
        st.success(f"**Texto Pseudonimizado:**\n\n`{st.session_state.pseudonym}`")

with col2:
    st.subheader("Reversão (Com a 'Chave')")
    if 'pseudonym' in st.session_state and st.session_state.pseudonym:
        st.write(f"O sistema agora só vê o token: `{st.session_state.pseudonym}`")
        if st.button("Reverter para Original 🔑"):
            st.info(f"**Texto Original Restaurado:**\n\n`{st.session_state.original_text}`")