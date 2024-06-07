# This agent pulls the learning items that are ready for knowledge distillation and attempts to do just that.
import db_manager

import json
import os
import time

import llm_utils
import config


# AI EVALUATION STEP
def generate_evaluation(user_info, req_info):
    prompt = """
    ## INSTRUCTIONS ##
    You are a Security Engineering Lead analyzing the provided conversation transcript. Your task is to evaluate the interaction and provide insights based on the following criteria:
    1. Identify the primary intent of the requester. What is their main goal or concern?
    2. Assess whether the security engineer effectively resolved the requester's issue.
    3. Determine if the nature of this request is informational, requiring only guidance, or if it necessitates specific actions by the security team to be resolved.
    4. Evaluate if this interaction could be automated: Could a chatbot handle this type of request in the future without human intervention?
    5. Consider if this request could be formulated into a generic Question/Answer pair that could be used to address similar future inquiries.

    ## OUTPUT FORMAT ##
    Please provide your analysis in a JSON format with the following keys:
    - "feedback": "Provide your detailed feedback here.",
    - "chatbot": "YES/NO"  (Indicate whether a chatbot could handle such a request based on current technology and available information.)
    - "justification": "Explain your reasoning for whether or not this request can be handled automatically by a chatbot."

    ## REQUEST INFORMATION ##
    ```""" + req_info + """```

    ## USER INFORMATION ##
    ```""" + user_info + """```
    """


    response = llm_utils.get_json_response_from_llm(prompt)
    return response

def generate_qan(user_info, req_info, evaluation_data):

    prompt = """
    ## INSTRUCTIONS ##
    You are a Security Engineering Lead tasked with creating a Question/Answer pair based on the provided conversation transcript. Your task is to generate a question that encapsulates the primary intent of the requester and an answer that effectively addresses their concern. Additionally, provide a nuance that captures the unique aspect of this interaction in the event that it is required for this question and answer to be relevant to a future inquiry.

    ## OUTPUT FORMAT ##
    Please provide your Question/Answer pair in a JSON format with the following keys
    - "question": "Your generated question here. Please ensure it is general enough to be useful to future inquiries as appropriate",
    - "answer": "Your generated answer here.",
    - "nuance": "Provide a nuanced detail that would qualify or disqualify this question and answer from being used in similar requests if necessary. If not, leave blank"

    ## REQUEST INFORMATION ##
    ```""" + req_info + """```

    ## USER INFORMATION ##
    ```""" + user_info + """```

    ## EVALUATION DATA ##
    ```""" + evaluation_data + """```

     """
    response = llm_utils.get_json_response_from_llm(prompt)
    return response    

def generate_request_information(db, conversation_id):
    conversation = db.get_conversation(conversation_id)
    if conversation is None:
        print("Conversation ID Does not Exist")
        return False, None
    
    messages_info = json.loads(conversation.messages,strict=False)
    users_info = json.loads(conversation.userinfo,strict=False)

    request_info = config.extract_request_information(messages_info)
    rendered_request = config.render_request(request_info)
    chat_transcript = config.generate_chat_transcript(messages_info)
    user_infos = config.generate_user_info(users_info)

    # Create Transcript
    rinfo = {
        "req_info":rendered_request + chat_transcript,
        "user_info": user_infos
    }
    return True,rinfo

def agent_learning_routine():
    print("Starting Learning Agent")
    db = db_manager.DBManager(config.DATABASE_URL)
    while config.SERVICE_RUNNING:
        processed_count = 0 
        new_learning_entries = db.get_learning_entries_with_state("NEW")
        for entry in new_learning_entries:
            print(f"Processing Learning Entry: {entry.conversation_id}...")
            status, rinfo = generate_request_information(db, entry.conversation_id)
            if status is False:
                continue

            evaluation = generate_evaluation(rinfo['user_info'],rinfo['req_info'])
            if evaluation['chatbot'] == "NO":
                evaluation_text = f"Feedback: {evaluation['feedback']}\nChatbot: {evaluation['chatbot']}\nJustification: {evaluation['justification']}"
                db.update_learning(entry.id,evaluation=evaluation_text, state="SKIPPED")
                processed_count+=1
                continue
            else:
                evaluation_text = f"Feedback: {evaluation['feedback']}\nChatbot: {evaluation['chatbot']}\nJustification: {evaluation['justification']}"
                print(f"Summary: {evaluation['feedback']}\n\n")
                print(f"Justification: {evaluation['justification']}\n\n")
                print(f"Verdict: Accepted - Posted for Review")
                print("---")
                # Generate the Question / Answers and Nuance
                qan = generate_qan(rinfo['user_info'],rinfo['req_info'],json.dumps(evaluation,ensure_ascii=False))
                #print(qan)
                db.update_learning(entry.id,evaluation=evaluation_text, question=qan['question'],answer=qan['answer'],nuance=qan['nuance'], state="READY")
                processed_count +=1

        print(f"Processed {processed_count} learning entries.")
        time.sleep(config.LEARNING_AGENT_INTERVAL)

if __name__ == "__main__":
    config.SERVICE_RUNNING = True
    agent_learning_routine()    

