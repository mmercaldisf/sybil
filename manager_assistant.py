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

def is_message_help_request(message_text):
    if not config.WORKFLOW_MESSAGE_PREAMBLE in message_text:
        return False
    return True

def is_request_complete(messages):
    for message in messages:
        message_text = message['text']
        if config.WORKFLOW_COMPLETE_MESSAGE in message_text and message['user'] == config.WORKFLOW_BOT_ID:
            return True
    return False

def get_userid_from_message(message_text):
    return re.search(r"<@(U\w+)>", message_text).group(1)

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
            if not is_message_help_request(messages[0]['text']):
                continue
            # Check if the conversation is complete
            if is_request_complete(messages):
                continue
            user_id = get_userid_from_message(messages[0]['text'])
            db.add_assistant(conversation_id,user_id,"","","")
            print(f"New Assistant Request {conversation_id} - Added to DB")

        # Get all assistant entries with state READY
        answers = db.get_assistant_entries_with_state("ANSWERED")
        for answer in answers:            
            # Get the answer
            answer_text = answer.response
            # Send the answer
            send_bot_message(client, channel_id, answer_text, thread_ts=answer.conversation_id)
            send_bot_block_message(client, channel_id, config.QUESTION_PROMPT_MESSAGE, YES_NO_BLOCK, thread_ts=answer.conversation_id)
            # Update the assistant entry
            db.update_assistant(answer.conversation_id, state="RESPONDED")
            print(f"Assistant Request {answer.conversation_id} - Answer Sent")

        time.sleep(config.ASSISTANT_INTERVAL)

if __name__ == "__main__":
    assistant_manager_routine()