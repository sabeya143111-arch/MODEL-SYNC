# 🔄 Odoo Product Sync Tool

A Streamlit-based web application for syncing products between two Odoo instances (**SWAG** → **LaRouche**) using the XML-RPC API.

---

## Features

- 🔍 Search products in SWAG Odoo by Internal Reference (`default_code`)
- ✅ Check if the same product exists in LaRouche Odoo
- ➕ Create missing products in LaRouche with one click
- 📋 Bulk Mode — process multiple references at once
- 🟢 Live connection status for both Odoo instances
- 🛡️ Graceful handling of custom fields (`x_season`, `x_brand`)

---

## Requirements

- Python 3.8+
- Streamlit (`pip install streamlit`)
- `xmlrpc.client` — built into Python standard library (no install needed)

---

## Installation & Run

```bash
# 1. Clone the repository
git clone https://github.com/your-org/odoo-product-sync.git
cd odoo-product-sync

# 2. (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501` in your browser.

---

## Configuration

Fill in credentials in the **sidebar** of the app:

| Field    | SWAG Odoo              | LaRouche Odoo              |
|----------|------------------------|----------------------------|
| URL      | https://swag.odoo.com  | https://larouche.odoo.com  |
| Database | swag_db                | larouche_db                |
| Username | admin@swag.com         | admin@larouche.com         |
| Password | *(your password)*      | *(your password)*          |

Click **Test Connection** to verify both instances are reachable.

---

## Usage

### Single Mode
1. Enter an Internal Reference (e.g. `CA3691`) in the search box
2. View the SWAG product details
3. See the LaRouche status — if missing, click **Create in LaRouche**

### Bulk Mode
1. Check **Bulk Mode**
2. Paste multiple references (one per line)
3. Optionally enable **Auto-create missing products**
4. Click **Run Bulk Sync** — results appear in a colour-coded table

---

## Project Structure

```
odoo-product-sync/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── .gitignore          # Git ignore rules
```

---

## Notes

- Custom fields `x_season` and `x_brand` are optional — the app skips them silently if they don't exist in the target Odoo instance.
- All XML-RPC calls are wrapped in try/except for safe error handling.
- No third-party Odoo libraries are used — only Python's built-in `xmlrpc.client`.

---

## License

MIT
