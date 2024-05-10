import hashlib
import requests
import time
import aiohttp
import asyncio
from gtts import gTTS
import os

# Cache dictionary for storing OCR results
cache = {}

# Function to compute file hash
def compute_file_hash(filename):
    with open(filename, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    return file_hash

# Caching for OCR.space
def ocr_space_file_with_cache(filename, api_key):
    file_hash = compute_file_hash(filename)
    if file_hash in cache:
        print("Returning cached result")
        return cache[file_hash]

    result = ocr_space_file(filename, api_key)
    cache[file_hash] = result
    return result

# Basic OCR.space function without modifications
def ocr_space_file(filename, api_key):
    url = 'https://api.ocr.space/parse/image'
    payload = {'isOverlayRequired': False, 'apikey': api_key, 'language': 'eng'}
    with open(filename, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files, data=payload)
    return response.json()

def clean_text(text):
    # Replace unwanted escape characters and excessive whitespace
    cleaned_text = text.replace('\r', ' ').replace('\n', ' ').strip()
    return cleaned_text

# Function to extract a concise answer based on the presence of a summary or last four sentences
def extract_concise_answer(response):
    full_text = response['choices'][0]['text'].strip()
    sentences = full_text.split('.')
    summary_keywords = ["In summary", "To summarize", "In conclusion", "Summary:"]
    summary_text = None
    for keyword in summary_keywords:
        if keyword.lower() in full_text.lower():
            summary_start = full_text.lower().find(keyword.lower())
            summary_text = full_text[summary_start:]
            break
    if summary_text:
        return ' '.join(summary_text.split('.')[-4:])  # Return last four sentences of summary
    elif len(sentences) >= 4:
        return ' '.join(sentences[-4:])  # Return the last four sentences
    else:
        return full_text  # Return full text if less than four sentences

# Asynchronous call to OpenAI
async def ask_chatgpt_async(question, openai_api_key):
    url = 'https://api.openai.com/v1/completions'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {openai_api_key}'}
    payload = {'model': 'gpt-3.5-turbo', 'prompt': question, 'max_tokens': 150}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            result = await response.json()
            print("API Response:", result)  # Debug: Print the raw API response
            if 'choices' in result:
                return extract_concise_answer(result)
            else:
                return "Error: No choices in response. Check API call."

# Function to speak text using gTTS and play it
def speak_text(text):
    tts = gTTS(text=text, lang='en')
    tts.save('response.mp3')  # Save the spoken text to an mp3 file
    os.system('mpg123 -q response.mp3')  # Play the mp3 file using mpg123

# Main function to orchestrate the calls
def main(filename, question, ocr_api_key, openai_api_key):
    ocr_result = ocr_space_file_with_cache(filename, ocr_api_key)
    parsed_text = clean_text(ocr_result['ParsedResults'][0].get('ParsedText', ''))
    loop = asyncio.get_event_loop()
    concise_response = loop.run_until_complete(ask_chatgpt_async(parsed_text, openai_api_key))
    print("Concise ChatGPT Response:", concise_response)
    speak_text(concise_response)  # Speak the response

# Example usage
if __name__ == "__main__":
    filename = '/home/jasalat/text.jpg'
    question = "Answer this question, and end your response with a short summary of what you said. When you start this summary use words like in conclusion, or summarize, and keep these summaries 4 sentences or less."
    ocr_api_key = "Your_OCR_API_Key"
    openai_api_key = "Your_OpenAI_API_Key"
    main(filename, question, ocr_api_key, openai_api_key)
