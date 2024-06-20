# Slack Scraper Module for a Given Bot Workflow
import os 
import time 
import re
import json
import logging

from slack_sdk import WebClient

import config
import db_manager


YES_NO_BLOCK = [
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": config.QUESTION_PROMPT_MESSAGE
        }
    },
    {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Yes"
                },
                "value": "yes",
                "action_id": "yes_button"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "No"
                },
                "value": "no",
                "action_id": "no_button"
            }
        ]
    }
]

def send_bot_reaction(client, channel_id, thread_ts, reaction):
    # Add a reaction to the parent message in the thread
    try:
        client.reactions_add(
            channel=channel_id,
            timestamp=thread_ts,  # This is the ID of the parent message
            name=reaction
        )
    except Exception as e:
        print(f"Unable to Add Reaction to Response: {e}")
        pass

def send_bot_message(client, channel_id, message_text, thread_ts=None):
    response = client.chat_postMessage(channel=channel_id, text=message_text, thread_ts=thread_ts)
    if not response["ok"]:
        logging.error(f"Error sending bot message: {response['error']}")
        return None
    return response


def send_bot_block_message(client, channel_id, message_text, blocks, thread_ts=None):
    response = client.chat_postMessage(channel=channel_id, text=message_text, blocks=blocks, thread_ts=thread_ts)
    if not response["ok"]:
        logging.error(f"Error sending bot message: {response['error']}")
        return None
    return response

# -- WebClient Stuff

def is_message_help_request(message_content):
    if not 'blocks' in message_content:
        return False
    if not 'text' in message_content['blocks'][0]:
        return False
    message_text = message_content["blocks"][0]["text"]["text"]
    if not config.WORKFLOW_MESSAGE_PREAMBLE in message_text:
        return False
    return True



def get_userid_from_message(message_content):
    if not 'blocks' in message_content:
        return ""
    if not 'text' in message_content['blocks'][0]:
        return ""
    message_text = message_content["blocks"][0]["text"]["text"]
    try:
        user_id = re.search(r"<@(U\w+)>", message_text).group(1)
        return user_id
    except:
        pass
    return ""
    

def assistant_manager_routine():
    print("Starting Assistant Manager")
    db = db_manager.DBManager(config.DATABASE_URL)
    channel_id = config.TARGET_CHANNEL_ID
    
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    while config.SERVICE_RUNNING:
        learning_ids = db.list_learning_ids()
        assistant_ids = db.list_assistant_ids()
        # iterates over the conversations table and looks for any new entries to put into the assistant table for AI workflows
        conversations = db.get_all_conversations()
        proc_count = 0
        for conversation in conversations:
            conversation_id = conversation.id
            # If a conversation is already in the learning table, then it was completed and we don't care about it here.
            if conversation_id in learning_ids:
                continue
            # We also don't care about conversations that are already in the assistant table
            if conversation_id in assistant_ids:
                continue
            # Check if the conversation is a help request
            messages = json.loads(conversation.messages,strict=False)
            if not is_message_help_request(messages[0]):
                continue
            # Check if the conversation is complete
            if config.is_request_complete(messages[0]):
                continue
            user_id = get_userid_from_message(messages[0])
            # We will skip the request if someone has claimed the message already.
            if config.is_request_claimed(messages[0]):
                db.add_assistant(conversation_id,user_id,"","","SKIPPED")
            else:
                db.add_assistant(conversation_id,user_id,"","","")
                print(f"New Assistant Request {conversation_id} - Added to DB")
            proc_count += 1

        # Get all assistant entries with state READY
        answers = db.get_assistant_entries_with_state("ANSWERED")
        if config.ACTIVE_AGENT_MODE == True:
            for answer in answers:            
                # Get the answer
                answer_text = answer.response
                # Send the answer
                send_bot_message(client, channel_id, answer_text + "\n\n" + config.ANSWER_DISCLAIMER, thread_ts=answer.conversation_id)
                send_bot_block_message(client, channel_id, config.QUESTION_PROMPT_MESSAGE, YES_NO_BLOCK, thread_ts=answer.conversation_id)
                send_bot_reaction(client,channel_id,answer.conversation_id,"einstein-gpt-sparkle")
                # Update the assistant entry
                db.update_assistant(answer.conversation_id, state="RESPONDED")
                print(f"Assistant Request {answer.conversation_id} - Answer Sent")
        print(f"Processed {proc_count} - Sleeping...")
        time.sleep(config.ASSISTANT_INTERVAL)

if __name__ == "__main__":
    config.SERVICE_RUNNING = True    
    assistant_manager_routine()