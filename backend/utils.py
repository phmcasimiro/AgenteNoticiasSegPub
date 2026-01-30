from datetime import datetime

# Função que retorna a data atual formatada como string.
def get_current_date_str(): 
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# Função para formatação de lista de notícias para exibição simples
def format_news_for_display(news_list): 
    return "\n\n".join([f"**{n['title']}**\n{n['link']}" for n in news_list])
