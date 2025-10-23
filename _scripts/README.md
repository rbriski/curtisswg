# Holiday Trees Mail Merge

This directory contains scripts for sending holiday tree emails to customers from previous years.

## Quick Start

1. **Setup Gmail** (first time only):
   - Follow instructions in `GMAIL_SETUP.md` to generate an App Password
   - Copy `.env.example` to `.env` and fill in your credentials

2. **Preview emails** (dry run):
   ```bash
   uv run _scripts/mail_merge.py --dry-run
   ```

3. **Send a test email** (recommended):
   ```bash
   uv run _scripts/mail_merge.py --test-email your@email.com
   ```

4. **Send emails for real**:
   ```bash
   uv run _scripts/mail_merge.py
   ```

## Files

- `mail_merge.py` - Main script that reads CSV and sends emails
- `email_template.txt` - Email template (edit this to customize the message)
- `.env.example` - Template for Gmail credentials
- `.env` - Your actual credentials (create this, not in git)
- `GMAIL_SETUP.md` - Detailed setup instructions
- `README.md` - This file

## How It Works

1. Reads customer data from `~/Downloads/WG Holiday Trees - 2025.csv`
2. Filters to only customers with email addresses
3. Personalizes each email with:
   - Informal name (or no name if not provided)
   - Last year's order details (trees, rebar, cost)
4. Sends via Gmail SMTP using your credentials
5. Shows progress and reports any failures

## Features

- ✓ Personalizes with informal names from CSV
- ✓ Includes last year's order details (trees, rebar, cost)
- ✓ Handles multiple comma-separated email addresses
- ✓ Test mode to send one email before bulk sending
- ✓ Dry-run mode to preview before sending
- ✓ Progress tracking during send
- ✓ Error handling and reporting
- ✓ Uses `uv` with inline dependencies (no venv needed)
- ✓ Skips empty rows and rows without emails automatically

## Customizing the Email

Edit `email_template.txt` to change the email content. Available placeholders:
- `{name}` - Recipient's informal name (or empty if not provided)
- `{last_year_details}` - Formatted details from last year's order

After editing, always do a dry run first to preview the changes:
```bash
uv run _scripts/mail_merge.py --dry-run
```

Or send yourself a test:
```bash
uv run _scripts/mail_merge.py --test-email your@email.com
```

