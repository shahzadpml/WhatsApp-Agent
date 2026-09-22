import os
from fastapi import FastAPI, Request, Response
import google.generativeai as genai
import requests

app = FastAPI()

# Environment Variables
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

# Meta Webhook Verification (GET Request)
@app.get("/webhook")
async def verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return Response(content=challenge, media_type="text/plain")
        return Response(content="Verification failed", status_code=403)
    return Response(content="Missing parameters", status_code=400)

# Incoming WhatsApp Message Handler (POST Request)
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    try:
        entries = data.get('entry', [])
        for entry in entries:
            changes = entry.get('changes', [])
            for change in changes:
                value = change.get('value', {})
                messages = value.get('messages', [])
                if messages:
                    message = messages[0]
                    from_number = message.get('from')
                    
                    if message.get('type') == 'text':
                        user_text = message.get('text', {}).get('body')

                        # Generate AI Response
                        response = model.generate_content(user_text)
                        ai_reply = response.text

                        # Send Response back to WhatsApp Meta API
                        url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
                        headers = {
                            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                            "Content-Type": "application/json"
                        }
                        payload = {
                            "messaging_product": "whatsapp",
                            "to": from_number,
                            "type": "text",
                            "text": {"body": ai_reply}
                        }
                        requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print(f"Error processing webhook: {e}")

    return {"status": "ok"}
