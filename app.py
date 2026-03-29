import xmlrpc.client
import streamlit as st

def get_connection(instance_key):
    """
    instance_key = "SWAG" ya "LAROUCHE"
    Returns (models, db, uid, api_key) tuple
    """
    cfg = st.secrets[instance_key]
    url     = cfg["url"]
    db      = cfg["db"]
    user    = cfg["user"]
    api_key = cfg["api_key"]

    # XML-RPC endpoints
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    # Authenticate using api_key as password
    uid = common.authenticate(db, user, api_key, {})

    if not uid:
        raise Exception(f"❌ {instance_key} Odoo mein login fail hua!")

    return models, db, uid, api_key


def search_product(models, db, uid, api_key, internal_ref):
    """SWAG se product dhundho by internal reference"""
    result = models.execute_kw(
        db, uid, api_key,
        'product.template', 'search_read',
        [[['default_code', '=', internal_ref]]],
        {'fields': [
            'name', 'default_code', 'barcode',
            'compare_list_price', 'x_season', 'x_brand'
        ], 'limit': 1}
    )
    return result[0] if result else None


def check_in_larouche(models, db, uid, api_key, internal_ref):
    """LaRouche mein check karo product exist karta hai ya nahi"""
    result = models.execute_kw(
        db, uid, api_key,
        'product.template', 'search_read',
        [[['default_code', '=', internal_ref]]],
        {'fields': ['id', 'name', 'default_code'], 'limit': 1}
    )
    return result[0] if result else None


def create_in_larouche(models, db, uid, api_key, swag_product):
    """SWAG product data se LaRouche mein create karo"""
    product_data = {
        'name':         swag_product.get('name', ''),
        'default_code': swag_product.get('default_code', ''),
        'barcode':      swag_product.get('barcode', False),
        'list_price':   swag_product.get('compare_list_price', 0.0),
        'type':         'product',
        'sale_ok':      True,
        'purchase_ok':  True,
    }

    # Custom fields — agar exist karte hain to add karo
    for field in ['x_season', 'x_brand']:
        val = swag_product.get(field)
        if val:
            product_data[field] = val

    new_id = models.execute_kw(
        db, uid, api_key,
        'product.template', 'create',
        [product_data]
    )
    return new_id


# ─── STREAMLIT UI ───────────────────────────────────────────────
st.set_page_config(page_title="Odoo Product Sync", page_icon="🔄", layout="wide")
st.title("🔄 Odoo Product Sync")
st.caption("SWAG → La Rouche Product Synchronization")

# Connection Test
st.sidebar.header("🔌 Connection Status")

@st.cache_resource
def load_connections():
    try:
        swag = get_connection("SWAG")
        swag_ok = True
    except Exception as e:
        swag = None
        swag_ok = str(e)

    try:
        lr = get_connection("LAROUCHE")
        lr_ok = True
    except Exception as e:
        lr = None
        lr_ok = str(e)

    return swag, swag_ok, lr, lr_ok

swag_conn, swag_status, lr_conn, lr_status = load_connections()

# Sidebar status
if swag_status is True:
    st.sidebar.success("✅ SWAG Connected")
else:
    st.sidebar.error(f"❌ SWAG: {swag_status}")

if lr_status is True:
    st.sidebar.success("✅ La Rouche Connected")
else:
    st.sidebar.error(f"❌ La Rouche: {lr_status}")

if st.sidebar.button("🔄 Reconnect"):
    st.cache_resource.clear()
    st.rerun()

# ─── Main Search ────────────────────────────────────────────────
st.divider()
ref = st.text_input(
    "🔍 Enter Internal Reference (Model Number)",
    placeholder="e.g. CA3691",
    help="SWAG Odoo mein product dhundho"
)

if ref and st.button("Search & Sync", type="primary"):
    if swag_status is not True or lr_status is not True:
        st.error("❌ Dono Odoo connected nahi hain. Sidebar check karo.")
    else:
        swag_models, swag_db, swag_uid, swag_key = swag_conn
        lr_models, lr_db, lr_uid, lr_key = lr_conn

        with st.spinner("SWAG mein search kar raha hoon..."):
            swag_prod = search_product(swag_models, swag_db, swag_uid, swag_key, ref)

        if not swag_prod:
            st.warning(f"⚠️ SWAG mein `{ref}` nahi mila!")
        else:
            st.subheader("📦 SWAG Product Data")
            col1, col2, col3 = st.columns(3)
            col1.metric("Name", swag_prod.get('name', '-'))
            col2.metric("Internal Ref", swag_prod.get('default_code', '-'))
            col3.metric("Barcode", swag_prod.get('barcode') or '-')

            col4, col5, col6 = st.columns(3)
            col4.metric("Compare Price → Sale Price", swag_prod.get('compare_list_price', 0))
            col5.metric("Season", swag_prod.get('x_season') or '-')
            col6.metric("Brand", swag_prod.get('x_brand') or '-')

            st.divider()

            with st.spinner("La Rouche mein check kar raha hoon..."):
                lr_prod = check_in_larouche(lr_models, lr_db, lr_uid, lr_key, ref)

            if lr_prod:
                st.success(f"✅ La Rouche mein already exist karta hai! (ID: {lr_prod['id']})")
            else:
                st.warning(f"⚠️ La Rouche mein `{ref}` nahi mila.")
                if st.button("➕ Create in La Rouche", type="primary"):
                    with st.spinner("Create kar raha hoon..."):
                        try:
                            new_id = create_in_larouche(
                                lr_models, lr_db, lr_uid, lr_key, swag_prod
                            )
                            st.success(f"🎉 Product create ho gaya! La Rouche ID: {new_id}")
                            st.balloons()
                        except Exception as e:
                            st.error(f"❌ Create fail: {e}")
