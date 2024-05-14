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
TARGET_CHANNEL_ID="C073RQ40WE5"
# Set this to the bot ID of the workflow bot that is creating requests.
TARGET_BOT_ID="B073FJB30H2"


# Refresh Frequency of the Various Modules (in seconds)
SCRAPER_INTERVAL = 120
ASSISTANT_INTERVAL = 90
LEARNING_INTERVAL = 600
LEARNING_AGENT_INTERVAL = 90
ASSISTANT_AGENT_INTERVAL = 90


# Set the Message Detection Items for the Workflow
WORKFLOW_MESSAGE_PREAMBLE = "*Name of Submitter:*"
WORKFLOW_COMPLETE_MESSAGE = "Thank you for engaging with SA. Your request has now been completed."
QUESTION_PROMPT_MESSAGE = "Does this solve your request?"
REJECT_MESSAGE = "Understood, I'll defer to the appropriate team member, in the meantime, could you please provide feedback to help me better improve my ability to help in the future?"
APPROVE_MESSAGE = "Thank you for your feedback!"
FEEDBACK_THANKYOU_MESSAGE = "Thank you for your feedback! A member of the team will be in contact shortly."
NOT_AUTHORIZED_MESSAGE = "Sorry, you're not authorized to perform this action."


# -- Methods for Conversation Templates - Heavily Dependent on the Workflow

def extract_help_request_info(message_text):
    try:
        # Extract the user's name
        user_name = re.search(r"\*Name of Submitter:\* <@(U\w+)>", message_text).group(1)
        #print(user_name)
        # Extract the user's cloud
        cloud = re.search(r"\*GUS Cloud:\* (.*)", message_text).group(1)
        #print(cloud)
        # Extract the user's team
        team = re.search(r"\*GUS Team:\* (.*)", message_text).group(1)
        #print(team)
        component_name = re.search(r"\*Component Name \(e.g. USD Service/Feature\):\* (.*)", message_text).group(1)
        #print(component_name)
        product_tag = re.search(r"\*Product Tag:\* (.*)", message_text).group(1)
        #print(product_tag)
        # Extract the user's request
        summary = re.search(r"\*Please summarize your issue or question:\* (.*)", message_text).group(1)
        #print(summary)
        # Extract the "I need Help with: Security Guidance" line
        help_type = re.search(r"\*I need advice related to:\* (.*)", message_text).group(1)
        #print(help_type)
        description = re.search(r"\*Description of Guidance Needed \(including links to documents\):\* ((.|\n)*)", message_text).group(1)
        #print(description)
        help_request = {
            'username': user_name,
            'cloud': cloud,
            'team': team,
            'component_name': component_name,
            'product_tag': product_tag,
            'help_type': help_type,
            'summary': summary,
            'description': description
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
            if not 'user' in message:
                user_id = message['bot_id']
            else:
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
    response += f"Component Name: {transcript['request_form']['component_name']}\n"
    response += f"Product Tag: {transcript['request_form']['product_tag']}\n"
    response += f"Request Type: {transcript['request_form']['help_type']}\n\n"
    response += f"Summary: {transcript['request_form']['summary']}\n\n"
    response += f"Description: {transcript['request_form']['description']}\n\n"
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
        if not 'user' in message:
            if not 'bot_id' in message:
                return ""
        if not 'user' in message:
            user_id = message['bot_id']
        else:
            user_id = message['user']
        if user_id not in user_info:
            continue
        contributors.add(user_id)
    
    for user_id in contributors:
        info_str+= render_user_info(user_info, user_id) + "\n"
    return info_str