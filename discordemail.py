import discord
import imaplib
import email
import re
import asyncio
from email.header import decode_header
from dotenv import load_dotenv
import os
load_dotenv('config.env')

# Discord bot token
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_USER_ID = os.getenv('DISCORD_USER_ID')
# Gmail credentials
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')

# Define which intents you want to use
intents = discord.Intents.default()  # This sets up the default intents
intents.messages = True  # This enables receiving messages
intents.dm_messages = True  # This enables receiving direct messages

# Initialize the client with the specified intents
client = discord.Client(intents=intents)

async def check_email():
    while True:
        imap = imaplib.IMAP4_SSL('imap.gmail.com')
        imap.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        imap.select('inbox')
        
        status, messages = imap.search(None, 'UNSEEN', '(HEADER Subject "Email Confirmation Pin")')
        if status == 'OK':
            for num in messages[0].split():
                status, data = imap.fetch(num, '(RFC822)')
                if status == 'OK':
                    msg = email.message_from_bytes(data[0][1])
                    subject = decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()
                    
                    # Find all sequences of digits in the email body
                    numbers = re.findall(r"\d+", body)
                    # Select the first sequence that is exactly four digits long
                    pin_code = next((num for num in numbers if len(num) == 4), None)
                    
                    if pin_code:
                        message_to_send = f"You have a new email with subject: {subject}\n\nAnd your PIN is: {pin_code}"
                    else:
                        message_to_send = f"You have a new email with subject: {subject}\n\nUnable to find a PIN in the email."
                    
                    try:
                        user = await client.fetch_user(DISCORD_USER_ID)
                        await user.send(message_to_send)
                    except Exception as e:
                        print(f"An error occurred: {e}")
                    
                    imap.store(num, '+FLAGS', '\\Seen')
        
        await asyncio.sleep(30)
        imap.close()
        imap.logout()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    client.loop.create_task(check_email())
    # Consider not ending the bot if you want it to check emails continuously or on a schedule
    # await client.close()

client.run(DISCORD_TOKEN)
