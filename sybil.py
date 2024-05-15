# Primary Runtime for Sybil
from threading import Thread

import config
from agent_assistant import agent_assistant_routine
from agent_learning import agent_learning_routine

from manager_assistant import assistant_manager_routine
from manager_channel import channel_manager_routine
from manager_feedback import feedback_manager_routine
from manager_knowledge import knowledge_manager_routine




if __name__ == "__main__":
    print("Starting Sybil Runtime...")
    config.SERVICE_RUNNING = True
    # Start all the threads
    threads = []
    threads.append(Thread(target=agent_assistant_routine))
    threads.append(Thread(target=agent_learning_routine))

    threads.append(Thread(target=assistant_manager_routine))
    threads.append(Thread(target=channel_manager_routine))
    threads.append(Thread(target=knowledge_manager_routine))


    for thread in threads:
        thread.daemon = True
        thread.start()
    # The listener for events kind of has to be the last thing that runs... it's fine.
    feedback_manager_routine()
