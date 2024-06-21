# Primary Configuration Module for Sybil
import os
import re
from dotenv import load_dotenv

# Service Running
SERVICE_RUNNING = False

# Set the Database URL for your chosen Backend
WORKSPACE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if os.environ.get("DB_ROOT_PATH",None):
    WORKSPACE_PATH = os.path.abspath(os.environ.get("DB_ROOT_PATH"))

# Set the path for your environment file
ENV_PATH = os.path.join(WORKSPACE_PATH, 'env.conf')

# Override fallback config path if specified in envar.
if os.environ.get("SYBIL_CONFIG"):
    ENV_PATH = os.path.abspath(os.environ.get("SYBIL_CONFIG"))
load_dotenv(ENV_PATH)

# Set this to the channel ID of the channel you want to monitor
TARGET_CHANNEL_ID= os.environ.get("TARGET_CHANNEL_ID","fff")
# Set this to the bot ID of the workflow bot that is creating requests.
TARGET_BOT_ID=os.environ.get("TARGET_WORKFLOW_ID","fff")



DB_FILENAME = f"{TARGET_CHANNEL_ID}.db"
DATABASE_URL = f"sqlite:///{os.path.join(WORKSPACE_PATH, DB_FILENAME)}"
print(f"Database is {DATABASE_URL}")
REVIEWER_HOST = "127.0.0.1"
REVIEWER_PORT = 5000


# Refresh Frequency of the Various Modules (in seconds)
SCRAPER_INTERVAL = 600
ASSISTANT_INTERVAL = 30
LEARNING_INTERVAL = 30
LEARNING_AGENT_INTERVAL = 30
ASSISTANT_AGENT_INTERVAL = 30

# Logic Flags
# -- This flag determines whether the bot will respond to messages in the channel if it has no knowledgebase content to reference
STRICT_ANSWERING_MODE = True

# -- This option allows agents to respond to channels - if disabled, agents will run, but only operate passively.
ACTIVE_AGENT_MODE = False
active_agent_value = os.environ.get("ACTIVE_AGENT_MODE",None)
if active_agent_value != None:
    try:
        active_agent_value = int(active_agent_value)
        if active_agent_value == 1:
            ACTIVE_AGENT_MODE = True
    except:
        pass

if ACTIVE_AGENT_MODE:
    print("WARNING: Agent is in Active Mode - Responses will be sent.")
else:
    print("INFO: Agent is in Passive Mode - No Responses will be sent.")

# Set the Message Detection Items for the Workflow
WORKFLOW_MESSAGE_PREAMBLE = "*Name of Submitter:*"
WORKFLOW_COMPLETE_MESSAGE = "Thank you for engaging with SA. Your request has now been completed."
WORKFLOW_COMPLETE_MESSAGE_OLD = "Engagement Complete!"
QUESTION_PROMPT_MESSAGE = "Does this solve your request?"
REJECT_MESSAGE = "Understood, I'll defer to the appropriate Security Assurance team member, in the meantime, could you please provide feedback to help me better improve my ability to help in the future?"
APPROVE_MESSAGE = "Thank you for your feedback!"
FEEDBACK_THANKYOU_MESSAGE = "Thank you for your feedback! A member of the Security Assurance team will be in contact shortly."
NOT_AUTHORIZED_MESSAGE = "Sorry, you're not authorized to perform this action."
ANSWER_DISCLAIMER="_This message was generated by artificial intelligence and may contain errors or inaccuracies._"

# -- Methods for Conversation Templates - Heavily Dependent on the Workflow
def extract_request_information(messages):
    request_info = {
        "username":"",
        "cloud":"",
        "team":"",
        "component_name":"",
        "product_tag":"",
        "help_type":"",
        "summary": "",
        "description":""
    }

    try:
        block = messages[0]['blocks'][0]["text"]["text"]
    except Exception as e:
        print("Failed to Extract Request Block From Message")
        return request_info
    
    try:
        request_info['username'] = re.search(r"\*Name of Submitter:\* <@([UW]\w+)>", block).group(1)
    except:
        pass
    

    try:
        request_info['cloud'] = re.search(r"\*GUS Cloud:\* (.*)", block).group(1)
    except:
        pass

    
    try:
        request_info['team'] = re.search(r"\*GUS Team:\* (.*)", block).group(1)
    except:
        pass

    try:
        request_info['component_name'] = re.search(r"\*Component Name \(e.g. USD Service/Feature\):\* (.*)", block).group(1)
    except:
        pass

    try:
        request_info['product_tag'] = re.search(r"\*Product Tag:\* (.*)", block).group(1)
    except:
        pass

    try:
        request_info['help_type'] = re.search(r"\*I need advice related to:\* (.*)", block).group(1)
    except:
        pass

    try:
        request_info['summary'] = re.search(r"\*Please summarize your issue or question:\* (.*)", block).group(1)
    except:
        pass

    if request_info['summary'] == "":
        try:
            request_info['summary'] = re.search(r"\*Summary of Question or Issue:\* (.*)", block).group(1)
        except:
            pass
    try:
        request_info['description'] = re.search(r"\*Description of Guidance Needed \(including links to documents\):\* ((.|\n)*)", block).group(1)
    except:
        pass

    return request_info

# Render the Request Information
def render_request(request_info):
    request_render = "Request Information:\n\n"
    request_render += f"User: {request_info['username']}\n"
    request_render += f"Cloud: {request_info['cloud']}\n"
    request_render += f"Team: {request_info['team']}\n"
    request_render += f"Component: {request_info['component_name']}\n"
    request_render += f"Product Tag: {request_info['product_tag']}\n"
    request_render += f"Topic: {request_info['help_type']}\n"
    request_render += f"Description: {request_info['summary']}\n"
    request_render += f"Details: {request_info['description']}\n"
    return request_render

def render_user(user_info):
    user_render = f"User ID: {user_info['id']}\n"
    user_render += f"Team ID: {user_info['team_id']}\n"
    user_render += f"Name: {user_info["profile"]["real_name"]}\n"
    user_render += f"Role: {user_info["profile"]["title"]}\n"
    return user_render

def generate_user_info(user_infos):
    render_userinfos = "User Information: \n---\n"
    for uid in user_infos.keys():
        info = user_infos[uid]
        render_userinfos += render_user(info)
        render_userinfos += "----\n"
    return render_userinfos+"\n\n"


# Take the Additional Messages And Write a sorted Message Transcript
def generate_chat_transcript(messages):
    if len(messages) < 2:
        return ""

    additional_message_content = "Request Chat Transcript: \n"
    replies = {}
    for msg in messages[1:]:
        if "subtype" in msg:
            continue        
        replies[msg['ts']] = {'user':msg.get("user","Unknown"),"text":msg["text"]}
    for ts in sorted(replies.keys()):
        cr = replies[ts]
        additional_message_content += f"{cr["user"]}: {cr["text"]}\n\n"
    return additional_message_content

COMPLETED_REACTIONS = ["white_check_mark", "checkmark"]
CLAIMED_REACTIONS = ["eyes"]

def get_message_reactions(message):
    reactions = []
    if not 'reactions' in message:
        return reactions
    for item in message['reactions']:
        reactions.append(item['name'])
    return reactions

def is_request_claimed(message):
    reactions = get_message_reactions(message)

    for cr in COMPLETED_REACTIONS:
        if cr in reactions:
            return True

    return False

def is_request_complete(message):
    reactions = get_message_reactions(message)

    for cr in COMPLETED_REACTIONS:
        if cr in reactions:
            return True

    return False