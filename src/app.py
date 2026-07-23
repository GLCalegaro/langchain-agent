import uuid

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.errors import GraphRecursionError

from agent_runtime import AgentRuntime
from logging_config import configure_logging
from settings import Settings
from utils import sanitize_response

st.set_page_config(
    page_title="Aryaz - Assistente de Moda - Demo",
    page_icon="👗",
    layout="centered",
)


@st.cache_resource
def get_runtime() -> AgentRuntime:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    return AgentRuntime.create(settings)


def new_thread() -> None:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.resume_thread_id = ""


def valid_thread_id(value: str) -> str | None:
    try:
        return str(uuid.UUID(value.strip()))
    except (ValueError, AttributeError):
        return None


if "thread_id" not in st.session_state:
    new_thread()

st.title("👗 Aryaz - Assistente de Moda Virtual")
st.caption(
    "Demonstração com catálogo e pedidos fictícios. Converse sobre looks, "
    "produtos, entregas e devoluções."
)

try:
    runtime = get_runtime()
except (ValueError, TypeError) as error:
    st.error(str(error))
    st.stop()
except Exception:
    st.error(
        "Não foi possível iniciar o assistente. Confira a configuração e "
        "tente novamente."
    )
    st.stop()

with st.sidebar:
    st.subheader("Conversa")
    st.caption("Código de acesso")
    st.code(st.session_state.thread_id, language=None)
    st.caption(f"Memória ativa: {runtime.backend}")

    if runtime.persistence_warning:
        st.warning(runtime.persistence_warning)

    st.button("Nova conversa", use_container_width=True, on_click=new_thread)

    resume_value = st.text_input(
        "Retomar pelo código",
        key="resume_thread_id",
        placeholder="00000000-0000-0000-0000-000000000000",
    )
    if st.button("Retomar conversa", use_container_width=True):
        normalized_thread_id = valid_thread_id(resume_value)
        if normalized_thread_id is None:
            st.error("Informe um código de conversa válido.")
        else:
            try:
                restored_messages = runtime.messages(normalized_thread_id)
            except Exception:
                st.error("Não foi possível consultar essa conversa.")
            else:
                if restored_messages:
                    st.session_state.thread_id = normalized_thread_id
                    st.success("Conversa retomada.")
                    st.rerun()
                else:
                    st.warning("Nenhuma conversa persistida foi encontrada.")

try:
    messages = runtime.messages(st.session_state.thread_id)
except Exception:
    messages = []
    st.error("Não foi possível carregar o histórico desta conversa.")

for message in messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(sanitize_response(message.content))
    elif isinstance(message, AIMessage) and not message.tool_calls:
        content = sanitize_response(message.content)
        if content:
            with st.chat_message("assistant"):
                st.markdown(content)

user_input = st.chat_input("Digite sua mensagem...")
if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                result = runtime.invoke(
                    st.session_state.thread_id,
                    HumanMessage(content=user_input),
                )
                last_message = result["messages"][-1]
                answer = sanitize_response(last_message.content)
                st.markdown(
                    answer
                    or "Não consegui gerar uma resposta agora. Tente novamente."
                )
            except GraphRecursionError:
                st.warning(
                    "A solicitação exigiu etapas demais. Reformule a pergunta "
                    "ou informe os dados pedidos."
                )
            except Exception:
                st.error(
                    "O assistente está temporariamente indisponível. "
                    "Tente novamente em instantes."
                )
