# This agent pulls the learning items that are ready for knowledge distillation and attempts to do just that.
import os
import time
import json

import config
import db_manager
import llm_utils


def generate_answer(user_info, transcript, knowledgebase):
    prompt = """
    ## INSTRUCTIONS ##
    Assume the role of a Security Engineering Lead who is well-versed in security protocols and solutions. Using the detailed information available, respond to the requester's inquiry. Your answers should be informed and precise, as if you are consulting your extensive experience and knowledge in security engineering.
    ** IMPORTANT ** the response should be framed as if you are responding to the requester directly from your own knowledge, not as a direct quote from the knowledgebase. You can reference the knowledgebase for additional information, but the response should be personalized and tailored to the user's inquiry.
    ## OUTPUT FORMAT ##
    Please provide your analysis in the following JSON format:
    - "response": "Provide a well-informed response to the requester, utilizing your extensive security knowledge.",
    - "justification": "Explain the reasoning behind your response, referencing your depth of knowledge in the field."

    ## TRANSCRIPT ##
    ```""" + transcript + """```

    ## USER INFO ##
    ```""" + user_info + """```

    ## KNOWLEDGEBASE ##
    ```""" + knowledgebase + """```

    """

    response = llm_utils.get_json_response_from_llm(prompt)
    return response



def determine_answerable(user_info, transcript, knowledgebase):
    prompt = """
    ## INSTRUCTIONS ##
    As a Security Engineering Lead, evaluate the provided conversation transcript to determine if it can be resolved using the knowledge available in our knowledgebase. Your analysis should cover the following aspects:
    1. Clarify the main goal or concern of the requester by identifying the primary intent of their inquiry.
    2. Determine if any existing Question/Answer pairs in the knowledgebase directly address the requester's issue.
    3. Assess if the request is purely informational, needing only guidance, or if it requires specific actions by the security team to be effectively resolved.

    ## OUTPUT FORMAT ##
    Provide your analysis in the following JSON format:
    - "feedback": "Your detailed feedback on the possibility of resolving the request using the knowledgebase.",
    - "answerable": "YES/NO" (State whether the request can be answered using the knowledgebase based on your evaluation.)
    - "references": [Question IDs] (List the IDs of relevant Question/Answer pairs from the knowledgebase that could address this request, if any.)

    ## TRANSCRIPT ##
    ```""" + transcript + """```

    ## USER INFO ##
    ```""" + user_info + """```

    ## KNOWLEDGEBASE ##
    ```""" + knowledgebase + """```

    """

    response = llm_utils.get_json_response_from_llm(prompt)
    return response

def agent_assistant_routine():
    print("Starting Assistant Agent")
    db = db_manager.DBManager(config.DATABASE_URL)
    while config.SERVICE_RUNNING:
        processed_count = 0 
        new_entries = db.get_assistant_entries_with_state("NEW")
        knowledgebase = db.get_all_knowledge()
        knowledgebase_rendering = ""
        for entry in knowledgebase:
            knowledgebase_rendering += f"ID: {entry.id} Question: {entry.question}\nAnswer: {entry.answer}\nNuance: {entry.nuance}\n\n"
        for entry in new_entries:
            conversation = db.get_conversation(entry.conversation_id)
            conversation_info = json.loads(conversation.messages,strict=False)
            user_info = json.loads(conversation.userinfo,strict=False)
            conversation_user_info = ""
            rendered_transcript = ""
            try:
                transcript = config.create_message_transcript(conversation_info)
                conversation_user_info = config.get_full_user_infos(transcript,conversation_info, user_info)
                rendered_transcript = config.render_transcript(transcript)
            except Exception as e:
                print(f"Error processing Assistant Entry {entry.conversation_id}")
                print(e)
                continue        
            print(f"Processing Assistant Entry {entry.conversation_id}")
            evaluation = determine_answerable(conversation_user_info,rendered_transcript,knowledgebase_rendering)
            if evaluation['answerable'] == "NO":
                db.update_assistant(entry.conversation_id, state="NOANSWER")
                processed_count+=1
                continue
            else:
                tkb = ""
                for ref_entry in evaluation['references']:
                    ref_entry -= 1
                    tkb += f"ID: {ref_entry} Question: {knowledgebase[ref_entry].question}\nAnswer: {knowledgebase[ref_entry].answer}\nNuance: {knowledgebase[ref_entry].nuance}\n\n"
                response = generate_answer(conversation_user_info,rendered_transcript,tkb)
                db.update_assistant(entry.conversation_id, response=response['response'],sources=json.dumps(evaluation['references']), state="ANSWERED")     
                processed_count+=1     
        print(f"Processed {processed_count} assistant entries.")
        time.sleep(config.ASSISTANT_AGENT_INTERVAL)

if __name__ == "__main__":
    config.SERVICE_RUNNING = True
    agent_assistant_routine()    

