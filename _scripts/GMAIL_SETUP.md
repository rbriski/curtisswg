# Gmail Setup Instructions

This guide will walk you through setting up Gmail to send emails via the mail merge script.

## Prerequisites

You need a Gmail account with 2-Factor Authentication (2FA) enabled.

## Step 1: Enable 2-Factor Authentication

If you don't already have 2FA enabled:

1. Go to your [Google Account Security page](https://myaccount.google.com/security)
2. Under "How you sign in to Google", click on "2-Step Verification"
3. Follow the prompts to set up 2FA (you can use your phone, Google Authenticator, etc.)

## Step 2: Generate an App Password

An App Password is a special password that lets the script access Gmail without using your main password.

1. Go to your [Google Account App Passwords page](https://myaccount.google.com/apppasswords)
   - Or: Google Account → Security → 2-Step Verification → App passwords
2. You may need to sign in again
3. Under "Select app", choose "Mail"
4. Under "Select device", choose "Other (Custom name)"
5. Type a name like "Holiday Trees Mail Merge"
6. Click "Generate"
7. Google will show you a 16-character password (example: `abcd efgh ijkl mnop`)
8. **Copy this password** - you won't be able to see it again!

## Step 3: Configure the Script

1. In the `_scripts/` directory, copy the example configuration:
   ```bash
   cd _scripts
   cp .env.example .env
   ```

2. Open the `.env` file in a text editor

3. Fill in your credentials:
   ```
   GMAIL_EMAIL=your.actual.email@gmail.com
   GMAIL_APP_PASSWORD=abcdefghijklmnop
   ```
   
   **Note**: Remove the spaces from the app password (it should be one continuous string)

4. Save the file

## Step 4: Test the Script

Before sending emails for real, do a dry run to preview what will be sent:

```bash
uv run _scripts/mail_merge.py --dry-run
```

This will show you:
- How many recipients will receive emails
- Preview of each email that will be sent
- Who will receive each email

Review the output carefully!

## Step 5: Send Emails

When you're ready to send the emails for real:

```bash
uv run _scripts/mail_merge.py
```

The script will:
- Connect to Gmail
- Send emails one by one
- Show progress as it goes
- Report any failures at the end

## Troubleshooting

### "Login failed" or "Authentication failed"

1. Double-check your Gmail email address in `.env`
2. Make sure you copied the App Password correctly (no spaces)
3. Verify 2FA is enabled on your Google account
4. Try generating a new App Password

### "Connection refused" or "Connection timeout"

1. Check your internet connection
2. Make sure your firewall isn't blocking port 587
3. Try again - sometimes Gmail's servers are temporarily busy

### Rate Limiting

Gmail has sending limits to prevent spam:
- ~500 emails per day for regular Gmail accounts
- ~2000 emails per day for Google Workspace accounts

For 20-30 emails, you'll be well under the limit.

## Security Notes

- **Never commit the `.env` file to git** - it contains your password!
- The `.env` file is already in `.gitignore` for your protection
- If you suspect your App Password was compromised, revoke it in your Google Account settings and generate a new one
- App Passwords are safer than your main password because they can be revoked individually

## Additional Resources

- [Google Account Security](https://myaccount.google.com/security)
- [About App Passwords](https://support.google.com/accounts/answer/185833)

