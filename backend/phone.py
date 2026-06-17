from twilio.rest import Client

ACCOUNT_SID = "AC1426e6628f8d8b8a2fe9bf0104d1d466"
AUTH_TOKEN = "cf640cd8008d49bf6e7c2d02eedb72b1"
TWILIO_NUMBER = "+17178640924"
TO_NUMBER = "+919347637152"

client = Client(ACCOUNT_SID, AUTH_TOKEN)

call = client.calls.create(
    to=TO_NUMBER,
    from_=TWILIO_NUMBER,
    twiml='<Response><Say>Hello! Test call working</Say></Response>'
)

print("Call sent successfully")