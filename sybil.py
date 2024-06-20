# Primary Runtime for Sybil
import sys
import os
from threading import Thread


if __name__ == "__main__":
    print("Starting Sybil Runtime...")
    if len(sys.argv) > 1:
        config_file = os.path.abspath(os.path.expanduser(sys.argv[1]))
        if os.path.exists(config_file):
            print(f"Starting Sybil with Config: {config_file}")
            os.environ['SYBIL_CONFIG'] = config_file

    import config
    config.SERVICE_RUNNING = True
    # Start all the threads
    from agent_assistant import agent_assistant_routine
    from agent_learning import agent_learning_routine
    from manager_assistant import assistant_manager_routine
    from manager_channel import channel_manager_routine
    from manager_feedback import feedback_manager_routine
    from manager_knowledge import knowledge_manager_routine    
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
    #while True:
    #    pass
    feedback_manager_routine()
