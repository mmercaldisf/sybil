# Slack Scraper Module for a Given Bot Workflow
import os 
import time 
import re
import json

from slack_sdk import WebClient

import config
import db_manager

def check_for_changed_message(db, n_message):
    existing_message = db.get_conversation(n_message['ts'])
    if not existing_message:
        return True
    if not 'latest_reply' in n_message.keys():
        return False
    if existing_message.updated != n_message['latest_reply']:
        return True
    return False

def is_new_message(db, message_id):
    if db.get_conversation(message_id):
        return False
    return True


# Get all Top Level Messages from a User in a Channel
def fetch_all_top_level_messages_from_user(client, channel_id, user_id, timestamp_cutoff=None):
    messages = []
    cursor = None

    # Keep paginating as long as there's a next cursor
    while True:
        response = client.conversations_history(
            channel=channel_id,
            cursor=cursor,
            latest=timestamp_cutoff,
            limit=200  # Adjust the number of messages per API call (up to 1000)
        )
        if "messages" in response:
            rmsgs = response["messages"]
            for rmsg in rmsgs:
                if not "subtype" in rmsg:
                    if "bot_profile" in rmsg:
                        if rmsg["bot_profile"]["name"] == config.BOT_NAME:
                            messages.append(rmsg)
        # Slack uses a "response_metadata" object with a "next_cursor" to indicate more results
        cursor = response.get('response_metadata', {}).get('next_cursor')
        if not cursor:
            break

    return messages

def get_all_contributors(client, messages):
    contributors = {}
    for msg in messages:
        try:
            target_user = msg.get('user') or msg.get('bot_id')
            info = client.users_info(user=target_user)
            user_info = info.get('user') or info.get('bot_id')
            contributors[target_user] = user_info
            # We also have to parse the message text for any mentions and include those too.
            mentions = re.findall(r"<@([UW]\w+)>", msg['text'])
            for mention in mentions:
                if mention not in contributors:
                    try:
                        info = client.users_info(user=mention)
                        user_info = info.get('user') or info.get('bot_id')
                        contributors[mention] = user_info
                    except:
                        pass
        except:
            continue        
    return contributors

def fetch_all_thread_messages(client, channel_id, parent_ts):
    messages = []
    cursor = None

    # Keep paginating as long as there's a next cursor
    max_attempts = 100
    current_attempts = 0

    while True:
        try:
            response = client.conversations_replies(
                channel=channel_id,
                ts=parent_ts,
                cursor=cursor,
                limit=200  # Adjust the number of messages per API call (up to 1000)
            )
        except:
            current_attempts+=1
            if current_attempts >= max_attempts:
                break
            time.sleep(5)
            continue
        messages.extend(response['messages'])

        # Slack uses a "response_metadata" object with a "next_cursor" to indicate more results
        cursor = response.get('response_metadata', {}).get('next_cursor')
        if not cursor:
            break
    return messages

def channel_manager_routine():
    print("Starting Channel Manager")
    db = db_manager.DBManager(config.DATABASE_URL)
    channel_id = config.TARGET_CHANNEL_ID
    bot_id = config.TARGET_BOT_ID
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    while config.SERVICE_RUNNING:
        # Get All Top Level Messages
        messages = fetch_all_top_level_messages_from_user(client, channel_id, bot_id)
        print(f"[Channel Manager] Processing {len(messages)}...")
        for message in messages:
            # Get All Thread Messages
            if 'latest_reply' in message.keys():
                thread_messages = fetch_all_thread_messages(client, channel_id, message["ts"])
            else:
                thread_messages = [message]
            if is_new_message(db, message["ts"]):
                contributors = get_all_contributors(client, thread_messages)
                db.add_conversation(message["ts"], thread_messages, contributors)
                print(f"New Message {message['ts']} - Added to DB")
            elif check_for_changed_message(db, message):
                contributors = get_all_contributors(client, thread_messages)
                db.update_conversation(message["ts"], thread_messages, contributors)
                print(f"Message {message['ts']} has changed - Updating...")
            else:
                pass
                #print(f"Message {message['ts']} has not changed - Skipping...")
        print("Channel Scan Complete - Sleeping...")
        time.sleep(config.SCRAPER_INTERVAL)

if __name__ == "__main__":
    config.SERVICE_RUNNING = True    
    channel_manager_routine()