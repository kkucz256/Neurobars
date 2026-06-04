import os
from groq import Groq

def ask_llm_rag(context_lyrics, user_question):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    system_prompt = (
        "You are an uncompromising hip-hop expert, critic, and analyst. "
        "Your task is to answer the user's question basing ONLY on the provided song lyrics context. "
        "CRITICAL: You must write your entire response exclusively in English, regardless of the language of the question. "
        "If the context does not contain the answer, state clearly in English that the provided lyrics do not explain it. "
        "Keep your tone natural, sharp, hip-hop savvy, and concise."
    )
    
    user_content = f"CONTEXT (Song snippets):\n{context_lyrics}\n\nUSER QUESTION: {user_question}"
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error communicating with LLM: {str(e)}"
    
def generate_qdrant_query(user_question):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    system_prompt = (
        "You are a search query optimization engine for a vector database containing rap lyrics. "
        "Your only job is to convert a user's natural language question into a short, effective, "
        "semantic search phrase that will find the relevant verse in the database. "
        "CRITICAL: Output ONLY the final search phrase. Do not include quotes, explanations, introductory text, or punctuation."
    )
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Optimize this question into a vector search query: {user_question}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.0,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception:
        return user_question