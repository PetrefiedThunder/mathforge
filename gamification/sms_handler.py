"""
This module integrates SMS functionality into the gamification service.
It uses Twilio to:
  - Send the "problem of the day" via SMS to subscribers, and
  - Receive inbound SMS messages (responses) from subscribers.
  
Subscribers can simply respond and the AI will work to decipher, test,
verify, and use their input as the next step for crowdsourcing solutions.
  
Before using, ensure the following environment variables are configured:
  - TWILIO_ACCOUNT_SID: Your Twilio Account SID.
  - TWILIO_AUTH_TOKEN: Your Twilio Auth Token.
  - TWILIO_FROM_NUMBER: The Twilio phone number to send SMS from.
  
This module is designed for open source use so even the newest developers
can follow the documentation.
"""

import os
from fastapi import FastAPI, Request, HTTPException, Query
from twilio.twiml.messaging_response import MessagingResponse
import twilio.rest

app = FastAPI(title="Gamification SMS Handler")

# A demonstration list of subscriber phone numbers.
# In a production system, you would use a persistent data store.
TEL_SUBSCRIBERS = [
    "+1234567890",
    "+1987654321",
    # Add additional subscriber phone numbers here.
]

def send_sms_to_subscribers(problem_text: str):
    """
    Sends the given problem text as SMS to every subscriber.
    
    Uses the Twilio API via environment variables.
    
    Args:
        problem_text (str): The text content of the problem to send.
    
    Raises:
        Exception: In case any Twilio required environment variable is missing.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")
    if not all([account_sid, auth_token, from_number]):
        raise Exception("Twilio environment variables (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER) must be set.")
    
    client = twilio.rest.Client(account_sid, auth_token)
    
    for subscriber in TEL_SUBSCRIBERS:
        message = client.messages.create(
            body=f"Problem of the Day: {problem_text}",
            from_=from_number,
            to=subscriber
        )
        print(f"Sent SMS to {subscriber}: SID {message.sid}")

@app.post("/sms/send")
async def trigger_sms(problem_text: str = Query(..., description="The problem text to send via SMS")):
    """
    Endpoint to trigger SMS notifications to subscribers.
    
    Query Parameter:
      - problem_text (str): The text content for the problem that will be sent.
    
    Returns:
      - JSON object indicating the SMS messages have been sent successfully.
    """
    try:
        send_sms_to_subscribers(problem_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "SMS messages sent"}

@app.post("/sms/inbound")
async def inbound_sms(request: Request):
    """
    Endpoint to handle inbound SMS messages from subscribers.
    This endpoint is intended to be used as a webhook endpoint for Twilio.
    
    Process:
      1. Receives inbound SMS data in form-urlencoded format.
      2. Logs the phone number and body of the incoming message.
      3. Returns a Twilio-compatible XML response.
    
    Returns:
      - A Twilio MessagingResponse XML string.
    """
    # Twilio sends its webhook data as form-url-encoded.
    form_data = await request.form()
    incoming_message = form_data.get("Body")
    from_number = form_data.get("From")
    
    # Log the incoming message for debugging and processing.
    print(f"Received SMS from {from_number}: {incoming_message}")
    
    # Here you could add AI processing to decipher the response, verify it, and update the problem of the day.
    # For demonstration, we simply acknowledge receipt.
    
    response = MessagingResponse()
    response.message("Thank you for your response! We are processing your input.")
    return str(response)