import streamlit as st
import uuid
import uuid_utils
import sys
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.graph.state import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from typing import cast

from context import Context

ROOT = Path(__file__).parent
sys.path.append(str(ROOT / "src"))

from graph import build_graph
from prompts import SYSTEM_PROMPT
from utils import sanitize_response

st.set_page_config(page_title="Aryaz - Assistente de Moda - Demo", page_icon="👗", layout="centered")
st.title("👗 Aryaz - Assistente de Moda Virtual")
st.caption("✨ Bem-vindo! Sou seu assistente de moda inteligente. Posso ajudá-lo com sugestões de looks, dúvidas sobre pedidos, devoluções e tudo mais. Basta iniciar uma conversa! 💬")

# --- Estado da sessão ---
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# Valores padrão de configuração
user_type = "plus"
recursion_limit = 25
max_concurrency = 4

# --- Cache do grafo (não recompilar a cada rerun) ---
@st.cache_resource
def get_graph():
    checkpointer = MemorySaver()
    return build_graph(checkpointer=checkpointer)

graph = get_graph()

# Renderiza histórico
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            # AIMessage às vezes tem .content ou .text dependendo da versão
            content = getattr(msg, "content", None) or getattr(msg, "text", "")
            clean_content = sanitize_response(content)
            st.markdown(clean_content)

# Input do usuário
user_input = st.chat_input("Digite sua mensagem...")

if user_input:
    # Adiciona mensagem do usuário
    st.session_state.messages.append(HumanMessage(user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    # Monta loop atual (igual seu main.py: adiciona SystemMessage só na primeira interação)
    current_loop_messages: list[BaseMessage]
    if len(st.session_state.messages) == 1:  # primeira do usuário
        current_loop_messages = cast(list[BaseMessage], [SystemMessage(SYSTEM_PROMPT)] + st.session_state.messages)
    else:
        current_loop_messages = [HumanMessage(user_input)]

    # Config (thread_id mantém “memória” do grafo via checkpointer)
    config = RunnableConfig(
        run_name="meu_grafo_streamlit",
        tags=["streamlit"],
        configurable={"thread_id": st.session_state.thread_id},
        max_concurrency=max_concurrency,
        recursion_limit=recursion_limit,
    )

    # Cria o contexto com o user_type
    context = Context(user_type=user_type)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            result = graph.invoke({"messages": current_loop_messages}, config=config, context=context)
            last_message = result["messages"][-1]

            # Extrai apenas o conteúdo de texto, rejeitando metadados sensíveis
            answer = getattr(last_message, "content", None) or getattr(last_message, "text", "")
            
            # Sanitiza a resposta: remove tokens, signatures e outros metadados sensíveis
            answer = sanitize_response(answer)
            
            st.markdown(answer)

    # Atualiza histórico completo com o retorno do grafo (igual seu main.py)
    # Limpa mensagens de metadados que não devem ser exibidas novamente
    st.session_state.messages = result["messages"]
