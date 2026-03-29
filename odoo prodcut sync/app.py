"""
Odoo Product Sync Tool
Syncs products between SWAG Odoo and LaRouche Odoo via XML-RPC API.
"""

import streamlit as st
import xmlrpc.client
from typing import Optional

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Odoo Product Sync",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS — industrial/utilitarian aesthetic
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}
h1, h2, h3 {
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: -0.5px;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background: #0f1117;
    border-right: 1px solid #2a2d35;
}
section[data-testid="stSidebar"] * {
    color: #e0e0e0 !important;
}
section[data-testid="stSidebar"] .stTextInput input {
    background: #1a1d27 !important;
    border: 1px solid #2a2d35 !important;
    color: #e0e0e0 !important;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px !important;
}

/* Status dot helpers */
.dot-green { color: #00ff88; font-size: 16px; }
.dot-red   { color: #ff4444; font-size: 16px; }

/* Product card */
.product-card {
    background: #1a1d27;
    border: 1px solid #2a2d35;
    border-left: 4px solid #4f8ef7;
    border-radius: 6px;
    padding: 20px 24px;
    margin: 12px 0;
}
.product-card h4 {
    font-family: 'IBM Plex Mono', monospace;
    color: #4f8ef7;
    margin: 0 0 14px 0;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.field-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    border-bottom: 1px solid #2a2d3540;
}
.field-row:last-child { border-bottom: none; }
.field-label {
    color: #888;
    font-size: 12px;
    font-family: 'IBM Plex Mono', monospace;
    min-width: 160px;
}
.field-value {
    color: #e8e8e8;
    font-size: 14px;
    font-weight: 500;
    text-align: right;
}
.field-value.mono {
    font-family: 'IBM Plex Mono', monospace;
    color: #a8d8a8;
}

/* Bulk table */
.bulk-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
    margin-top: 16px;
}
.bulk-table th {
    background: #1a1d27;
    color: #888;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid #2a2d35;
}
.bulk-table td {
    padding: 10px 14px;
    border-bottom: 1px solid #2a2d3530;
    color: #ccc;
}
.bulk-table tr:hover td { background: #1a1d2750; }
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 600;
}
.badge-found    { background: #00ff8820; color: #00ff88; border: 1px solid #00ff8840; }
.badge-missing  { background: #ff444420; color: #ff6666; border: 1px solid #ff444440; }
.badge-synced   { background: #4f8ef720; color: #4f8ef7; border: 1px solid #4f8ef740; }
.badge-error    { background: #ff880020; color: #ff9944; border: 1px solid #ff880040; }
.badge-skipped  { background: #88888820; color: #aaaaaa; border: 1px solid #88888840; }

/* Main title */
.main-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 26px;
    font-weight: 600;
    color: #e8e8e8;
    margin-bottom: 4px;
}
.main-subtitle {
    color: #666;
    font-size: 13px;
    font-family: 'IBM Plex Mono', monospace;
    margin-bottom: 28px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DEFAULT CREDENTIALS (editable in sidebar)
# ─────────────────────────────────────────────
DEFAULTS = {
    "swag_url":      "https://swag.odoo.com",
    "swag_db":       "swag_db",
    "swag_user":     "admin@swag.com",
    "swag_pw":       "swag_password",
    "lr_url":        "https://larouche.odoo.com",
    "lr_db":         "larouche_db",
    "lr_user":       "admin@larouche.com",
    "lr_pw":         "larouche_password",
}


# ─────────────────────────────────────────────
# XML-RPC HELPERS
# ─────────────────────────────────────────────
def odoo_connect(url: str, db: str, username: str, password: str) -> tuple[Optional[int], Optional[object], Optional[str]]:
    """
    Authenticate with an Odoo instance via XML-RPC.
    Returns (uid, models_proxy, error_message).
    uid is None if connection fails.
    """
    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
        uid = common.authenticate(db, username, password, {})
        if not uid:
            return None, None, "Authentication failed — check credentials."
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
        return uid, models, None
    except Exception as e:
        return None, None, str(e)


def search_product(models, db: str, uid: int, password: str, default_code: str) -> Optional[dict]:
    """
    Search product.template by internal reference (default_code).
    Returns the first match as a dict, or None.
    Custom fields (x_season, x_brand) are fetched with fallback.
    """
    base_fields = ['name', 'default_code', 'barcode', 'compare_list_price', 'list_price', 'type']

    # Try with custom fields first
    try:
        results = models.execute_kw(
            db, uid, password,
            'product.template', 'search_read',
            [[['default_code', '=', default_code]]],
            {'fields': base_fields + ['x_season', 'x_brand'], 'limit': 1}
        )
    except Exception:
        # Fallback: without custom fields
        try:
            results = models.execute_kw(
                db, uid, password,
                'product.template', 'search_read',
                [[['default_code', '=', default_code]]],
                {'fields': base_fields, 'limit': 1}
            )
        except Exception as e:
            st.error(f"Search error: {e}")
            return None

    return results[0] if results else None


def create_product_in_larouche(
    models, db: str, uid: int, password: str, swag_product: dict
) -> tuple[Optional[int], Optional[str]]:
    """
    Create a product in LaRouche Odoo from SWAG product data.
    Returns (new_product_id, error_message).
    Gracefully skips x_season / x_brand if they don't exist.
    """
    product_data = {
        "name":             swag_product.get("name", ""),
        "default_code":     swag_product.get("default_code", ""),
        "barcode":          swag_product.get("barcode") or False,
        "list_price":       swag_product.get("compare_list_price") or swag_product.get("list_price") or 0.0,
        "type":             "product",   # storable
        "sale_ok":          True,
        "purchase_ok":      True,
    }

    # Attempt to add custom fields — skip silently if rejected
    for field in ("x_season", "x_brand"):
        val = swag_product.get(field)
        if val:
            product_data[field] = val

    try:
        new_id = models.execute_kw(db, uid, password, 'product.template', 'create', [product_data])
        return new_id, None
    except Exception as e:
        err = str(e)
        # If the error mentions a custom field, retry without it
        if "x_season" in err or "x_brand" in err:
            for f in ("x_season", "x_brand"):
                product_data.pop(f, None)
            try:
                new_id = models.execute_kw(db, uid, password, 'product.template', 'create', [product_data])
                return new_id, "Created (custom fields skipped — not available in LaRouche)"
            except Exception as e2:
                return None, str(e2)
        return None, err


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

for key in ("swag_uid", "swag_models", "lr_uid", "lr_models",
            "swag_conn_err", "lr_conn_err", "connected"):
    if key not in st.session_state:
        st.session_state[key] = None

if "connected" not in st.session_state:
    st.session_state.connected = False


# ─────────────────────────────────────────────
# SIDEBAR — Credentials & Connection Status
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    # SWAG credentials
    st.markdown("### SWAG Odoo")
    st.session_state.swag_url  = st.text_input("URL",      value=st.session_state.swag_url,  key="swag_url_input")
    st.session_state.swag_db   = st.text_input("Database", value=st.session_state.swag_db,   key="swag_db_input")
    st.session_state.swag_user = st.text_input("Username", value=st.session_state.swag_user, key="swag_user_input")
    st.session_state.swag_pw   = st.text_input("Password", value=st.session_state.swag_pw,   key="swag_pw_input",  type="password")

    st.markdown("---")

    # LaRouche credentials
    st.markdown("### LaRouche Odoo")
    st.session_state.lr_url  = st.text_input("URL",      value=st.session_state.lr_url,  key="lr_url_input")
    st.session_state.lr_db   = st.text_input("Database", value=st.session_state.lr_db,   key="lr_db_input")
    st.session_state.lr_user = st.text_input("Username", value=st.session_state.lr_user, key="lr_user_input")
    st.session_state.lr_pw   = st.text_input("Password", value=st.session_state.lr_pw,   key="lr_pw_input",  type="password")

    st.markdown("---")

    # Test Connection button
    if st.button("🔌 Test Connection", use_container_width=True):
        with st.spinner("Connecting…"):
            uid_s, mdl_s, err_s = odoo_connect(
                st.session_state.swag_url, st.session_state.swag_db,
                st.session_state.swag_user, st.session_state.swag_pw
            )
            uid_l, mdl_l, err_l = odoo_connect(
                st.session_state.lr_url, st.session_state.lr_db,
                st.session_state.lr_user, st.session_state.lr_pw
            )
            st.session_state.swag_uid    = uid_s
            st.session_state.swag_models = mdl_s
            st.session_state.swag_conn_err = err_s
            st.session_state.lr_uid      = uid_l
            st.session_state.lr_models   = mdl_l
            st.session_state.lr_conn_err = err_l
            st.session_state.connected   = bool(uid_s and uid_l)

    # Connection status indicators
    st.markdown("### Connection Status")
    swag_ok = st.session_state.swag_uid is not None
    lr_ok   = st.session_state.lr_uid   is not None

    swag_dot = "🟢" if swag_ok else "🔴"
    lr_dot   = "🟢" if lr_ok   else "🔴"

    st.markdown(f"{swag_dot} **SWAG Odoo** — {'Connected' if swag_ok else 'Not Connected'}")
    if st.session_state.swag_conn_err:
        st.caption(f"↳ {st.session_state.swag_conn_err}")

    st.markdown(f"{lr_dot} **LaRouche Odoo** — {'Connected' if lr_ok else 'Not Connected'}")
    if st.session_state.lr_conn_err:
        st.caption(f"↳ {st.session_state.lr_conn_err}")

    st.markdown("---")
    st.caption("Odoo Product Sync Tool v1.0")


# ─────────────────────────────────────────────
# MAIN AREA
# ─────────────────────────────────────────────
st.markdown('<div class="main-title">🔄 Odoo Product Sync</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">SWAG → LaRouche · XML-RPC · product.template</div>', unsafe_allow_html=True)

if not st.session_state.connected:
    st.info("👈 Fill in credentials in the sidebar and click **Test Connection** to get started.")
    st.stop()


# ─────────────────────────────────────────────
# BULK MODE TOGGLE
# ─────────────────────────────────────────────
bulk_mode = st.checkbox("📋 Bulk Mode — process multiple references at once")

st.markdown("---")


# ─────────────────────────────────────────────
# HELPER: render a product card (HTML)
# ─────────────────────────────────────────────
def render_product_card(product: dict, title: str = "Product Details"):
    fields = [
        ("Name",               product.get("name", "—")),
        ("Internal Reference", product.get("default_code", "—")),
        ("Barcode",            product.get("barcode") or "—"),
        ("Compare Price",      f"${product.get('compare_list_price', 0):.2f}" if product.get("compare_list_price") else "—"),
        ("Sale Price",         f"${product.get('list_price', 0):.2f}" if product.get("list_price") else "—"),
        ("Season (x_season)",  product.get("x_season", "—") or "—"),
        ("Brand (x_brand)",    product.get("x_brand",  "—") or "—"),
        ("Type",               product.get("type", "—")),
    ]
    rows_html = "".join(
        f'<div class="field-row">'
        f'<span class="field-label">{label}</span>'
        f'<span class="field-value{"  mono" if label in ("Internal Reference","Barcode") else ""}">{value}</span>'
        f'</div>'
        for label, value in fields
    )
    st.markdown(
        f'<div class="product-card"><h4>{title}</h4>{rows_html}</div>',
        unsafe_allow_html=True
    )


# ─────────────────────────────────────────────
# SINGLE MODE
# ─────────────────────────────────────────────
if not bulk_mode:
    ref = st.text_input(
        "Enter Model / Internal Reference",
        placeholder="e.g. CA3691",
        help="Searches product.template.default_code in SWAG Odoo"
    )

    if ref.strip():
        ref = ref.strip().upper()

        # ── Search SWAG ──
        with st.spinner(f"Searching SWAG for **{ref}**…"):
            swag_product = search_product(
                st.session_state.swag_models,
                st.session_state.swag_db,
                st.session_state.swag_uid,
                st.session_state.swag_pw,
                ref
            )

        if not swag_product:
            st.warning(f"⚠️ Product not found in SWAG with reference **{ref}**")
            st.stop()

        # Show SWAG product
        st.markdown("#### Found in SWAG")
        render_product_card(swag_product, "SWAG Product")

        # ── Check LaRouche ──
        with st.spinner("Checking LaRouche…"):
            lr_product = search_product(
                st.session_state.lr_models,
                st.session_state.lr_db,
                st.session_state.lr_uid,
                st.session_state.lr_pw,
                ref
            )

        st.markdown("#### LaRouche Status")

        if lr_product:
            st.success(f"✅ Product already exists in LaRouche (ID: {lr_product.get('id', '?')})")
            render_product_card(lr_product, "LaRouche Product (existing)")
        else:
            st.warning("⚠️ Product **not found** in LaRouche — ready to create.")

            col1, col2 = st.columns([1, 3])
            with col1:
                create_btn = st.button("➕ Create in LaRouche", type="primary", use_container_width=True)

            if create_btn:
                with st.spinner("Creating product in LaRouche…"):
                    new_id, err = create_product_in_larouche(
                        st.session_state.lr_models,
                        st.session_state.lr_db,
                        st.session_state.lr_uid,
                        st.session_state.lr_pw,
                        swag_product
                    )
                if new_id:
                    st.success(f"🎉 Product created in LaRouche! (ID: {new_id})")
                    if err:
                        st.info(f"ℹ️ Note: {err}")
                    st.balloons()
                else:
                    st.error(f"❌ Failed to create product: {err}")


# ─────────────────────────────────────────────
# BULK MODE
# ─────────────────────────────────────────────
else:
    st.markdown("#### Bulk Reference Input")
    raw_refs = st.text_area(
        "Paste Internal References (one per line)",
        placeholder="CA3691\nCA1234\nXY9999",
        height=150
    )

    auto_create = st.checkbox("Auto-create missing products in LaRouche", value=False)

    run_bulk = st.button("▶ Run Bulk Sync", type="primary")

    if run_bulk and raw_refs.strip():
        refs = [r.strip().upper() for r in raw_refs.strip().splitlines() if r.strip()]
        refs = list(dict.fromkeys(refs))  # deduplicate preserving order

        results = []  # list of dicts for the table

        progress = st.progress(0, text="Starting…")

        for i, ref in enumerate(refs):
            progress.progress((i + 1) / len(refs), text=f"Processing {ref}…")

            row = {
                "ref":        ref,
                "swag_status": "",
                "swag_product": None,
                "lr_status":  "",
                "action":     "",
            }

            # Search SWAG
            try:
                swag_p = search_product(
                    st.session_state.swag_models,
                    st.session_state.swag_db,
                    st.session_state.swag_uid,
                    st.session_state.swag_pw,
                    ref
                )
            except Exception as e:
                row["swag_status"] = "error"
                row["action"] = str(e)
                results.append(row)
                continue

            if not swag_p:
                row["swag_status"]  = "missing"
                row["lr_status"]    = "skipped"
                row["action"]       = "Not in SWAG"
                results.append(row)
                continue

            row["swag_status"]  = "found"
            row["swag_product"] = swag_p

            # Check LaRouche
            try:
                lr_p = search_product(
                    st.session_state.lr_models,
                    st.session_state.lr_db,
                    st.session_state.lr_uid,
                    st.session_state.lr_pw,
                    ref
                )
            except Exception as e:
                row["lr_status"] = "error"
                row["action"]    = str(e)
                results.append(row)
                continue

            if lr_p:
                row["lr_status"] = "found"
                row["action"]    = f"Exists (ID {lr_p.get('id','?')})"
            else:
                if auto_create:
                    new_id, err = create_product_in_larouche(
                        st.session_state.lr_models,
                        st.session_state.lr_db,
                        st.session_state.lr_uid,
                        st.session_state.lr_pw,
                        swag_p
                    )
                    if new_id:
                        row["lr_status"] = "synced"
                        row["action"]    = f"Created (ID {new_id})" + (f" — {err}" if err else "")
                    else:
                        row["lr_status"] = "error"
                        row["action"]    = err or "Create failed"
                else:
                    row["lr_status"] = "missing"
                    row["action"]    = "Not in LaRouche"

            results.append(row)

        progress.empty()

        # ── Render results table ──
        badge_map = {
            "found":   "badge-found",
            "missing": "badge-missing",
            "synced":  "badge-synced",
            "error":   "badge-error",
            "skipped": "badge-skipped",
        }

        rows_html = ""
        for r in results:
            swag_cls = badge_map.get(r["swag_status"], "badge-skipped")
            lr_cls   = badge_map.get(r["lr_status"],   "badge-skipped")
            rows_html += (
                f"<tr>"
                f"<td><code>{r['ref']}</code></td>"
                f"<td><span class='badge {swag_cls}'>{r['swag_status'] or '—'}</span></td>"
                f"<td><span class='badge {lr_cls}'>{r['lr_status'] or '—'}</span></td>"
                f"<td>{r['action']}</td>"
                f"</tr>"
            )

        table_html = f"""
        <table class="bulk-table">
          <thead>
            <tr>
              <th>Reference</th>
              <th>SWAG Status</th>
              <th>LaRouche Status</th>
              <th>Action / Notes</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
        """
        st.markdown(table_html, unsafe_allow_html=True)

        # Summary stats
        total    = len(results)
        synced   = sum(1 for r in results if r["lr_status"] == "synced")
        existing = sum(1 for r in results if r["lr_status"] == "found")
        missing  = sum(1 for r in results if r["lr_status"] == "missing")
        errors   = sum(1 for r in results if r["lr_status"] == "error" or r["swag_status"] == "error")

        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Refs",     total)
        c2.metric("✅ Already Sync", existing)
        c3.metric("🆕 Created",      synced)
        c4.metric("⚠️ Missing / Err", missing + errors)

        if synced > 0 and auto_create:
            st.balloons()
