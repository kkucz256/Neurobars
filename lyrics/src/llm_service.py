import os
from groq import Groq
import json

import json

def validate_hiphop_intent(query):
    from groq import Groq
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    system_prompt = (
        "You are a strict security guardrail API. Evaluate if the user query is about hip-hop music, rap culture, artists, or lyrics. "
        "If the query is unrelated (e.g., coding, general knowledge, tech, help, recipes, math), you MUST classify it as invalid. "
        "You must respond ONLY with a raw JSON object matching this schema: {\"valid\": true} or {\"valid\": false}. "
        "Do not include any chat formatting, markdown backticks, or explanations."
    )
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        raw_response = chat_completion.choices[0].message.content.strip()
        
        print(f"--- GUARDRAIL RAW RESPONSE: {raw_response} ---", flush=True)
        
        data = json.loads(raw_response)
        return bool(data.get("valid", False))
        
    except Exception as e:
        print(f"--- GUARDRAIL EXCEPTION: {str(e)} ---", flush=True)
        return True

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
    
def generate_lyrics_in_style(artist_name, topic, style_context):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    system_prompt = (
        f"You are the ghostwriter for the rapper {artist_name}. "
        "Your task is to write a brand new, highly creative rap verse (16 bars) in English based on the TOPIC provided by the user. "
        f"CRITICAL: You must perfectly mimic the rhyming style, flow, vocabulary, rhythm, and emotional vibe of {artist_name}. "
        "Use the provided STYLE CONTEXT as examples of how this artist writes. Do not copy lines directly, but match the essence. "
        "Output ONLY the lyrics of the new verse, formatted with line breaks. Do not include introductory text, explanations, or music notes."
    )
    
    user_content = f"STYLE CONTEXT (Original verses by {artist_name}):\n{style_context}\n\nTOPIC for the new verse: {topic}"
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating lyrics: {str(e)}"
    
def generate_quiz_riddle(lyrics_snippet):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    system_prompt = (
        "You are a hip-hop quiz master. Your job is to read the provided rap lyrics snippet and create a short, "
        "engaging riddle in English (2-3 sentences max) that describes the themes, style, vocabulary, or content of the lyrics, "
        "WITHOUT ever mentioning the artist's name, track title, or quoting large parts of the text directly. "
        "The riddle must help the user guess who wrote these bars based on their style and message. "
        "Output ONLY the final riddle text. No intro, no outro."
    )
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a riddle based on this lyrics snippet:\n{lyrics_snippet}"}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Could not generate a riddle: {str(e)}"
    
def ask_llm_without_context(user_question):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    system_prompt = (
        "You are an uncompromising hip-hop expert and critic. "
        "The local database did not provide matching song lyrics for this query. "
        "Answer the user's question using your vast, general real-world knowledge about hip-hop history and artists. "
        "CRITICAL: Write your entire response exclusively in English. Be concise, sharp, and savvy."
    )
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Error processing request without context: {str(e)}"