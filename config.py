# Primary Configuration Module for Sybil
import os
import re
from dotenv import load_dotenv

# Service Running
SERVICE_RUNNING = False

# Set the Database URL for your chosen Backend
WORKSPACE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(WORKSPACE_PATH, 'sybil.db')}"

REVIEWER_HOST = "127.0.0.1"
REVIEWER_PORT = 5000

# Set the path for your environment file
ENV_PATH = os.path.join(WORKSPACE_PATH, 'env.conf')
load_dotenv(ENV_PATH)

# Set this to the channel ID of the channel you want to monitor
TARGET_CHANNEL_ID="C072TKUENDT"
# Set this to the bot ID of the workflow bot that is creating requests.
TARGET_BOT_ID="U06C12U3Y3Y"


# Refresh Frequency of the Various Modules (in seconds)
SCRAPER_INTERVAL = 300
ASSISTANT_INTERVAL = 300
LEARNING_INTERVAL = 600
LEARNING_AGENT_INTERVAL = 600
ASSISTANT_AGENT_INTERVAL = 600


# Set the Message Detection Items for the Workflow
WORKFLOW_MESSAGE_PREAMBLE = "**QA REQUEST**"
WORKFLOW_COMPLETE_MESSAGE = "Thank you for Stopping By, Your Task is Now Closed!"
QUESTION_PROMPT_MESSAGE = "Does this solve your request?"
REJECT_MESSAGE = "Understood, I'll defer to the appropriate team member, in the meantime, could you please provide feedback to help me better improve my ability to help in the future?"
APPROVE_MESSAGE = "Thank you for your feedback!"
FEEDBACK_THANKYOU_MESSAGE = "Thank you for your feedback! A member of the team will be in contact shortly."
NOT_AUTHORIZED_MESSAGE = "Sorry, you're not authorized to perform this action."


# -- Methods for Conversation Templates - Heavily Dependent on the Workflow

def extract_help_request_info(message_text):
    try:
        # Extract the user's name
        user_name = re.search(r"Name: <@(U\w+)>", message_text).group(1)
        # Extract the user's cloud
        cloud = re.search(r"Cloud: (.+)", message_text).group(1)
        # Extract the user's team
        team = re.search(r"Team: (.+)", message_text).group(1)
        # Extract the user's request
        request = re.search(r"Request: (.+)", message_text).group(1)
        # Extract the "I need Help with: Security Guidance" line
        help_type = re.search(r"I need Help with: (.+)", message_text).group(1)
        
        help_request = {
            'username': user_name,
            'cloud': cloud,
            'team': team,
            'help_type': help_type,
            'request': request
        }
    except Exception as e:
        print(f"Error extracting help request info: {e}")
        help_request = None
    return help_request

def create_message_transcript(conversation):
    # Extract Content from the First Message
    request_form = extract_help_request_info(conversation[0]['text'])

    transcript = []
    if len(conversation) > 1:
        for message in conversation[1:]:
            message_text = message['text']
            user_id = message['user']
            message_entry = f"{user_id}: {message_text}"
            transcript.append(message_entry)
    message_transcript = {
        "request_form": request_form,
        "additional_messages": transcript,
    }
    return message_transcript

def render_transcript(transcript):
    response = "---\n"
    response += "Request Form: \n"
    response += f"User: {transcript['request_form']['username']}\n"
    response += f"Cloud: {transcript['request_form']['cloud']}\n"
    response += f"Team: {transcript['request_form']['team']}\n"
    response += f"Help Type: {transcript['request_form']['help_type']}\n"
    response += f"Request: {transcript['request_form']['request']}\n\n"
    response += "Additional Messages: \n"
    for message in transcript['additional_messages']:
        response += message + "\n"
    response += "---"
    return response

def render_user_info(user_info, user_id):

    user = user_info[user_id]

    response = "----\n"
    response += f"User ID: {user_id}\n"
    response += f"Name: {user['name']}\n"
    response += f"Real Name: {user['real_name']}\n"
    response += f"Title: {user['profile']['title']}\n"
    return response


def get_full_user_infos(transcript, conv_info, user_info):
    info_str = ""
    contributors = set()
    contributors.add(transcript['request_form']['username'])
    for message in conv_info:
        user_id = message['user']
        if user_id not in user_info:
            continue
        contributors.add(user_id)
    
    for user_id in contributors:
        info_str+= render_user_info(user_info, user_id) + "\n"
    return info_str