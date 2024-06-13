import os 
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import config
import db_manager


app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# This is just here to shut up the debug message.
@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)

@app.event("reaction_added")
def handle_reaction_added_events(body, logger):
    logger.info(body)

@app.event("reaction_removed")
def handle_reaction_removed_events(body, logger):
    logger.info(body)

@app.action("yes_button")
def handle_yes_button(ack, body, client):
    ack()
    # Check if the user who clicked is the intended user
    channel_id = body["channel"]["id"]
    ts = body["container"]["message_ts"]
    # Retrieve the thread timestamp, which is the parent message ID
    thread_ts = body["container"]["thread_ts"]
    user_id = body["user"]["id"]
    intended_user_id = db_manager.DBManager(config.DATABASE_URL).get_assistant_user_id(thread_ts)
    
    if user_id != intended_user_id:
        # Optionally, send a message to the user that they cannot interact with this button
        client.chat_postEphemeral(
            channel=body["channel"]["id"],
            user=user_id,
            thread_ts=thread_ts,            
            text=config.NOT_AUTHORIZED_MESSAGE
        )
        return
    


    # Update the current message
    client.chat_update(
        channel=channel_id,
        ts=ts,
        text=config.APPROVE_MESSAGE,
        blocks=None  # Clear the blocks to just show the text message
    )
    """
    # Add a reaction to the parent message in the thread
    client.reactions_add(
        channel=channel_id,
        timestamp=thread_ts,  # This is the ID of the parent message
        name="white_check_mark"
    )
    """

    # Update the Assistant Entry that the answer was "APPROVED"
    db = db_manager.DBManager(config.DATABASE_URL)
    print(f"Updating Assistant Entry {thread_ts} to APPROVED")
    db.update_assistant(thread_ts, state="APPROVED")



@app.action("no_button")
def handle_no_button(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    ts = body["container"]["message_ts"]
    thread_ts = body["container"]["thread_ts"]

    intended_user_id = db_manager.DBManager().get_assistant_user_id(thread_ts)

    if user_id != intended_user_id:
        client.chat_postEphemeral(
            channel=body["channel"]["id"],
            user=user_id,
            thread_ts=thread_ts,            
            text=config.NOT_AUTHORIZED_MESSAGE
        )
        return
    

    # Update the message with new text and a button for submitting feedback
    feedback_button = [
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": config.REJECT_MESSAGE
        }
    },        
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Submit Feedback"
                    },
                    "action_id": "submit_feedback_button"
                }
            ]
        }
    ]

    client.chat_update(
        channel=channel_id,
        ts=ts,
        text=config.REJECT_MESSAGE,
        blocks=feedback_button
    )
    # Update the Assistant Entry that the answer was "REJECTED"
    db = db_manager.DBManager(config.DATABASE_URL)
    print(f"Updating Assistant Entry {thread_ts} to REJECTED")
    db.update_assistant(thread_ts, state="REJECTED")    

@app.action("submit_feedback_button")
def open_feedback_modal(ack, body, client):
    ack()
    trigger_id = body["trigger_id"]
    channel_id = body["channel"]["id"]
    message_ts = body["container"]["message_ts"]
    thread_ts = body["container"]["thread_ts"]
    intended_user_id = db_manager.DBManager(config.DATABASE_URL).get_assistant_user_id(thread_ts)
    user_id = body["user"]["id"]
    if user_id != intended_user_id:
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            thread_ts=thread_ts,
            text=config.NOT_AUTHORIZED_MESSAGE
        )
        return
    
    # Store the channel and message_ts in private_metadata as a JSON string
    private_metadata = json.dumps({"channel_id": channel_id, "message_ts": message_ts, "thread_ts": thread_ts})

    modal = {
        "type": "modal",
        "title": {"type": "plain_text", "text": "Response Feedback"},
        "callback_id": "feedback_modal",
        "submit": {"type": "plain_text", "text": "Submit"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "private_metadata": private_metadata,  # Pass metadata here
        "blocks": [
            {
                "type": "input",
                "block_id": "feedback_input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "feedback",
                    "multiline": True,  # Enables multiline input
                    "min_length": 0,  # Optional: Set minimum length of input
                    "max_length": 2999  # Optional: Set maximum length of input                    
                },
                "label": {"type": "plain_text", "text": "Details"}
            }
        ]
    }
    client.views_open(trigger_id=trigger_id, view=modal)

@app.view("feedback_modal")
def handle_feedback_submission(ack, body, client):
    ack()
    user_feedback = body['view']['state']['values']['feedback_input']['feedback']['value']

    # Retrieve metadata
    private_metadata = json.loads(body["view"]["private_metadata"])
    channel_id = private_metadata["channel_id"]
    message_ts = private_metadata["message_ts"]

    # Add feedback to the database
    db = db_manager.DBManager(config.DATABASE_URL)
    db.update_assistant(private_metadata["thread_ts"], feedback=user_feedback)
    print(f"Feedback added to Assistant Entry {message_ts}")
    print(f"Feedback: {user_feedback}")

    # Update the message post-feedback
    client.chat_update(
        channel=channel_id,
        ts=message_ts,
        text=config.FEEDBACK_THANKYOU_MESSAGE,
        blocks=None  # Clear the blocks after submission
    )


def feedback_manager_routine():
    print("Starting Feedback Manager")
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()


if __name__ == "__main__":
    config.SERVICE_RUNNING = True    
    feedback_manager_routine()