

# Needs to install pip install sqlalchemy psycopg2-binary
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
import hashlib

Base = declarative_base()

# Define your table models using SQLAlchemy's ORM system
class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(String, primary_key=True)
    updated = Column(String)
    messages = Column(Text)
    userinfo = Column(Text)

class Knowledge(Base):
    __tablename__ = 'knowledge'
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text)
    answer = Column(Text)
    nuance = Column(Text)
    sources = Column(String)

class Learning(Base):
    __tablename__ = 'learning'
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String)
    evaluation = Column(Text)
    question = Column(Text)
    answer = Column(Text)
    nuance = Column(Text)
    state = Column(String)

class Assistant(Base):
    __tablename__ = 'assistant'
    conversation_id = Column(String, primary_key=True)
    user_id = Column(String)
    response = Column(Text)
    sources = Column(Text)
    feedback = Column(Text)
    state = Column(String)

class DBManager:
    def __init__(self, db_url='sqlite:///sybil.db'):
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def hash_message(self, message):
        """
        Generate a hash for a message.
        """
        return hashlib.md5(json.dumps(message, ensure_ascii=False).encode()).hexdigest()

    # Conversation Table Operations
    def add_conversation(self, message_id, messages, userinfo):
        updated = messages[0].get('latest_reply',"") if messages else ""
        conversation = Conversation(id=message_id, updated=updated, messages=json.dumps(messages, ensure_ascii=False), userinfo=json.dumps(userinfo, ensure_ascii=False))
        self.session.add(conversation)
        self.session.commit()

    def get_conversation(self, message_id):
        return self.session.query(Conversation).filter(Conversation.id == message_id).first()

    def get_all_conversations(self):
        return self.session.query(Conversation).all()

    def update_conversation(self, message_id, messages=None, userinfo=None):
        conversation = self.session.query(Conversation).filter(Conversation.id == message_id).first()
        if conversation:
            if messages:
                conversation.messages = json.dumps(messages, ensure_ascii=False)
                conversation.updated = messages[0].get("latest_reply","")
            if userinfo:
                conversation.userinfo = json.dumps(userinfo, ensure_ascii=False)
            self.session.commit()

    # Knowledge Table Operations
    def add_knowledge(self, question, answer, nuance, sources=None):
        knowledge_entry = Knowledge(question=question, answer=answer, nuance=nuance, sources=sources)
        self.session.add(knowledge_entry)
        self.session.commit()

    def get_knowledge(self, id):
        return self.session.query(Knowledge).filter(Knowledge.id == id).first()
    
    def get_all_knowledge(self):
        return self.session.query(Knowledge).all()

    # Learning Table Operations
    def add_learning(self, conversation_id, evaluation, question, answer, nuance, state="NEW"):
        learning_entry = Learning(conversation_id=conversation_id, evaluation=evaluation, question=question, answer=answer, nuance=nuance, state=state)
        self.session.add(learning_entry)
        self.session.commit()

    def update_learning(self, id, **kwargs):
        learning_entry = self.session.query(Learning).filter(Learning.id == id).first()
        if learning_entry:
            for key, value in kwargs.items():
                setattr(learning_entry, key, value)
            self.session.commit()

    def get_learning_entries_with_state(self, state):
        return self.session.query(Learning).filter(Learning.state == state).all()

    def list_learning_ids(self):
        """
        Retrieve all conversation IDs from the learning table.
        """
        return [entry.conversation_id for entry in self.session.query(Learning.conversation_id).all()]
    
    # Assistant Table Operations
    def add_assistant(self, conversation_id, user_id, response, sources, feedback, state="NEW"):
        assistant_entry = Assistant(conversation_id=conversation_id, user_id=user_id, response=response, sources=sources, feedback=feedback, state=state)
        self.session.add(assistant_entry)
        self.session.commit()

    def update_assistant(self, conversation_id, **kwargs):
        assistant_entry = self.session.query(Assistant).filter(Assistant.conversation_id == conversation_id).first()
        if assistant_entry:
            for key, value in kwargs.items():
                setattr(assistant_entry, key, value)
            self.session.commit()

    def get_assistant_entries_with_state(self, state):
        return self.session.query(Assistant).filter(Assistant.state == state).all()

    def get_assistant_user_id(self, conversation_id):
        """
        Retrieve the user ID associated with a given conversation ID from the assistant table.
        """
        assistant_entry = self.session.query(Assistant.user_id).filter(Assistant.conversation_id == conversation_id).first()
        return assistant_entry.user_id if assistant_entry else None

    def list_assistant_ids(self):
        """
        Retrieve all conversation IDs from the assistant table.
        """
        return [entry.conversation_id for entry in self.session.query(Assistant.conversation_id).all()]



    def __del__(self):
        self.session.close()

