# Aryaz - LangChain Agent

Assistente virtual de moda e atendimento construído com LangChain, LangGraph,
Gemini e Streamlit. O projeto demonstra sugestões de looks, pesquisa de
catálogo, consulta de pedidos, problemas de entrega e devoluções.

> Catálogo, pedidos, datas e protocolos desta aplicação são fictícios.

## Arquitetura

O Streamlit envia cada mensagem ao grafo LangGraph usando um `thread_id`. Esse
identificador é a chave usada pelo checkpointer para recuperar o estado da
conversa.

O fluxo principal é:

```text
Usuário -> call_llm -> resposta
                    -> tools -> call_llm -> resposta
```

O prompt de sistema é injetado pelo nó `call_llm` em todas as chamadas, mas não
é persistido no histórico. O estado salvo contém as mensagens do usuário, do
modelo e das tools.

### Memória e retomada

O backend preferencial é PostgreSQL, usando `PostgresSaver`. Na inicialização,
as tabelas necessárias são preparadas automaticamente. Se o banco estiver
indisponível, a aplicação usa `InMemorySaver` e mostra um aviso de que as novas
mensagens não serão persistidas.

Na barra lateral é possível:

- copiar o código da conversa;
- iniciar uma nova conversa;
- retomar uma conversa persistida informando um UUID válido.

O código funciona como acesso à conversa nesta demonstração. Não há
autenticação.

## Tools

As tools possuem entradas validadas por Pydantic e retornam objetos com
`status`, `message`, `data` e `protocol`, quando aplicável.

- `suggest_outfit`: monta um look com itens fictícios.
- `search_catalog`: filtra catálogo por categoria, tamanho, cor, ocasião e
  preço.
- `get_order_status`: consulta um pedido fictício.
- `late_delivery`: orienta problemas de entrega com base no status do pedido.
- `start_return`: valida e gera um protocolo fictício de devolução.

Dados de demonstração estão em `src/data`. Alguns pedidos disponíveis para
teste são `ARY-1001`, `ARY-1002` e `ARY-1003`.

## Fallbacks

- PostgreSQL indisponível: troca para memória e mantém o chat em funcionamento.
- Erro transitório do modelo: realiza novas tentativas com espera exponencial
  curta.
- Erro de tool: retorna uma mensagem segura para o modelo, sem detalhes da
  exceção.
- Limite de recursão: pede ao usuário para reformular ou fornecer os dados
  faltantes.
- Resposta em formato inesperado: exibe apenas o texto sanitizado.

## Logs e LangSmith

Os logs são escritos em JSON no stdout. Cada execução registra eventos, duração,
backend de memória e nomes de nó ou tool. `thread_id` e `run_id` aparecem
mascarados. Conteúdo das mensagens, API keys e DSN não são registrados.

O tracing do LangSmith é opcional:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=sua_chave
LANGSMITH_PROJECT=aryaz
```

Sem essas variáveis, o agente continua funcionando normalmente.

## Configuração

Copie `.env.example` para `.env` e informe ao menos uma chave do Gemini:

```env
GOOGLE_API_KEY=sua_chave
DB_DSN=postgresql://aryaz:aryaz@localhost:5432/aryaz
```

Variáveis disponíveis:

| Variável | Padrão | Finalidade |
| --- | --- | --- |
| `GOOGLE_API_KEY` ou `GEMINI_API_KEY` | obrigatório | Acesso ao Gemini |
| `DB_DSN` | vazio | Conexão PostgreSQL |
| `MODEL_NAME` | `gemini-2.5-flash` | Modelo Google GenAI |
| `MODEL_TEMPERATURE` | `0.2` | Temperatura do modelo |
| `MODEL_MAX_RETRIES` | `2` | Novas tentativas após falha |
| `RECURSION_LIMIT` | `12` | Limite de passos do grafo |
| `MAX_CONCURRENCY` | `4` | Pool e concorrência |
| `LOG_LEVEL` | `INFO` | Nível dos logs |
| `APP_ENV` | `development` | Tag do ambiente |

## Executar com Docker Compose

O Compose inicia a aplicação e um PostgreSQL com volume persistente:

```bash
docker compose up --build
```

Acesse [http://localhost:8501](http://localhost:8501). Para acompanhar os logs:

```bash
docker compose logs -f app
```

Para encerrar os containers sem apagar as conversas:

```bash
docker compose down
```

O volume só é removido quando `docker compose down -v` é executado.

## Executar somente a imagem

Com um PostgreSQL já disponível:

```bash
docker build -t langchain-agent .
docker run --rm -p 8501:8501 --env-file .env langchain-agent
```

## Executar localmente

Requer Python 3.13:

```bash
pip install -r requirements.txt
streamlit run src/app.py
```

O fluxo de terminal também está disponível:

```bash
python src/main.py
```

## Testes e qualidade

```bash
pip install -r requirements-dev.txt
pytest
ruff check src tests
pyright
```

Os testes não chamam Gemini nem serviços externos. O modelo é injetado no grafo
e substituído por implementações determinísticas.

Com um PostgreSQL de teste configurado, o teste de integração pode ser ativado:

```bash
RUN_POSTGRES_TESTS=true pytest tests/test_postgres_integration.py
```
