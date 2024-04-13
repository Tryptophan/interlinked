import re
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


async def add_emphasis(lang, text):
    prompt = f"""
    Your job is to translate sentence text in any lang provided to html and add emphasis along the way. Please use <p> tags. Enclose the whole fragment in triple backticks ```

    You do not have to add emphasis!
    
    Examples: 
    
    Lang: English
    Text: John is going to New York tomorrow.
    Emphasized HTML: 
    ```
    <p>John</p> <p>is</p> <p>going</p> <p>to</p> <p class="emphasis-1">New</p> <p class="emphasis-2">York</p> <p>tomorrow.</p>
    ```
    
    Lang: Hindi
    Text: राम दिल्ली में रहता है।
    Emphasized HTML: 
    ```
    <p class="emphasis-1">राम</p> <p class="emphasis-2">दिल्ली</p> <p>में</p> <p>रहता</p> <p>है।</p>
    ```
    
    Lang: Chinese
    Text: 我和李娜去北京旅游
    Emphasized HTML: 
    ```
    <p>我</p><p>和</p><p class="emphasis-2">李娜</p><p>去</p><p class="emphasis-1">北京</p><p>旅游。</p>
    ```
    
    Lang: English
    Text: Hello how are you?
    Emphasized HTML: 
    ```
    <p>Hello</p> <p>how</p> <p>are</p> <p>you?</p>
    ```
    
    Task: 
    
    Lang: {lang}
    Text: {text}
    Emphasized HTML: 
    
        
    
    """
    raw_answer = call_fireworks_api(prompt)
    answer = extract_from_triple_backticks(raw_answer)[0].strip()
    return answer


if __name__ == "__main__":
    user_message = "I am awesome."
    answer = asyncio.run(translate_text("english", "spanish", user_message))
    print(answer)
