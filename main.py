import os
import requests
from fastapi import FastAPI, Request, Response
import google.generativeai as genai

app = FastAPI()

# Environment Variables Load Karein
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_verify_token_123")

# Gemini AI Configure Karein
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

# 1. Root Endpoint (404 Error Fixed)
@app.get("/")
def read_root():
    return {"status": "WhatsApp Gemini Bot is Live & Running"}

# 2. Webhook Verification (GET Request - Meta Webhook Verification Ke Liye)
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verified successfully!")
        return Response(content=challenge, status_code=200)
    
    print("Webhook verification failed!")
    return Response(status_code=403)

# 3. Message Receive & Reply Logic (POST Request)
@app.post("/webhook")
@app.post("/")
async def handle_whatsapp_message(request: Request):
    try:
        body = await request.json()
        print("Incoming Webhook Data:", body)

        # Meta Event Check Karein
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            message = messages[0]
            from_number = message.get("from") # Customer/User Ka Number
            
            # Agar Incoming Message Text Type Hai
            if message.get("type") == "text":
                user_text = message.get("text", {}).get("body", "")
                print(f"Received Message from {from_number}: {user_text}")

                # 1. Gemini AI Se Response Handle Karein
                try:
                    gemini_response = model.generate_content(user_text)
                    reply_text = gemini_response.text
                except Exception as e:
                    print(f"Gemini API Error: {e}")
                    reply_text = "Sorry, main abhi aapke message ka reply nahi de pa raha hoon."

                # 2. WhatsApp Par Reply Bhejein
                send_whatsapp_message(from_number, reply_text)

        return {"status": "success"}

    except Exception as e:
        print(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}

# Helper Function: WhatsApp API Response Sender
def send_whatsapp_message(to_number: str, text: str):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text}
    }
    
    response = requests.post(url, json=payload, headers=headers)
    print("WhatsApp API Response Status:", response.status_code)
    print("WhatsApp API Response Body:", response.text)
