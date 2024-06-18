import os
import time 
import dirtyjson 
import json
import llm_gateway

def clean_json_output(output):
    output = output.strip()
    if output.startswith("```json"):
        output = output[7:]
    if output.endswith("```"):
        output = output[:-3]
    cleaned_output = output.strip()

    try:
        json_data = dirtyjson.loads(cleaned_output)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return cleaned_output

    def clean_json(data):
        if isinstance(data, dict):
            return {key: clean_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [clean_json(item) for item in data]
        elif isinstance(data, str):
            return "" if data.lower() in ["unknown", "na", "null"] else data
        else:
            return data

    cleaned_json_data = clean_json(json_data)
    #cleaned_output = json.dumps(cleaned_json_data, ensure_ascii=False)

    return cleaned_json_data

def get_json_response_from_llm(prompt,temperature=0.1,fields=[]):
    max_attempts = 50
    current_attempt = 0
    while current_attempt < max_attempts:    
        current_attempt +=1
        response = llm_gateway.generate(prompt,temperature=temperature)
        if not response:
            continue
        try:
            response = clean_json_output(response)
            for field in fields:
                if response.get(field) == None:
                    print(f"Failed to Get Response with Field: {field} - Retrying...")
                    print(response)
                    time.sleep(5)
                    continue
            return response
        
        except Exception as e:
            print("Failed to Get JSON - Reattempting...")
            print(response)

            time.sleep(5)
            continue
    print("Max Retries Exceeded - Giving Up...")
    return {}


def get_response_from_llm(prompt,temperature=0.1):
    response = llm_gateway.generate(prompt,temperature=temperature)
    if not response:
        return ""
    return response

from openai import OpenAI

def prompt_ai(prompt, system_message="",json_format=True):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    messages = []
    response_format = None
    if json_format:
        response_format = { "type": "json_object" }
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": prompt})
    completion = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=messages,
    response_format=response_format
    )

    if json_format:
        return json.loads(completion.choices[0].message.content,strict=False)
    return completion.choices[0].message.content