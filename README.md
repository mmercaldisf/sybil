# Sybil - A Simple, AI Powered Q&A Chatbot Framework for Slack
![alt text](https://github.com/batteryshark/sybil/blob/main/slack_assets/icon.png)

This service is designed to run in a slack channel and monitor a submission workflow where it will learn from completed requests and attempt to answer requests where it can from its knowledgebase.

## Features

* Independently-Operated Runtimes with Configurable Refresh Rates
* OpenAI-API complatible inferencing for automatic knowledge curation and responses.
* Human Feedback System to better tailor results.
* Human Review System (via included reviewer_app) for manual approval of new knowledgebase items.
* SQLAlchemy Data Manager Backend to support multiple DB backends (e.g. sqlite3, postgres, etc.)

## Component Breakdown
Sybil is comprised of several processes for optimal availability that operate at regular intervals

### Channel Manager
Scrapes a target channel for workflow items and caches them alongside their conversation threads and user information.

### Knowledge Manager
Analyzes completed workflow requests and stages them for AI-powered knowledge extraction.
Integrates any newly approved knowledge entries into the knowledgebase.

### Assistant Manager
Analyzes incomplete workflow requests and stages them for AI-powered workflows to determine if they can be answered with the knowledgebase.
Forwards any AI-generated responses to their appropriate request thread.

### Feedback Manager
Listener for Slack Interaction. When the requestor receives an automated answer, a prompt is given to determine if the answer has completed their request.
If the requestor indicates that it does, the request will be automatically closed. If not, the requestor will be given instructions that the request will be deferred to 
the team and an optional feedback submission form is given.

## Instructions for Setup
1. Ensure that the requirements are pulled via pip install -r requirements.txt
2. Copy env.conf.example to env.conf and fill out necessary API tokens.
3. Edit config.py to suit your workflow and options such as refresh rate on the various components.
4. Run sybil.py when ready to kick off full service.

### Optional
5. run app.py in the "reviewer_app" directory for a web interface to review potential knowledgebase materials.
6. run the importer or exporter in the kb_tools folder to import/export the knowledgebase to/from a CSV file.

