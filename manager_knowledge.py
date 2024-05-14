import os 
import time 
import re
import json

from slack_sdk import WebClient

import config
import db_manager



# -- WebClient Stuff

def is_message_help_request(message_text):
    if not config.WORKFLOW_MESSAGE_PREAMBLE in message_text:
        return False
    return True

def is_request_complete(messages):
    for message in messages:
        message_text = message['text']
        if config.WORKFLOW_COMPLETE_MESSAGE in message_text and message['user'] == config.TARGET_BOT_ID:
            return True
    return False

def get_userid_from_message(message_text):
    return re.search(r"<@(U\w+)>", message_text).group(1)

def knowledge_manager_routine():
    print("Starting Knowledge Manager")
    db = db_manager.DBManager(config.DATABASE_URL)
    channel_id = config.TARGET_CHANNEL_ID
    
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    while config.SERVICE_RUNNING:
        learning_ids = db.list_learning_ids()       
        # iterates over the conversations table and looks for any new entries to put into the assistant table for AI workflows
        conversations = db.get_all_conversations()
        for conversation in conversations:
            conversation_id = conversation.id
            # If a conversation is already in the learning table, then we don't care about it here.
            if conversation_id in learning_ids:
                continue

            # Check if the conversation is a help request
            messages = json.loads(conversation.messages,strict=False)
            if not is_message_help_request(messages[0]['text']):
                continue
            # Check if the conversation is incomplete
            if not is_request_complete(messages):
                continue

            db.add_learning(conversation_id,"","","","")
            print(f"New Learning Request {conversation_id} - Added to DB")

        # Add all APPROVED learning entries to the knowledge table
        entries = db.get_learning_entries_with_state("APPROVED")
        for entry in entries:
            db.add_knowledge(entry.question, entry.answer, entry.nuance, entry.conversation_id)
            db.update_learning(entry.conversation_id, state="ADDED")
            print(f"Learning Request {entry.conversation_id} - Added to Knowledge DB")

        time.sleep(config.LEARNING_INTERVAL)

if __name__ == "__main__":
    knowledge_manager_routine()