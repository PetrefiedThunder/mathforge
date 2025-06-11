from fastapi import FastAPI, Form
from pydantic import BaseModel
from twilio.rest import Client as TwilioClient
import redis, os, json, threading, time
from sqlalchemy import create_engine, Column, String, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import openai

# Initialize FastAPI, database engine, Redis, Twilio, and OpenAI
app = FastAPI()
engine = create_engine(os.getenv('DATABASE_URL'))
Session = sessionmaker(bind=engine)
Base = declarative_base()
r = redis.Redis(host='redis', port=6379)

twilio = TwilioClient(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
openai.api_key = os.getenv('OPENAI_API_KEY')

# DB Models

# Subscriber tracks active phone numbers for SMS notifications.
class Subscriber(Base):
    __tablename__ = 'subscribers'
    phone = Column(String, primary_key=True)
    active = Column(Boolean, default=True)

# Problem represents a registered Clay Millennium Prize Problem.
class Problem(Base):
    __tablename__ = 'problems'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    description = Column(String)
    active = Column(Boolean, default=True)

Base.metadata.create_all(engine)

# Helper to broadcast a micro-task to all active subscribers
def broadcast_task(problem_id, prompt):
    db = Session()
    try:
        subs = db.query(Subscriber).filter_by(active=True).all()
        # db.commit() is not needed here as we are only reading.
        # db.rollback() is also not strictly necessary for read-only, but good practice.
        for sub in subs:
            twilio.messages.create(
                to=sub.phone,
                from_=os.getenv('TWILIO_PHONE_NUMBER'),
                body=f'Problem {problem_id}: {prompt}'
            )
    except Exception as e:
        # Log the exception e here, e.g., print(f"Error in broadcast_task: {e}")
        # For read-only operations, rollback might not be critical, but doesn't hurt.
        db.rollback()
        raise
    finally:
        db.close()

# SMS Inbound Endpoint: Process subscriptions and contributions
@app.post('/sms')
async def sms_reply(From: str = Form(...), Body: str = Form(...)):
    db = Session()
    try:
        sub = db.query(Subscriber).filter_by(phone=From).first()
        if not sub:
            # New subscriber: add to DB and notify
            sub = Subscriber(phone=From)
            db.add(sub)
            db.commit()
            # db.refresh(sub) # If needed
            twilio.messages.create(
                to=From, from_=os.getenv('TWILIO_PHONE_NUMBER'),
                body='Subscribed to Millennium Problems updates.'
            )
            return "Subscribed"

        # Process incoming contribution. Expected format: "<problem_id>: <idea>"
        # This part does not involve DB operations with the 'db' session from this function.
        # It queues to Redis.
        if ':' in Body:
            pid, contrib = Body.split(':', 1)
            # Clarify contribution with LLM
            resp = openai.ChatCompletion.create(
                model='gpt-4',
                messages=[{'role':'user', 'content': f'Clarify this contribution for problem {pid}: {contrib}'}]
            )
            clarified = resp.choices[0].message.content
            # Queue for feasibility test (using Redis list)
            r.rpush('tasks', json.dumps({'phone': From, 'problem_id': pid.strip(), 'contrib': clarified}))
            twilio.messages.create(
                to=From, from_=os.getenv('TWILIO_PHONE_NUMBER'),
                body=f'Contribution received for Problem {pid.strip()}. Queued for review.'
            )
            return "Received"

        # If the message format is unrecognized
        # No db.commit() needed here if only reads happened or no changes were made.
        return "Format: <problem_id>: <your idea>"
    except Exception as e:
        db.rollback()
        # Log the exception e here, e.g., print(f"Error in sms_reply: {e}")
        raise
    finally:
        db.close()

# Endpoint to register a new problem via an admin UI or bulk load script
class ProblemIn(BaseModel):
    name: str
    description: str

@app.post('/problems')
def add_problem(p: ProblemIn):
    db = Session()
    try:
        pr = Problem(name=p.name, description=p.description)
        db.add(pr)
        db.commit()
        # db.refresh(pr) # Uncomment if needed, e.g., to get pr.id if it's auto-generated and not returned by commit
        return {'id': pr.id} # Assuming id is available after commit or is set by default
    except Exception as e:
        db.rollback()
        # Log the exception e here, e.g., print(f"Error in add_problem: {e}")
        raise
    finally:
        db.close()

# Endpoint to send a micro-task for a given problem
class MicroTask(BaseModel):
    problem_id: int
    prompt: str

@app.post('/send_task')
def send_task(task: MicroTask):
    broadcast_task(task.problem_id, task.prompt)
    return {'sent': True}

# Worker to process queued tasks (feasibility tests, etc.)
def process_tasks():
    while True:
        try:
            item_tuple = r.blpop('tasks', timeout=1)
            if item_tuple:
                _, item = item_tuple
                data = json.loads(item)
                # TODO: Automate feasibility tests based on problem-specific criteria
                # For now, we are not interacting with the DB here.
                # If DB operations were needed, a new session would be created:
                # db = Session()
                # try:
                #   ... db operations ...
                #   db.commit()
                # except Exception as e:
                #   db.rollback()
                #   print(f"Error processing task with data {data}: {e}") # Or use a proper logger
                # finally:
                #   db.close()

                feasible = True  # Placeholder evaluation
                msg = "Accepted and credited." if feasible else "Needs refinement."

                twilio.messages.create(
                    to=data['phone'], from_=os.getenv('TWILIO_PHONE_NUMBER'),
                    body=msg
                )
        except json.JSONDecodeError as e:
            # Log JSON parsing errors
            print(f"Error decoding JSON: {e}. Item: {item}") # Or use a proper logger
        except Exception as e:
            # Log other potential errors (Twilio API calls, etc.)
            # Note: `data` might not be defined if json.loads failed.
            print(f"Error processing task: {e}") # Or use a proper logger
        else:
            # If blpop times out (item_tuple is None), sleep briefly
            if not item_tuple:
                time.sleep(0.1) # Sleep for 100ms to prevent tight loop if Redis is busy or list is empty

@app.on_event("startup")
def startup_event_handler():
    task_processor_thread = threading.Thread(target=process_tasks, daemon=True)
    task_processor_thread.start()