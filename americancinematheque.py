import discord
import imaplib
import asyncio
import email
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

# Define the sender name to match (you can adjust this)
SENDER_NAME = 'American Cinematheque'

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
        
        # Search for emails from senders with "American Cinematheque" in the name
        status, messages = imap.search(None, 'UNSEEN', f'(FROM "{SENDER_NAME}")')
        if status == 'OK':
            for num in messages[0].split():
                status, data = imap.fetch(num, '(RFC822)')
                if status == 'OK':
                    msg = email.message_from_bytes(data[0][1])
                    subject = decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    
                    try:
                        user = await client.fetch_user(DISCORD_USER_ID)
                        await user.send(f'You have a new email from {SENDER_NAME} with subject: {subject}')
                    except Exception as e:
                        print(f"An error occurred: {e}")
                    
                    imap.store(num, '+FLAGS', '\\Seen')
        
        await asyncio.sleep(30)  # Check every 5 minutes (adjust as needed)
        imap.close()
        imap.logout()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    client.loop.create_task(check_email())
    # Consider not ending the bot if you want it to check emails continuously or on a schedule
    # await client.close()

client.run(DISCORD_TOKEN)
