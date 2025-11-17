# EMAIL IMPORT SETUP

Your server is back! Here's how to start importing emails.

## 🔧 SETUP

### 1. Configure .env file

Add these to your `.env` file in the repo root:

```bash
# Email Server (Axigen IMAP)
EMAIL_SERVER=your-axigen-server.com
EMAIL_PORT=993
EMAIL_USER=brian@bensleydesign.com
EMAIL_PASSWORD=your_password_here

# Database
DATABASE_PATH=database/bensley_master.db

# Optional: Attachments directory
ATTACHMENTS_DIR=/Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/BY_DATE
```

### 2. Test Connection

```bash
python3 start_email_import.py
```

This will:
1. ✅ Check your configuration
2. ✅ Test connection to Axigen server
3. ✅ List available folders
4. ✅ Let you choose how many emails to import

## 📧 WHAT GETS IMPORTED

The `EmailImporter` class in `backend/services/email_importer.py` imports:

- **Email metadata**: Subject, sender, recipients, date
- **Email body**: Full text content
- **Attachments**: Downloads to BDS_SYSTEM/05_FILES/BY_DATE/{YYYY-MM}/
- **Threading**: Groups emails into conversations
- **Project linking**: Auto-links emails to projects based on codes (BK-XXX)

## 🔄 IMPORT OPTIONS

### Quick Test (50 emails):
```bash
python3 start_email_import.py
# Choose option 1
```

### Standard Import (100 emails):
```bash
python3 start_email_import.py
# Choose option 2
```

### Large Import (500 emails):
```bash
python3 start_email_import.py
# Choose option 3
```

### Full Import (ALL emails - may take hours):
```bash
python3 start_email_import.py
# Choose option 4
```

## 🤖 AFTER IMPORT

Once emails are imported, they'll be automatically:

1. **Categorized** by `smart_email_matcher.py`:
   - Project updates
   - RFIs
   - Invoices
   - Proposals
   - Meeting schedules

2. **Linked to projects** based on project codes

3. **Processed for attachments** (PDFs, images, etc.)

4. **Queryable** via bensley_brain.py:
   ```bash
   python3 bensley_brain.py "show me recent emails about BK-070"
   ```

## 🔐 SECURITY

- `.env` file is gitignored (never committed)
- Passwords stored locally only
- IMAP uses SSL/TLS (port 993)

## 🐛 TROUBLESHOOTING

### "Connection failed"
- Check server status: Is Axigen running?
- Verify credentials in .env
- Test port 993 is open: `telnet your-server.com 993`

### "Module not found"
```bash
pip3 install python-dotenv
```

### "Database locked"
- Close any programs accessing the database
- Stop the API server temporarily

## 📊 CURRENT STATUS

- **Email importer**: ✅ Ready
- **Smart matcher**: ✅ Ready (categorizes emails)
- **Attachment downloader**: ✅ Ready
- **Server connection**: ⏳ Waiting for your .env config

---

**Next:** Once you've added the email config to `.env`, run `python3 start_email_import.py` to test!
