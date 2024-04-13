import asyncio
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()


def call_fireworks_api(user_message):
    api_key = os.getenv("FIREWORKS_API_KEY")
    print(api_key)
    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    payload = {
        "model": "accounts/fireworks/models/mixtral-8x7b-instruct",
        "max_tokens": 4096,
        "top_p": 1,
        "top_k": 40,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "temperature": 0.6,
        "messages": [
            {
                "role": "user",
                "content": user_message
            }
        ]
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    parsed_response = response.json()
    answer = parsed_response['choices'][0]['message']['content']

    return answer


import re

def extract_from_triple_backticks(text):
    """
    Extracts and returns all text blocks enclosed in triple backticks from the given text.
    
    Parameters:
    - text (str): The text from which to extract the enclosed blocks.
    
    Returns:
    - List[str]: A list of strings, each being a block of text that was enclosed in triple backticks.
    """
    pattern = r"```(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches

async def translate_text(from_lang, to_lang, text):
    prompt = f"""
    Translate the following text from {from_lang} to {to_lang}:
    
    {text}
    
    Return the translation inside triple backticks. If you have any notes, include them but outside the triple backticks.
    
    Example
    Text: I am a boy
    Translation:
    ```
    我是男孩
    ```
    
    Text: {text}
    Translation:
    """
    raw_answer = call_fireworks_api(prompt)
    answer = extract_from_triple_backticks(raw_answer)[0].strip()
    return answer


async def add_emphasis(text, lang):
    prompt = f"""
    Your job is to translate sentence text to html and add emphasis along the way.
    
    Examples: 
    
    Text: I visited the Great Wall yesterday.
    Answer: 
    
    {text}
    
    Return the text inside triple backticks.
    """
    raw_answer = call_fireworks_api(prompt)
    answer = extract_from_triple_backticks(raw_answer)[0]
    return answer


if __name__ == "__main__":
    user_message = "I am awesome."
    answer = asyncio.run(translate_text("english", "spanish", user_message))
    print(answer)
