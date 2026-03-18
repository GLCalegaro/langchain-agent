from langchain.tools import BaseTool, tool

@tool
def suggest_outfit(user_style: str) -> str:
    """Sugere uma roupa baseada no estilo do usuário."""
    if "casual" in user_style:
        return "Jeans, camiseta branca e tênis branco."
    return "Um vestido elegante com saltos."

@tool
def late_delivery(user_complain: str) -> str:
    """Ajuda com pedido atrasado calculando o tempo de atraso ou compensação."""

    if user_complain == "pedido não entregue no prazo":
        return "Lamentamos o atraso. Peça o número do pedido e depois de confirmar, diga que o cliente pode solicitar uma devolução gratuita dentro de 7 dias úteis após a data de entrega através do app em > Minha Conta > Meus Pedidos > Devolução > Forneça as informações solicitadas e clique em Enviar. Após a solicitação, o reembolso será processado em até 10 dias úteis."
    elif user_complain == "Pedido consta como entregue mas não foi recebido.":
        return "Neste caso, entraremos em contato com a transportadora responsável pela entrega pois é ela quem atualiza essa informação e nos faz o repasse. Pode ser que o entregador esteja na rota de entrega e tenha dado a baixa por engano, ou até mesmo o pedido ser entregue para algum vizinho próximo ou portaria.  Nosso Núcleo de atendimento vai te ajudar a solucionar este problema, abrindo uma solicitação para que o contato com o setor responsável e a transportadora ocorra. Peça para o cliente que aguarde o contato do nosso Núcleo de Atendimento em até 48 horas após este atendimento."
    return "Vou direcioná-lo ao nosso Núcleo de Atendimento."


TOOLS: list[BaseTool] = [suggest_outfit, late_delivery]
TOOLS_BY_NAME: dict[str, BaseTool] = {tool.name: tool for tool in TOOLS}