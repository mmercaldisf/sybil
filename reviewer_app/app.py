import os
import sys
import json

from flask import Flask, jsonify, render_template, redirect, url_for, request
from flask_httpauth import HTTPBasicAuth


# Some modules are in the parent directory. Make sure to add the path to sys.path if needed
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db_manager import DBManager

import config

app = Flask(__name__)
auth = HTTPBasicAuth()

# Initialize DBManager
db_manager = DBManager(config.DATABASE_URL)

@auth.verify_password
def verify_password(username, password):
    if username == "reviewer" and password == os.getenv('REVIEWER_PW'):
        return username

@app.route('/')
@auth.login_required
def index():
    # Print all learning entries with state 'READY'
    ready_entries = db_manager.get_learning_entries_with_state('READY')
    entries_with_details = []
    for entry in ready_entries:
        conversation = db_manager.get_conversation(entry.conversation_id)
        conversation_info = json.loads(conversation.messages,strict=False)
        user_info = json.loads(conversation.userinfo,strict=False)

        try:
            transcript = config.create_message_transcript(conversation_info)
        except:
            continue

        conversation_user_info = config.get_full_user_infos(transcript,conversation_info, user_info)
        rendered_transcript = config.render_transcript(transcript)
        entry_details = {
            'id': entry.id,
            'question': entry.question,
            'answer': entry.answer,
            'nuance': entry.nuance,
            'state': entry.state,
            'source': entry.conversation_id,
            'evaluation': entry.evaluation,
            'messages': rendered_transcript if conversation else "No messages found",
            'userinfo': conversation_user_info if conversation else "No user info found"
        }
        entries_with_details.append(entry_details)
    return render_template('index.html', entries=entries_with_details)

@app.route('/update', methods=['POST'])
@auth.login_required
def update_entry():
    entry_id = request.form['id']
    new_state = request.form['state']
    db_manager.update_learning(entry_id, 
                               question=request.form['question'], 
                               answer=request.form['answer'], 
                               nuance=request.form['nuance'], 
                               state=new_state)

    if new_state == 'APPROVED':
        db_manager.add_knowledge(question=request.form['question'],
                                 answer=request.form['answer'],
                                 nuance=request.form['nuance'],
                                 sources=request.form['source'])

    return redirect(url_for('index'))


if __name__ == '__main__':
    HOST = config.REVIEWER_HOST
    PORT = config.REVIEWER_PORT
    app.run(host=HOST, port=PORT, debug=True)
