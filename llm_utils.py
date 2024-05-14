import time 
import dirtyjson 
import json
import llm_gateway

def get_json_response_from_llm(prompt,temperature=0.1):
    max_attempts = 3
    current_attempt = 0
    while current_attempt < max_attempts:
        current_attempt += 1
        status,response = llm_gateway.generate(prompt,temperature=temperature)
        if not status:
            print("Failed to Send Request to LLM: %s " % response)
            time.sleep(10)
            continue
        try:
            # nudge the response to json for leading issues.
            response = response[response.find("{"):]
            return dirtyjson.loads(response)
        except Exception as e:
            print("Failed to Get JSON - Reattempting...")
            print(response)
            time.sleep(5)
            continue
    print("Max Retries Exceeded - Giving Up...")
    return {}

def get_response_from_llm(prompt,temperature=0.1):
    max_attempts = 20
    current_attempt = 0
    while current_attempt < max_attempts:
        current_attempt += 1
        status,response = llm_gateway.generate(prompt,temperature=temperature)
        if not status:
            print("Failed to Send Request to LLM: %s " % response)
            time.sleep(10)
            continue
        return response
    print("Max Retries Exceeded - Giving Up...")
    return ""

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