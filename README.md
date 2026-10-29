# RightShip Inspector Performance Dashboard — starter

This is a starter implementation, not a production-ready deployment. It provides a browser-based dashboard and a first-pass parser for Excel/CSV, text-based PDFs, and DOCX reports.

## Recommended company deployment

For access from multiple HSQE users, deploy this app on an IT-managed internal server or approved VM. Configure the app to read a **shared company folder** (SMB/network share or an approved synced SharePoint/OneDrive folder). Do not run it only on one employee's desktop if the team needs continuous access.

Suggested flow:
1. Company shared folder receives inspection reports.
2. App server reads the folder on a schedule / refresh.
3. Data is normalized and checked for duplicates.
4. Dashboard is published internally behind company authentication/VPN.

The current starter rescans the folder when the dashboard loads or is refreshed. It does not yet maintain a persistent database, automated scheduled ingestion, user authentication, or audit logs. These should be added and approved by IT before production use.

## Run locally for a proof of concept

Python 3.11+ recommended.

```bash
python -m venv .venv
```

Windows:
```bat
.venv\Scripts\activate
pip install -r requirements.txt
set RIGHTSHIP_REPORTS_DIR=C:\Path\To\Shared\RightShipReports
streamlit run app.py
```

macOS/Linux:
```bash
source .venv/bin/activate
pip install -r requirements.txt
export RIGHTSHIP_REPORTS_DIR="/path/to/shared/RightShipReports"
streamlit run app.py
```

The app opens in a browser. For a team deployment, IT should configure the service and internal URL; do not expose the port directly to the public internet.

## Important extraction limitations

- Excel/CSV works best when a row represents one inspection and columns clearly identify inspector, location, vessel, date and finding count.
- PDF and DOCX extraction uses basic label matching. RightShip report layouts vary, so the actual files must be tested and parsing rules adapted to your templates.
- Scanned PDFs need OCR, which is not included.
- Legacy `.doc` files should be converted to `.docx` or searchable PDF.
- A count of findings must not be inferred from ambiguous prose. Verify the extracted data against source reports.
- Duplicate detection and persistent history are not yet implemented in this proof of concept. Do not use the current aggregate results for formal performance decisions without validation.

## Production checklist

- [ ] Confirm approved shared folder path and service-account read permissions.
- [ ] Test parser against representative reports from each template/version.
- [ ] Agree on canonical definitions for inspector, inspection, finding, location and date.
- [ ] Add persistent database, file hash tracking, duplicate handling and processing log.
- [ ] Add OCR only if scanned PDFs are common and company policy permits it.
- [ ] Add company authentication, access control, backups and monitoring.
- [ ] Validate dashboard numbers against a manually checked sample before operational use.
