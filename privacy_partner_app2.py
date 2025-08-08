import streamlit as st
import pandas as pd
import re
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# --- Importar o Reconhecedor de Telefone ---
from presidio_analyzer.predefined_recognizers import PhoneRecognizer

# --- Reconhecedor de CPF Customizado e Inteligente ---
class CustomBrCpfRecognizer(PatternRecognizer):
    """
    Reconhecedor de CPF Brasileiro que valida o checksum (dígitos verificadores)
    e aceita formatos com ou sem pontuação.
    """
    # Regex para pegar CPF com ou sem pontuação (ex: 123.456.789-00 ou 12345678900)
    PATTERNS = [
        Pattern(
            name="cpf",
            regex=r"\b(\d{3}\.?\d{3}\.?\d{3}-?\d{2}|\d{11})\b",
            score=0.5, # Score inicial antes da validação
        ),
    ]

    def __init__(self, **kwargs):
        super().__init__(
            supported_entity="BR_CPF",
            name="Custom CPF Recognizer (with Checksum)",
            patterns=self.PATTERNS,
            **kwargs,
        )

    def validate_result(self, pattern_text: str) -> bool:
        """
        Valida o CPF encontrado usando o algoritmo de checksum.
        """
        # Limpa a string, removendo tudo que não for dígito
        cpf = "".join(re.findall(r'\d', pattern_text))

        # Verifica se o CPF tem 11 dígitos e se não são todos iguais
        if len(cpf) != 11 or len(set(cpf)) == 1:
            return False

        # Validação do primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10) % 11
        if digito1 == 10:
            digito1 = 0
        if digito1 != int(cpf[9]):
            return False

        # Validação do segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10) % 11
        if digito2 == 10:
            digito2 = 0
        if digito2 != int(cpf[10]):
            return False

        # Se todas as validações passaram, o CPF é válido
        return True


# --- Carregamento dos Motores e Configuração ---
@st.cache_resource
def get_analyzer():
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
    
    # Adicionando nossos reconhecedores "especialistas"
    analyzer.registry.add_recognizer(CustomBrCpfRecognizer())
    analyzer.registry.add_recognizer(PhoneRecognizer(supported_regions=["BR"]))
    
    return analyzer

@st.cache_resource
def get_anonymizer():
    return AnonymizerEngine()

try:
    analyzer = get_analyzer()
    anonymizer = get_anonymizer()
    st.set_page_config(page_title="Privacy Partner Demo", layout="centered")

    with open(".streamlit/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro ao carregar modelos: {e}")
    st.stop()

# --- Interface do Mockup ---
with st.sidebar:
    st.write(" Chats Recentes")
    st.button("💬 Análise de Campanha", use_container_width=True)
    st.button("📊 Relatório de Vendas", use_container_width=True)

st.markdown("<h1 style='text-align: center; color: #4A4A4A;'>L'ORÉAL GPT</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #555; font-weight: normal;'>Demonstração do Privacy Partner</h3>", unsafe_allow_html=True)
st.write("")

if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'file_is_safe' not in st.session_state:
    st.session_state.file_is_safe = True

uploaded_file = st.file_uploader("Ou anexe um arquivo (.csv) para usar como contexto:", type=["csv"])

if uploaded_file:
    with st.spinner("Analisando arquivo..."):
        df = pd.read_csv(uploaded_file)
        file_content_string = df.to_string()
        analyzer_results = analyzer.analyze(text=file_content_string, language="pt")

        if analyzer_results:
            st.error(f"🚨 **PRIVACY PARTNER:** O arquivo `{uploaded_file.name}` contém dados sensíveis. O chat está bloqueado.")
            st.session_state.file_is_safe = False
        else:
            st.success(f"✅ **PRIVACY PARTNER:** O arquivo `{uploaded_file.name}` é seguro para uso.")
            st.session_state.file_is_safe = True
else:
    st.session_state.file_is_safe = True

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Digite seu prompt ou cole um texto para análise...")

if prompt:
    if not st.session_state.file_is_safe:
        st.warning("Não é possível processar seu prompt pois o arquivo anexado contém dados sensíveis. Remova o arquivo para continuar.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Analisando prompt..."):
            analyzer_results = analyzer.analyze(text=prompt, language="pt")

        if analyzer_results:
            alert_message = f"""
            🚨 **ALERTA DO PRIVACY PARTNER!** 🚨

            Seu prompt contém **{len(analyzer_results)}** tipo(s) de informações sensíveis e não será processado.
            
            **Riscos Detectados:**
            """
            tipos_de_risco = list(set([res.entity_type for res in analyzer_results]))
            for tipo in tipos_de_risco:
                alert_message += f"\n- {tipo}"
            
            st.session_state.messages.append({"role": "assistant", "content": alert_message})
            with st.chat_message("assistant"):
                st.warning(alert_message)
        else:
            response_message = "✅ **Privacy Partner:** Nenhuma informação sensível detectada. \n\n (Aqui viria a resposta normal do L'Oréal GPT...)"
            st.session_state.messages.append({"role": "assistant", "content": response_message})
            with st.chat_message("assistant"):
                st.success(response_message)