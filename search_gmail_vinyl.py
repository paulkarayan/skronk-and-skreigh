#!/usr/bin/env python3
"""
Gmail Vinyl/LP Purchase Search Script

This script searches your Gmail account for emails related to vinyl/LP purchases.
It looks for keywords like 'vinyl', 'LP', 'record', combined with purchase-related terms.
"""

import os
import pickle
import base64
import json
from datetime import datetime
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    """Authenticate and return Gmail service instance."""
    creds = None
    
    # Token file stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Create credentials from environment variables
            client_config = {
                "installed": {
                    "client_id": os.getenv('GMAIL_CLIENT_ID'),
                    "client_secret": os.getenv('GMAIL_CLIENT_SECRET'),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["http://localhost", "http://localhost:8080/", "urn:ietf:wg:oauth:2.0:oob"]
                }
            }
            
            flow = InstalledAppFlow.from_client_config(
                client_config, SCOPES)
            print("\nOpening browser for OAuth authentication...")
            print("If the browser doesn't open automatically, please visit the URL shown below.")
            print("\nIMPORTANT: Make sure you:")
            print("1. Added paulkarayan@gmail.com as a test user in Google Cloud Console")
            print("2. OAuth consent screen is in 'Testing' mode")
            print("3. Gmail API is enabled in your project")
            
            creds = flow.run_local_server(port=8080, open_browser=True)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)

def search_vinyl_purchases(service, max_results=50):
    """
    Search Gmail for vinyl/LP purchase emails.
    
    Args:
        service: Gmail API service instance
        max_results: Maximum number of results to return
    
    Returns:
        List of email details
    """
    # Build search query - focusing on Merchbar and eBay, since Jan 2024
    search_queries = [
        'from:(merchbar.com) AND (LP OR vinyl) after:2024/1/1',
        'from:(ebay.com) AND (LP OR vinyl) after:2024/1/1',
        'from:(paypal.com) AND (LP OR vinyl OR record) after:2024/1/1',  # PayPal receipts for eBay
        '(subject:"order confirmation" OR subject:"purchase confirmation" OR subject:"order receipt") AND (vinyl OR LP) after:2024/1/1'
    ]
    
    all_messages = []
    
    for query in search_queries:
        try:
            # Search for messages
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if messages:
                print(f"\nFound {len(messages)} messages for query: {query[:50]}...")
                
                for msg in messages:
                    # Get the full message
                    message = service.users().messages().get(
                        userId='me',
                        id=msg['id']
                    ).execute()
                    
                    # Extract email details
                    email_data = parse_email(message)
                    if email_data and email_data not in all_messages:
                        all_messages.append(email_data)
            
        except HttpError as error:
            print(f'An error occurred: {error}')
    
    return all_messages

def parse_email(message):
    """
    Parse email message and extract relevant information.
    
    Args:
        message: Gmail message object
    
    Returns:
        Dictionary with email details
    """
    headers = message['payload'].get('headers', [])
    
    # Extract header information
    subject = ''
    sender = ''
    date = ''
    
    for header in headers:
        name = header['name']
        value = header['value']
        
        if name == 'Subject':
            subject = value
        elif name == 'From':
            sender = value
        elif name == 'Date':
            date = value
    
    # Extract body
    body = extract_body(message['payload'])
    
    # Extract snippet
    snippet = message.get('snippet', '')
    
    return {
        'id': message['id'],
        'subject': subject,
        'sender': sender,
        'date': date,
        'snippet': snippet,
        'body': body[:500] if body else snippet  # First 500 chars of body
    }

def extract_body(payload):
    """
    Extract body from email payload.
    
    Args:
        payload: Email payload
    
    Returns:
        Email body text
    """
    body = ''
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                break
            elif part['mimeType'] == 'text/html':
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    else:
        if payload['body'].get('data'):
            body = base64.urlsafe_b64decode(
                payload['body']['data']).decode('utf-8', errors='ignore')
    
    return body

def save_results(emails, filename='vinyl_purchases.txt'):
    """Save search results to a file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Vinyl/LP Purchase Search Results\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total emails found: {len(emails)}\n")
        f.write("=" * 80 + "\n\n")
        
        for i, email in enumerate(emails, 1):
            f.write(f"Email #{i}\n")
            f.write(f"Subject: {email['subject']}\n")
            f.write(f"From: {email['sender']}\n")
            f.write(f"Date: {email['date']}\n")
            f.write(f"Preview: {email['snippet']}\n")
            f.write("-" * 80 + "\n\n")

def main():
    """Main function to run the vinyl purchase search."""
    print("Gmail Vinyl/LP Purchase Search")
    print("=" * 40)
    
    # Check for credentials in environment
    if not os.getenv('GMAIL_CLIENT_ID') or not os.getenv('GMAIL_CLIENT_SECRET'):
        print("\nERROR: Gmail credentials not found in environment!")
        print("\nTo use this script, you need to:")
        print("1. Create a .env file with:")
        print("   GMAIL_CLIENT_ID=your_client_id")
        print("   GMAIL_CLIENT_SECRET=your_client_secret")
        print("\nOr set these as environment variables.")
        return
    
    try:
        # Authenticate
        print("\nAuthenticating with Gmail...")
        service = authenticate_gmail()
        
        # Search for vinyl purchases
        print("\nSearching for vinyl/LP purchases...")
        emails = search_vinyl_purchases(service, max_results=100)
        
        if emails:
            print(f"\n✓ Found {len(emails)} vinyl/LP purchase emails!")
            
            # Save results
            save_results(emails)
            print(f"\nResults saved to: vinyl_purchases.txt")
            
            # Display preview
            print("\nPreview of found emails:")
            print("-" * 80)
            for i, email in enumerate(emails[:5], 1):
                print(f"\n{i}. {email['subject']}")
                print(f"   From: {email['sender']}")
                print(f"   Date: {email['date']}")
                print(f"   Preview: {email['snippet'][:100]}...")
            
            if len(emails) > 5:
                print(f"\n... and {len(emails) - 5} more emails")
        else:
            print("\nNo vinyl/LP purchase emails found.")
            print("Try adjusting the search terms or checking your Gmail account.")
    
    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting tips:")
        print("- Make sure you have the correct permissions")
        print("- Check your internet connection")
        print("- Verify credentials.json is valid")

if __name__ == '__main__':
    main()