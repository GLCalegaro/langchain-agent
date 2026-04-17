from langchain.tools import BaseTool, tool

@tool
def suggest_outfit(user_style: str) -> str:
    """Sugere uma roupa baseada no estilo do usuário."""
    if "casual" in user_style:
        return "Uma camiseta básica com jeans e tênis."
    return "Recomenda roupas e acessórios baseados no estilo, ocasião, clima e gênero.."

@tool
def late_delivery(user_complain: str) -> str:
    """Ajuda com pedido atrasado calculando o tempo de atraso ou compensação."""
    complain_lower = user_complain.lower()

    # Verifica se é reclamação sobre pedido não entregue no prazo
    if any(keyword in complain_lower for keyword in ["atraso", "atrasou", "atrasado", "não entregue", "prazo", "não chegou no prazo"]):
        return "Lamentamos o atraso. Peça o número do pedido e depois de confirmar, diga que o cliente pode solicitar uma devolução gratuita dentro de 7 dias úteis após a data de entrega através do app em > Minha Conta > Meus Pedidos > Devolução > Forneça as informações solicitadas e clique em Enviar. Após a solicitação, o reembolso será processado em até 10 dias úteis."
    
    # Verifica se é pedido que consta como entregue mas não foi recebido
    if any(keyword in complain_lower for keyword in ["entregue mas não recebi", "diz entregue", "consta entregue", "não chegou", "não recebi"]):
        return "Neste caso, entraremos em contato com a transportadora responsável pela entrega pois é ela quem atualiza essa informação e nos faz o repasse. Pode ser que o entregador esteja na rota de entrega e tenha dado a baixa por engano, ou até mesmo o pedido ser entregue para algum vizinho próximo ou portaria. Nosso Núcleo de atendimento vai te ajudar a solucionar este problema, abrindo uma solicitação para que o contato com o setor responsável e a transportadora ocorra. Peça para o cliente que aguarde o contato do nosso Núcleo de Atendimento em até 48 horas após este atendimento."
    
    return "Vou direcioná-lo ao nosso Núcleo de Atendimento."


TOOLS: list[BaseTool] = [suggest_outfit, late_delivery]
TOOLS_BY_NAME: dict[str, BaseTool] = {tool.name: tool for tool in TOOLS}