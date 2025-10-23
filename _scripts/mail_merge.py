#!/usr/bin/env python3
# /// script
# dependencies = [
#   "python-dotenv",
# ]
# ///

"""
Mail merge script for Holiday Trees email campaign.
Reads CSV data and sends personalized emails via Gmail SMTP.

Usage:
    uv run _scripts/mail_merge.py --dry-run              # Preview emails without sending
    uv run _scripts/mail_merge.py --test-email you@email.com  # Send one test email
    uv run _scripts/mail_merge.py                        # Send emails for real
"""

import csv
import smtplib
import sys
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

# Configuration
CSV_FILE = "/Users/bbriski/Downloads/WG Holiday Trees - 2025.csv"
TEMPLATE_FILE = Path(__file__).parent / "email_template.txt"
GMAIL_EMAIL = os.getenv('GMAIL_EMAIL')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

def load_template():
    """Load email template from file."""
    with open(TEMPLATE_FILE, 'r') as f:
        return f.read()

def parse_emails(email_string):
    """Parse comma-separated emails and return list."""
    if not email_string or not email_string.strip():
        return []
    return [email.strip() for email in email_string.split(',') if email.strip()]

def get_greeting_name(informal_name):
    """Get the name to use in greeting. Returns empty string if no informal name."""
    if not informal_name or not informal_name.strip():
        return ""
    # Add a space before the name so "Hi{name}," becomes "Hi Michelle," or "Hi,"
    return " " + informal_name.strip()

def read_recipients(csv_file):
    """Read CSV and return list of recipients with email addresses."""
    recipients = []
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip rows without email addresses
            email_field = row.get('Email', '').strip()
            if not email_field:
                continue
            
            # Parse potentially multiple emails
            emails = parse_emails(email_field)
            if not emails:
                continue
            
            recipient = {
                'informal_name': row.get('Informal Name', '').strip(),
                'name': row.get('Name', '').strip(),
                'house': row.get('House', '').strip(),
                'emails': emails,
                'trees': row.get('Trees', '').strip(),
                'rebar': row.get('Rebar', '').strip(),
                'cost': row.get('Cost', '').strip(),
            }
            recipients.append(recipient)
    
    return recipients

def format_last_year_details(trees, rebar, cost):
    """Format last year's order details for the email."""
    details = []
    
    # Add trees if present
    if trees and trees != '0':
        tree_count = int(trees) if trees.isdigit() else 1
        tree_text = f"{trees} tree" if tree_count == 1 else f"{trees} trees"
        details.append(tree_text)
    
    # Add rebar if present
    if rebar and rebar != '0':
        rebar_text = f"{rebar} rebar"
        details.append(rebar_text)
    
    # Build the message
    if details:
        items_text = " and ".join(details)
        if cost and cost != '$0':
            return f" ({items_text} for {cost}). If you want the same order, it'll be {cost}"
        else:
            return f" ({items_text})"
    return ""

def create_email(template, recipient, sender_email, override_email=None):
    """Create email message from template and recipient data."""
    greeting_name = get_greeting_name(recipient['informal_name'])
    
    # Format last year's order details
    last_year_details = format_last_year_details(
        recipient.get('trees', ''),
        recipient.get('rebar', ''),
        recipient.get('cost', '')
    )
    
    # Fill in template
    body_text = template.replace('{name}', greeting_name)
    body_text = body_text.replace('{last_year_details}', last_year_details)
    
    # Create HTML version with proper line breaks
    body_html = body_text.replace('\n', '<br>\n')
    body_html = f'<html><body style="font-family: Arial, sans-serif;">{body_html}</body></html>'
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    
    # Use override email if provided (for testing)
    if override_email:
        msg['To'] = override_email
    else:
        msg['To'] = ', '.join(recipient['emails'])
    
    msg['Subject'] = 'Holiday Trees 2025 - Curtiss Ave'
    
    # Attach both plain text and HTML versions
    msg.attach(MIMEText(body_text, 'plain'))
    msg.attach(MIMEText(body_html, 'html'))
    
    return msg

def send_emails(recipients, template, dry_run=False, test_email=None):
    """Send emails to all recipients."""
    if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        print("ERROR: Gmail credentials not found in .env file")
        print("Please copy .env.example to .env and fill in your credentials")
        return
    
    if test_email:
        print(f"\nTEST MODE - Sending one test email to {test_email}\n")
        recipients = [recipients[0]]  # Just use first recipient for test
    else:
        print(f"\n{'DRY RUN - ' if dry_run else ''}Found {len(recipients)} recipients with email addresses\n")
    
    if dry_run:
        print("=" * 70)
        print("PREVIEW MODE - No emails will be sent")
        print("=" * 70 + "\n")
        
        for i, recipient in enumerate(recipients, 1):
            print(f"\n--- Email {i}/{len(recipients)} ---")
            print(f"To: {', '.join(recipient['emails'])}")
            print(f"Informal Name: {recipient['informal_name']}")
            print(f"Name: {recipient['name']}")
            print(f"House: {recipient['house']}")
            print(f"Last Year: {recipient['trees']} trees, {recipient['rebar']} rebar, {recipient['cost']}")
            print(f"\nMessage Preview:")
            print("-" * 70)
            greeting_name = get_greeting_name(recipient['informal_name'])
            last_year_details = format_last_year_details(
                recipient.get('trees', ''),
                recipient.get('rebar', ''),
                recipient.get('cost', '')
            )
            body = template.replace('{name}', greeting_name)
            body = body.replace('{last_year_details}', last_year_details)
            print(body)
            print("-" * 70)
        
        print(f"\n\nDry run complete. {len(recipients)} emails would be sent.")
        print("Run without --dry-run to send for real.\n")
        return
    
    # Send for real
    try:
        print("Connecting to Gmail SMTP server...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        print("Connected successfully!\n")
        
        sent_count = 0
        failed = []
        
        for i, recipient in enumerate(recipients, 1):
            try:
                msg = create_email(template, recipient, GMAIL_EMAIL, test_email)
                server.send_message(msg)
                
                if test_email:
                    print(f"✓ Test email sent to {test_email}")
                    print(f"   (Using data from: {recipient['name']} at {recipient['house']})")
                else:
                    print(f"✓ [{i}/{len(recipients)}] Sent to {recipient['name']} ({', '.join(recipient['emails'])})")
                sent_count += 1
            except Exception as e:
                if test_email:
                    error_msg = f"✗ Failed to send test email: {str(e)}"
                else:
                    error_msg = f"✗ [{i}/{len(recipients)}] Failed to send to {recipient['name']}: {str(e)}"
                print(error_msg)
                failed.append((recipient, str(e)))
        
        server.quit()
        
        if test_email:
            print(f"\nTest email sent successfully!")
        else:
            print(f"\n{'=' * 70}")
            print(f"Summary: {sent_count} sent successfully, {len(failed)} failed")
            print(f"{'=' * 70}\n")
            
            if failed:
                print("Failed emails:")
                for recipient, error in failed:
                    print(f"  - {recipient['name']} ({', '.join(recipient['emails'])}): {error}")
        
    except Exception as e:
        print(f"\nERROR connecting to Gmail: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure you have 2-factor authentication enabled on your Gmail account")
        print("2. Generate an App Password (see GMAIL_SETUP.md)")
        print("3. Check your .env file has correct credentials")
        sys.exit(1)

def main():
    """Main function."""
    # Check for flags
    dry_run = '--dry-run' in sys.argv
    test_email = None
    
    # Check for test email flag
    if '--test-email' in sys.argv:
        try:
            idx = sys.argv.index('--test-email')
            test_email = sys.argv[idx + 1]
        except (IndexError, ValueError):
            print("ERROR: --test-email requires an email address")
            print("Usage: uv run _scripts/mail_merge.py --test-email you@example.com")
            sys.exit(1)
    
    # Check if files exist
    if not os.path.exists(CSV_FILE):
        print(f"ERROR: CSV file not found: {CSV_FILE}")
        sys.exit(1)
    
    if not TEMPLATE_FILE.exists():
        print(f"ERROR: Template file not found: {TEMPLATE_FILE}")
        sys.exit(1)
    
    # Load data
    template = load_template()
    recipients = read_recipients(CSV_FILE)
    
    if not recipients:
        print("No recipients with email addresses found in CSV file.")
        sys.exit(1)
    
    # Send emails
    send_emails(recipients, template, dry_run, test_email)

if __name__ == '__main__':
    main()

