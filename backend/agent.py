import os
import json
import google.generativeai as genai
from groq import Groq, RateLimitError
from ddgs import DDGS
from dotenv import load_dotenv
from .logging_config import setup_logging

load_dotenv()
logger = setup_logging()

# --- Ferramenta de Busca ---
def buscar_noticias_seguranca_df(query: str):
    """
    Busca notícias recentes sobre segurança pública e forças policiais no Distrito Federal.
    """
    logger.info(f"Buscando por '{query} Distrito Federal'")
    with DDGS() as ddgs:
        results = list(ddgs.text(f"{query} Distrito Federal", region="br-pt", safesearch="off", max_results=5))

        if not results:
            return "Nenhuma notícia encontrada para esta busca."

        noticias_formatadas = ""
        for i, r in enumerate(results, 1):
            noticias_formatadas += f"[{i}] Título: {r['title']}\nLink: {r['href']}\nResumo: {r['body']}\n\n"

        return noticias_formatadas

# Configuração da Ferramenta para o Groq (OpenAI format)
tools = [
    {
        "type": "function",
        "function": {
            "name": "buscar_noticias_seguranca_df",
            "description": "Busca notícias recentes sobre segurança pública no DF",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "O termo de busca (ex: 'operação policial', 'crimes')"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# --- Fallback: Gemini ---
def get_gemini_response(user_query, context_data=None):
    """Fallback using Google Gemini"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY missing for fallback.")
        return "Erro: Falha no Groq e chave do Gemini não encontrada."

    logger.info("⚠️ Activando FALBACK para Gemini Flash...")
    genai.configure(api_key=api_key)
    # Mapping 'gemini-flash-lite-latest' request to stable 'gemini-1.5-flash'
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""Você é um Agente Pesquisador de Segurança Pública do DF. 
    O sistema principal falhou, você está operando em modo de contingência.
    
    Pergunta do usuário: {user_query}
    
    Se houver dados de contexto de uma busca anterior:
    {context_data if context_data else "Sem contexto adicional."}
    
    Responda de forma concisa e útil.
    """
    
    try:
        response = model.generate_content(prompt)
        return f"[Mojo Fallback - Gemini] {response.text}"
    except Exception as e:
        logger.error(f"Gemini fallback failed: {e}")
        return "Erro crítico: Ambos os sistemas de IA (Groq e Gemini) falharam."

# --- Lógica do Agente Principal ---
def get_agent_response(user_query, api_key=None):
    """
    Inicializa o modelo Groq com Fallback para Gemini.
    """
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        return "Erro: GROQ_API_KEY não encontrada."

    client = Groq(api_key=key)
    model_name = "llama-3.3-70b-versatile"
    
    instrucoes = """Você é um Agente Pesquisador de Segurança Pública do DF.
    Use a função de busca para encontrar fatos reais.
    Responda sempre em tópicos, citando os links das fontes.
    Se encontrar notícias relevantes, sugira que elas sejam salvas no banco de dados.
    """

    messages = [
        {"role": "system", "content": instrucoes},
        {"role": "user", "content": user_query}
    ]

    try:
        # 1. Primeira chamada ao modelo
        completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=4096
        )
        
        response_message = completion.choices[0].message
        tool_calls = response_message.tool_calls

        # 2. Se houver chamada de ferramentas
        if tool_calls:
            messages.append(response_message)
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                
                if function_name == "buscar_noticias_seguranca_df":
                    function_args = json.loads(tool_call.function.arguments)
                    function_response = buscar_noticias_seguranca_df(
                        query=function_args.get("query")
                    )
                    
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        }
                    )
            
            second_response = client.chat.completions.create(
                model=model_name,
                messages=messages
            )
            return second_response.choices[0].message.content
        
        return response_message.content

    except (RateLimitError, Exception) as e:
        logger.warning(f"Groq Error ({type(e).__name__}): {e}. Switching to Fallback.")
        # Se falhar, tentamos o Gemini. 
        # Nota: Se a falha for DEPOIS de buscar ferramentas (contexto), perdemos o contexto na implementação simples.
        # Melhor seria passar o histórico, mas para fallback simples, passamos a query.
        return get_gemini_response(user_query)
