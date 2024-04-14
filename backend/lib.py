import base64
import anthropic
import re
import asyncio
import requests
import json
import os
from dotenv import load_dotenv
import fal_client
import uuid


load_dotenv()


anthropic_client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))


def generate_image_with_prompt(prompt):
    """
    Submits a request to the FAL AI service to generate an image based on a textual prompt,
    without requiring an image URL.

    Parameters:
    - prompt (str): The textual description of the image to be generated.

    Returns:
    - The result of the image generation request.
    """
    handler = fal_client.submit(
        "fal-ai/fast-turbo-diffusion",
        arguments={
            "model_name": "stabilityai/sdxl-turbo",
            "prompt": prompt,
            "negative_prompt": "cartoon, illustration, animation. face. male, female, hands, body, signs, text",
            "image_size": "square",
            "num_inference_steps": 2,
            "guidance_scale": 1,
            "sync_mode": True,
            "num_images": 1,
            "enable_safety_checker": True,
            "expand_prompt": True
        },
    )
    log_index = 0
    for event in handler.iter_events(with_logs=True):
        if isinstance(event, fal_client.InProgress):
            new_logs = event.logs[log_index:]
            for log in new_logs:
                print(log["message"])
            log_index = len(event.logs)

    result = handler.get()
    print(f"generated image for {prompt}")
    return result


def save_image_from_response_and_return_url(response_data):
    """
    Saves an image from the base64 encoded string in the response data to a file and returns the URL.

    Parameters:
    - response_data (dict): The response data containing the image in base64 format.

    Returns:
    - str: The URL of the saved image.
    """
    # Ensure the media directory exists
    media_dir = "/var/www/media"
    os.makedirs(media_dir, exist_ok=True)

    # Extract the base64 image data
    image_data_base64 = response_data["images"][0]["url"].split(",")[1]

    # Decode the base64 string to binary data
    image_data = base64.b64decode(image_data_base64)

    # Generate a random filename
    filename = f"{uuid.uuid4()}.jpeg"

    # Construct the full path for the image file
    file_path = os.path.join(media_dir, filename)

    # Write the binary data to a file
    with open(file_path, "wb") as image_file:
        image_file.write(image_data)

    # Construct the URL
    image_url = f"https://interlinked.auto.movie/media/{filename}"

    print(f"Image saved to {file_path}")
    return image_url


def call_haiku_with_prompt(prompt):
    message = anthropic_client.messages.create(
        model="claude-3-haiku-20240307",
        system="You are an expert AI translation assistant, creating captions and images for interactive video conversations. You help everyone understand.",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ],
            }
        ],
    )

    answer = message.content[0].text.strip().lower()

    return answer


def call_fireworks_api(user_message):
    api_key = os.getenv("FIREWORKS_API_KEY")
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
    print(text)
    print(raw_answer)
    answer = extract_from_triple_backticks(
        raw_answer)[0].strip().lstrip("\"").rstrip("\"")
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
    raw_answer = call_haiku_with_prompt(prompt)
    answer = extract_from_triple_backticks(raw_answer)[0].strip()
    return answer


def extract_proper_nouns(prompt):
    prompt = f"""
    Extract all proper nouns from the following text:
    
    {prompt}
    
    Return the proper nouns in a comma separated list. Keep it brief.
    """
    answer = call_haiku_with_prompt(prompt)
    try:
        return answer.split(",")
    except Exception as e:
        print(e)
        return []


async def generate_images(prompt):
    """
    For each prompt, extracts proper nouns, generates an image for each proper noun, and returns an array of dictionaries
    with the proper noun and the corresponding image URL.

    Parameters:
    - prompts (List[str]): A list of textual prompts.

    Returns:
    - List[Dict[str, str]]: An array of dictionaries with proper nouns and their corresponding image URLs.
    """
    results = []

    # Extract proper nouns from the prompt
    proper_nouns = extract_proper_nouns(prompt)

    for noun in proper_nouns:
        print("generating image for", noun)
        # Generate an image for each proper noun
        image_response = generate_image_with_prompt(noun)
        if image_response:
            # Save the image and get its URL
            image_url = save_image_from_response_and_return_url(
                image_response)
            results.append({"proper_noun": noun, "image_url": image_url})
        else:
            print(f"Failed to generate image for {noun}")

    return results

if __name__ == "__main__":
    user_message = "I am awesome."
    answer = asyncio.run(translate_text("english", "spanish", user_message))
    print(answer)
