
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ==========================================
# 1. KONFIGURASI DASHBOARD
# ==========================================

st.set_page_config(
    page_title="E-Commerce Analysis Dashboard",
    page_icon="🛒",
    layout="wide"
)

st.title("E-Commerce Public Dataset")
st.subheader("Sales Performance & Customer Analysis")

st.markdown("""
Dashboard ini menyajikan analisis tren penjualan,
kontribusi kategori produk, dan segmentasi pelanggan
berdasarkan data transaksi E-Commerce.
""")

# ==========================================
# 2. MEMBACA DATASET
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "ecommerce_data"

@st.cache_data
def load_data():
    orders = pd.read_csv(
        DATA_DIR / "orders_dataset.csv"
    )

    order_items = pd.read_csv(
        DATA_DIR / "order_items_dataset.csv"
    )

    customers = pd.read_csv(
        DATA_DIR / "customers_dataset.csv"
    )

    products = pd.read_csv(
        DATA_DIR / "products_dataset.csv"
    )

    category_translation = pd.read_csv(
        DATA_DIR / "product_category_name_translation.csv"
    )

    return (
        orders,
        order_items,
        customers,
        products,
        category_translation
    )

try:
    (
        orders_df,
        order_items_df,
        customers_df,
        products_df,
        category_translation_df
    ) = load_data()

    st.success("Dataset berhasil dimuat.")

except Exception as e:
    st.error(f"Gagal memuat dataset: {e}")
    st.stop()



# Mengubah kolom tanggal menjadi datetime
orders_df['order_purchase_timestamp'] = pd.to_datetime(
    orders_df['order_purchase_timestamp'],
    errors='coerce'
)

# Mengambil transaksi berstatus delivered
delivered_orders = orders_df[
    (orders_df['order_status'] == 'delivered') &
    (orders_df['order_purchase_timestamp'].notna()) &
    (orders_df['order_delivered_customer_date'].notna())
].copy()


# ==========================================
# 2A. FILTER RENTANG TANGGAL ANALISIS
# ==========================================

# Batas tanggal diambil dari transaksi delivered yang valid.
min_date = delivered_orders['order_purchase_timestamp'].min().date()
max_date = delivered_orders['order_purchase_timestamp'].max().date()

# Ambil periode terakhir yang sudah diproses dari URL.
# Jika belum ada, gunakan seluruh rentang tanggal dataset.
def get_query_date(param_name, default_date):
    try:
        query_value = st.query_params.get(param_name)
        if query_value:
            parsed_date = pd.to_datetime(query_value, format="%Y-%m-%d").date()
            if min_date <= parsed_date <= max_date:
                return parsed_date
    except (ValueError, TypeError):
        pass

    return default_date


default_start_date = get_query_date("start_date", min_date)
default_end_date = get_query_date("end_date", max_date)

st.subheader("Periode Analisis")

with st.form("date_filter_form"):
    date_col1, date_col2 = st.columns(2)

    with date_col1:
        input_start_date = st.date_input(
            "Tanggal Awal",
            value=default_start_date,
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY",
            key="filter_start_date"
        )

    with date_col2:
        input_end_date = st.date_input(
            "Tanggal Akhir",
            value=default_end_date,
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY",
            key="filter_end_date"
        )

    process_filter = st.form_submit_button(
        "Proses Analisis",
        type="primary",
        use_container_width=True
    )

# Terapkan periode hanya ketika tombol ditekan.
# Pada pemuatan pertama, gunakan periode yang tersimpan di URL
# atau seluruh rentang data jika URL belum memiliki parameter.
if "applied_start_date" not in st.session_state:
    st.session_state.applied_start_date = default_start_date

if "applied_end_date" not in st.session_state:
    st.session_state.applied_end_date = default_end_date

if process_filter:
    if input_start_date > input_end_date:
        st.error("Tanggal awal tidak boleh melewati tanggal akhir.")
    else:
        st.session_state.applied_start_date = input_start_date
        st.session_state.applied_end_date = input_end_date

        # Simpan periode yang sudah diproses ke URL agar tetap
        # tersedia ketika halaman di-refresh atau dibuka kembali.
        st.query_params["start_date"] = input_start_date.isoformat()
        st.query_params["end_date"] = input_end_date.isoformat()

selected_start_date = st.session_state.applied_start_date
selected_end_date = st.session_state.applied_end_date

# Batas akhir dibuat eksklusif agar seluruh transaksi pada
# tanggal akhir pilihan tetap ikut dihitung.
period_start = pd.Timestamp(selected_start_date)
period_end_exclusive = pd.Timestamp(selected_end_date) + pd.Timedelta(days=1)

st.caption(
    f"Periode aktif: **{selected_start_date.strftime('%d %b %y')} "
    f"- {selected_end_date.strftime('%d %b %y')}**"
)
st.caption(
    f"Rentang data tersedia: {min_date.strftime('%d %b %y')} "
    f"s.d. {max_date.strftime('%d %b %y')}"
)

# ==========================================
# 3. ANALISIS TREN PENJUALAN
# ==========================================

st.divider()

st.header("Pertanyaan 1: Tren Penjualan")

st.subheader("Bagaimana Perkembangan Tren Penjualan Bulanan?")

st.markdown(
    f"""
Visualisasi ini menampilkan perkembangan nilai penjualan bulanan selama
**{selected_start_date.strftime('%d %b %y')} hingga
{selected_end_date.strftime('%d %b %y')}**. Nilai penjualan dihitung berdasarkan
total harga produk (`price`) dari pesanan berstatus delivered, tanpa memasukkan
biaya pengiriman.
"""
)

# Menggabungkan data pesanan dengan item transaksi
sales_df = delivered_orders[
    ['order_id', 'order_purchase_timestamp']
].merge(
    order_items_df[['order_id', 'price']],
    on='order_id',
    how='inner'
)

# Filter berdasarkan periode yang dipilih dan sudah diproses pengguna
sales_df = sales_df[
    (sales_df['order_purchase_timestamp'] >= period_start) &
    (sales_df['order_purchase_timestamp'] < period_end_exclusive)
].copy()

# Menghitung penjualan bulanan
sales_df['month'] = (
    sales_df['order_purchase_timestamp']
    .dt.to_period('M')
)

monthly_sales = (
    sales_df.groupby('month')
    .agg(
        total_sales=('price', 'sum'),
        total_orders=('order_id', 'nunique')
    )
    .reset_index()
)

monthly_sales['month'] = monthly_sales['month'].astype(str)

# Menampilkan KPI
col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Total Penjualan",
        f"R$ {monthly_sales['total_sales'].sum():,.2f}"
    )

with col2:
    st.metric(
        "Total Pesanan",
        f"{monthly_sales['total_orders'].sum():,}"
    )


# Grafik tren penjualan
fig, ax = plt.subplots(figsize=(12, 4.7))

ax.plot(
    monthly_sales['month'],
    monthly_sales['total_sales'] / 1_000_000,
    marker='o',
    linewidth=2
)

ax.set_title(
    f"Tren Penjualan Bulanan "
    f"({selected_start_date.strftime('%d %b %y')} - "
    f"{selected_end_date.strftime('%d %b %y')})"
)
ax.set_xlabel("Bulan")
ax.set_ylabel("Total Penjualan (Juta R$)")
ax.tick_params(axis='x', rotation=45)
ax.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()
st.pyplot(fig, width="content")

st.markdown("#### Explanatory Analysis")

if monthly_sales.empty:
    st.info(
        "Tidak terdapat transaksi delivered pada periode yang dipilih, "
        "sehingga tren penjualan bulanan belum dapat dianalisis."
    )
else:
    highest_month = monthly_sales.loc[monthly_sales['total_sales'].idxmax()]
    lowest_month = monthly_sales.loc[monthly_sales['total_sales'].idxmin()]
    first_month = monthly_sales.iloc[0]
    last_month = monthly_sales.iloc[-1]

    average_monthly_sales = monthly_sales['total_sales'].mean()

    # Ubah label bulan YYYY-MM menjadi nama bulan berbahasa Indonesia.
    month_names = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }

    def format_month_label(month_value):
        month_date = pd.to_datetime(f"{month_value}-01")
        return f"{month_names[month_date.month]} {month_date.year}"

    highest_month_label = format_month_label(highest_month['month'])
    lowest_month_label = format_month_label(lowest_month['month'])
    first_month_label = format_month_label(first_month['month'])
    last_month_label = format_month_label(last_month['month'])

    if first_month['total_sales'] != 0:
        period_change_pct = (
            (last_month['total_sales'] - first_month['total_sales'])
            / first_month['total_sales'] * 100
        )
        period_change_text = (
            f"Penjualan pada bulan terakhir **{last_month_label}** "
            f"{'meningkat' if period_change_pct >= 0 else 'menurun'} "
            f"{abs(period_change_pct):.2f}% dibandingkan bulan pertama "
            f"**{first_month_label}**."
        )
    else:
        period_change_text = (
            "Perbandingan persentase antara bulan pertama dan terakhir "
            "tidak dapat dihitung karena nilai penjualan bulan pertama nol."
        )

    st.markdown(
        f"""
Berdasarkan transaksi pada periode **{selected_start_date.strftime('%d %b %y')}
hingga {selected_end_date.strftime('%d %b %y')}**, berikut ringkasan
perkembangan penjualan:

- **Rata-rata penjualan bulanan:** R$ {average_monthly_sales:,.2f}.
- **Penjualan tertinggi:** terjadi pada **{highest_month_label}**
  sebesar R$ {highest_month['total_sales']:,.2f}.
- **Penjualan terendah:** terjadi pada **{lowest_month_label}**
  sebesar R$ {lowest_month['total_sales']:,.2f}.

{period_change_text}
"""
    )

plt.close(fig)



# ==========================================
# 4. ANALISIS KATEGORI PRODUK
# ==========================================

st.divider()

st.header("Pertanyaan 2: Kategori Produk")

st.subheader("Kategori Produk Apa yang Memberikan Kontribusi Nilai Penjualan Terbesar?")

st.markdown(
    f"""
Visualisasi ini menampilkan 10 kategori produk dengan nilai penjualan tertinggi
selama **{selected_start_date.strftime('%d %b %y')} hingga
{selected_end_date.strftime('%d %b %y')}**. Nilai penjualan dihitung berdasarkan
total harga produk (`price`), tanpa memasukkan biaya pengiriman.
"""
)

# Mengambil pesanan sesuai periode yang dipilih pengguna
orders_category = delivered_orders[
    (delivered_orders['order_purchase_timestamp'] >= period_start) &
    (delivered_orders['order_purchase_timestamp'] < period_end_exclusive)
][['order_id']].copy()

# Menggabungkan transaksi dengan informasi kategori produk
category_sales_df = (
    order_items_df
    .merge(orders_category, on='order_id', how='inner')
    .merge(
        products_df[['product_id', 'product_category_name']],
        on='product_id',
        how='left'
    )
    .merge(
        category_translation_df,
        on='product_category_name',
        how='left'
    )
)

# Menghitung penjualan berdasarkan kategori
category_sales = (
    category_sales_df
    .dropna(subset=['product_category_name_english'])
    .groupby('product_category_name_english')
    .agg(
        total_sales=('price', 'sum'),
        total_items=('order_item_id', 'count')
    )
    .reset_index()
    .sort_values('total_sales', ascending=False)
)

# Menghitung persentase kontribusi penjualan
category_sales['sales_percentage'] = (
    category_sales['total_sales'] /
    category_sales['total_sales'].sum() * 100
)

# Mengambil 10 kategori teratas
top_categories = category_sales.head(10).sort_values(
    'total_sales',
    ascending=True
)

# KPI kategori teratas
top_category = category_sales.iloc[0]

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Kategori Penjualan Tertinggi",
        top_category['product_category_name_english']
    )

with col2:
    st.metric(
        "Kontribusi Penjualan",
        f"{top_category['sales_percentage']:.2f}%"
    )


# Grafik 10 kategori teratas
fig, ax = plt.subplots(figsize=(12, 4.7))

# Konversi nilai penjualan ke satuan juta
top_categories_plot = top_categories.copy()
top_categories_plot['sales_million'] = (
    top_categories_plot['total_sales'] / 1_000_000
)

# Warna khusus untuk kategori tertinggi pada periode terpilih
highest_category = category_sales.iloc[0]['product_category_name_english']

colors = [
    '#F4A261' if category == highest_category else '#A9B9C9'
    for category in top_categories_plot[
        'product_category_name_english'
    ]
]

bars = ax.barh(
    top_categories_plot['product_category_name_english'],
    top_categories_plot['sales_million'],
    color=colors
)

# Menampilkan nilai di ujung batang
ax.bar_label(
    bars,
    fmt='%.2f',
    padding=5,
    fontsize=9
)

ax.set_title(
    f"10 Kategori Produk dengan Nilai Penjualan Tertinggi "
    f"({selected_start_date.strftime('%d %b %y')} - "
    f"{selected_end_date.strftime('%d %b %y')})"
)
ax.set_xlabel("Total Penjualan (Juta R$)")
ax.set_ylabel("Kategori Produk")
ax.grid(axis='x', linestyle='--', alpha=0.5)
ax.set_axisbelow(True)

# Memberikan ruang untuk label angka
ax.set_xlim(
    0,
    top_categories_plot['sales_million'].max() * 1.12
)

plt.tight_layout()
st.pyplot(fig, width="content")
st.markdown("#### Explanatory Analysis")

# Menyusun penjelasan berdasarkan hasil perhitungan periode terpilih.
if category_sales.empty:
    st.info(
        "Tidak terdapat data kategori produk yang dapat dianalisis "
        "pada periode yang dipilih."
    )
else:
    top_three = category_sales.head(3)
    top_three_lines = []

    for rank, (_, row) in enumerate(top_three.iterrows(), start=1):
        top_three_lines.append(
            f"{rank}. **{row['product_category_name_english']}** — "
            f"kontribusi {row['sales_percentage']:.2f}% "
            f"dengan {int(row['total_items']):,} item terjual."
        )

    highest_item_category = category_sales.loc[
        category_sales['total_items'].idxmax()
    ]
    highest_sales_category = category_sales.iloc[0]

    if (
        highest_item_category['product_category_name_english']
        == highest_sales_category['product_category_name_english']
    ):
        item_insight = (
            f"Kategori **{highest_item_category['product_category_name_english']}** "
            f"menjadi kategori dengan jumlah item terjual terbanyak sekaligus "
            f"nilai penjualan tertinggi, yaitu "
            f"{int(highest_item_category['total_items']):,} item."
        )
    else:
        item_insight = (
            f"Kategori dengan jumlah item terjual terbanyak adalah "
            f"**{highest_item_category['product_category_name_english']}**, "
            f"sebanyak {int(highest_item_category['total_items']):,} item. "
            f"Kategori ini berbeda dari kategori dengan nilai penjualan tertinggi, "
            f"yaitu **{highest_sales_category['product_category_name_english']}**. "
            f"Hal ini menunjukkan bahwa jumlah item terjual yang lebih banyak "
            f"tidak selalu menghasilkan nilai penjualan terbesar."
        )

    st.markdown(
        f"""
Berdasarkan transaksi pada periode **{selected_start_date.strftime('%d %b %y')}
hingga {selected_end_date.strftime('%d %b %y')}**, tiga kategori dengan
kontribusi nilai penjualan terbesar adalah:

{chr(10).join(top_three_lines)}

{item_insight}
"""
    )
plt.close(fig)



# ==========================================
# 5. SEGMENTASI PELANGGAN RFM
# ==========================================

st.divider()

st.header("Pertanyaan 3: Segmentasi Pelanggan")

st.subheader("Bagaimana Karakteristik Pelanggan Berdasarkan Recency, Frequency, dan Monetary?")

st.markdown(
    f"""
Visualisasi ini menampilkan distribusi pelanggan berdasarkan hasil segmentasi
RFM selama periode **{selected_start_date.strftime('%d %b %y')} hingga
{selected_end_date.strftime('%d %b %y')}**. Segmentasi dilakukan menggunakan
nilai Recency, Frequency, dan Monetary dari transaksi berstatus delivered.
"""
)

# Pilihan batas dasar Recency untuk segmentasi pelanggan
if "applied_recency_weeks" not in st.session_state:
    st.session_state.applied_recency_weeks = 4

with st.form("recency_parameter_form"):
    selected_recency_weeks = st.selectbox(
        "Pilih batas dasar Recency",
        options=[1, 2, 3, 4, 6],
        index=3,
        format_func=lambda weeks: f"{weeks} minggu",
        help="Pilihan ini menentukan batas waktu Recency untuk pemberian skor pelanggan."
    )

    apply_recency = st.form_submit_button(
        "Terapkan Pengaturan Recency",
        type="primary"
    )

if apply_recency:
    st.session_state.applied_recency_weeks = selected_recency_weeks

recency_base_days = st.session_state.applied_recency_weeks * 7

st.markdown(
    """
**Apa itu Recency?**

Recency adalah jarak waktu sejak pelanggan terakhir kali melakukan transaksi.
Semakin baru transaksi terakhir pelanggan, semakin kecil nilai Recency-nya.
"""
)

st.caption(
    "Semakin kecil nilai Recency, semakin tinggi skor yang diperoleh. "
    "Pelanggan yang lebih baru bertransaksi mendapatkan skor lebih baik."
)

# Mengambil pesanan delivered sesuai periode yang dipilih pengguna
rfm_orders = delivered_orders[
    (delivered_orders['order_purchase_timestamp'] >= period_start) &
    (delivered_orders['order_purchase_timestamp'] < period_end_exclusive)
][['order_id', 'customer_id', 'order_purchase_timestamp']].copy()

# Menghubungkan pesanan dengan identitas pelanggan
rfm_data = rfm_orders.merge(
    customers_df[['customer_id', 'customer_unique_id']],
    on='customer_id',
    how='inner'
)

# Menggabungkan dengan item transaksi
rfm_data = rfm_data.merge(
    order_items_df[['order_id', 'price']],
    on='order_id',
    how='inner'
)

# Tanggal acuan analisis
# Tanggal acuan adalah satu hari setelah tanggal akhir periode terpilih
reference_date = period_end_exclusive

# Menghitung Recency, Frequency, dan Monetary
rfm_df = (
    rfm_data.groupby('customer_unique_id')
    .agg(
        last_purchase=('order_purchase_timestamp', 'max'),
        frequency=('order_id', 'nunique'),
        monetary=('price', 'sum')
    )
    .reset_index()
)

rfm_df['recency'] = (
    reference_date - rfm_df['last_purchase']
).dt.days

# ==========================================
# MEMBERIKAN SKOR RFM
# ==========================================

# Skor Recency berdasarkan pilihan batas dasar dalam satuan minggu
rfm_df['R_score'] = np.select(
    [
        rfm_df['recency'] <= recency_base_days,
        rfm_df['recency'] <= recency_base_days * 2,
        rfm_df['recency'] <= recency_base_days * 3,
        rfm_df['recency'] <= recency_base_days * 6
    ],
    [5, 4, 3, 2],
    default=1
)

# Skor Frequency
rfm_df['F_score'] = np.select(
    [
        rfm_df['frequency'] == 1,
        rfm_df['frequency'] == 2,
        rfm_df['frequency'].between(3, 4),
        rfm_df['frequency'].between(5, 6)
    ],
    [1, 2, 3, 4],
    default=5
)

# Skor Monetary berdasarkan persentil
rfm_df['M_score'] = np.select(
    [
        rfm_df['monetary'] <= 39.9,
        rfm_df['monetary'] <= 69.9,
        rfm_df['monetary'] <= 109.9,
        rfm_df['monetary'] <= 179.9
    ],
    [1, 2, 3, 4],
    default=5
)

# Menggabungkan skor RFM menjadi tiga digit
rfm_df['RFM_score'] = (
    rfm_df['R_score'].astype(str) +
    rfm_df['F_score'].astype(str) +
    rfm_df['M_score'].astype(str)
)

# ==========================================
# MEMBENTUK SEGMEN PELANGGAN
# ==========================================

conditions = [
    (rfm_df['F_score'] >= 2) & (rfm_df['R_score'] >= 2),

    (rfm_df['R_score'] == 1) & (rfm_df['M_score'] >= 4),

    (rfm_df['R_score'] == 1) & (rfm_df['M_score'] <= 3),

    (rfm_df['F_score'] == 1) &
    (rfm_df['R_score'] >= 2) &
    (rfm_df['M_score'] >= 4),

    (rfm_df['F_score'] == 1) &
    (rfm_df['R_score'] >= 4) &
    (rfm_df['M_score'] <= 3),

    (rfm_df['F_score'] == 1) &
    (rfm_df['R_score'].isin([2, 3])) &
    (rfm_df['M_score'] <= 3)
]

segments = [
    'Pembelian Ulang',
    'Tidak Aktif - Bernilai Tinggi',
    'Tidak Aktif',
    'Bernilai Tinggi',
    'Potensial',
    'Perlu Perhatian'
]

rfm_df['customer_segment'] = np.select(
    conditions,
    segments,
    default='Lainnya'
)

# ==========================================
# RINGKASAN SEGMENTASI
# ==========================================

segment_summary = (
    rfm_df.groupby('customer_segment')
    .agg(
        total_customers=('customer_unique_id', 'count'),
        avg_recency=('recency', 'mean'),
        avg_frequency=('frequency', 'mean'),
        avg_monetary=('monetary', 'mean')
    )
    .reset_index()
    .sort_values('total_customers', ascending=False)
)

# KPI pelanggan
col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Total Pelanggan",
        f"{len(rfm_df):,}"
    )

with col2:
    inactive_customers = rfm_df[
        rfm_df['customer_segment'].isin([
            'Tidak Aktif',
            'Tidak Aktif - Bernilai Tinggi'
        ])
    ]

    inactive_percentage = (
        len(inactive_customers) / len(rfm_df) * 100
    )

    st.metric(
        "Pelanggan dalam Segmen Tidak Aktif",
        f"{inactive_percentage:.2f}%"
    )


# Grafik jumlah pelanggan per segmen
fig, ax = plt.subplots(figsize=(10.5, 4.5))

segment_plot = segment_summary.sort_values(
    'total_customers',
    ascending=True
).copy()

# Menghitung persentase pelanggan
segment_plot['percentage'] = (
    segment_plot['total_customers'] /
    segment_plot['total_customers'].sum() * 100
)

# Highlight segmen dengan jumlah pelanggan tertinggi pada periode terpilih
highest_segment = segment_plot.loc[
    segment_plot['total_customers'].idxmax(),
    'customer_segment'
]

colors = [
    '#F4A261' if segment == highest_segment else '#A9B9C9'
    for segment in segment_plot['customer_segment']
]

bars = ax.barh(
    segment_plot['customer_segment'],
    segment_plot['total_customers'],
    color=colors
)

# Label jumlah pelanggan dan persentase
labels = [
    f"{count:,.0f} ({percentage:.2f}%)"
    for count, percentage in zip(
        segment_plot['total_customers'],
        segment_plot['percentage']
    )
]

ax.bar_label(
    bars,
    labels=labels,
    padding=5,
    fontsize=9
)

ax.set_title(
    f"Distribusi Pelanggan Berdasarkan Segmen RFM "
    f"({selected_start_date.strftime('%d %b %y')} - "
    f"{selected_end_date.strftime('%d %b %y')})"
)
ax.set_xlabel("Jumlah Pelanggan")
ax.set_ylabel("Segmen Pelanggan")
ax.grid(axis='x', linestyle='--', alpha=0.5)
ax.set_axisbelow(True)

# Ruang untuk label di ujung batang
ax.set_xlim(
    0,
    segment_plot['total_customers'].max() * 1.16
)

plt.tight_layout()
st.pyplot(fig, width="content")
st.markdown("#### Explanatory Analysis")

if rfm_df.empty or segment_summary.empty:
    st.info(
        "Tidak terdapat data pelanggan yang dapat disegmentasikan "
        "pada periode dan pengaturan Recency yang dipilih."
    )
else:
    total_rfm_customers = len(rfm_df)
    segment_summary['percentage'] = (
        segment_summary['total_customers'] / total_rfm_customers * 100
    )

    # Susun karakteristik seluruh segmen berdasarkan hasil perhitungan aktual.
    segment_descriptions = []
    for _, segment_row in segment_summary.iterrows():
        segment_descriptions.append(
            f"- **{segment_row['customer_segment']}**: "
            f"{int(segment_row['total_customers']):,} pelanggan "
            f"({segment_row['percentage']:.2f}%), dengan rata-rata "
            f"Recency {segment_row['avg_recency']:.0f} hari, "
            f"Frequency {segment_row['avg_frequency']:.2f} kali, "
            f"dan Monetary R$ {segment_row['avg_monetary']:,.2f}."
        )

    largest_segment = segment_summary.iloc[0]
    smallest_segment = segment_summary.sort_values(
        'total_customers', ascending=True
    ).iloc[0]

    inactive_names = ['Tidak Aktif', 'Tidak Aktif - Bernilai Tinggi']
    inactive_count = rfm_df[
        rfm_df['customer_segment'].isin(inactive_names)
    ].shape[0]
    inactive_share = inactive_count / total_rfm_customers * 100

    repeated_customers = int((rfm_df['frequency'] > 1).sum())
    repeated_share = repeated_customers / total_rfm_customers * 100

    st.markdown(
        f"""
Berdasarkan hasil segmentasi RFM pada periode
**{selected_start_date.strftime('%d %b %y')} hingga
{selected_end_date.strftime('%d %b %y')}**, terdapat
**{total_rfm_customers:,} pelanggan** yang terbagi ke dalam
{len(segment_summary)} kelompok.

**Karakteristik Masing-Masing Segmen**

{chr(10).join(segment_descriptions)}

**Temuan Utama**

- Segmen dengan jumlah pelanggan terbanyak adalah
  **{largest_segment['customer_segment']}**, sebanyak
  **{int(largest_segment['total_customers']):,} pelanggan**
  ({largest_segment['percentage']:.2f}%).
- Segmen dengan jumlah pelanggan paling sedikit adalah
  **{smallest_segment['customer_segment']}**, sebanyak
  **{int(smallest_segment['total_customers']):,} pelanggan**
  ({smallest_segment['percentage']:.2f}%).
- Jika kedua kelompok Tidak Aktif digabungkan, jumlahnya mencapai
  **{inactive_count:,} pelanggan** atau **{inactive_share:.2f}%**
  dari seluruh pelanggan.
- Pelanggan yang melakukan transaksi lebih dari satu kali berjumlah
  **{repeated_customers:,} orang** ({repeated_share:.2f}%).

Temuan tersebut menggambarkan komposisi pelanggan berdasarkan perilaku
transaksi pada periode yang dipilih. Perubahan periode maupun batas
Recency dapat mengubah distribusi setiap segmen.
"""
    )
plt.close(fig)



# ==========================================
# 6. PROPORSI PELANGGAN BERDASARKAN FREKUENSI
# ==========================================

st.subheader("Proporsi Pelanggan Berdasarkan Frekuensi Transaksi")

# Menghitung jumlah pelanggan berdasarkan frekuensi transaksi
frequency_distribution = pd.Series({
    '1 Kali Transaksi': (
        rfm_df['frequency'] == 1
    ).sum(),
    'Lebih dari 1 Kali': (
        rfm_df['frequency'] > 1
    ).sum()
})

# Membuat grafik pie
fig, ax = plt.subplots(figsize=(6, 3.5))

colors = ['#F4A261', '#A9B9C9']

wedges, texts, autotexts = ax.pie(
    frequency_distribution.values,
    labels=frequency_distribution.index,
    autopct='%1.2f%%',
    startangle=90,
    colors=colors,
    wedgeprops={'edgecolor': 'white', 'linewidth': 2},
    textprops={'fontsize': 10}
)

ax.set_title(
    f"Proporsi Pelanggan Berdasarkan Frekuensi Transaksi "
    f"({selected_start_date.strftime('%d %b %y')} - "
    f"{selected_end_date.strftime('%d %b %y')})",
    fontweight='bold'
)

plt.tight_layout()
st.pyplot(fig, width="content")
st.markdown("#### Explanatory Analysis")

if not rfm_df.empty:
    one_time_customers = int((rfm_df['frequency'] == 1).sum())
    repeat_customers = int((rfm_df['frequency'] > 1).sum())
    one_time_pct = one_time_customers / len(rfm_df) * 100
    repeat_pct = repeat_customers / len(rfm_df) * 100

    dominant_frequency_group = (
        "pelanggan yang hanya melakukan satu kali transaksi"
        if one_time_customers >= repeat_customers
        else "pelanggan yang melakukan transaksi lebih dari satu kali"
    )

    st.markdown(
        f"""
**Analisis Frekuensi Transaksi Pelanggan**

Pada periode **{selected_start_date.strftime('%d %b %y')} hingga
{selected_end_date.strftime('%d %b %y')}**:

- **{one_time_customers:,} pelanggan ({one_time_pct:.2f}%)**
  melakukan satu kali transaksi.
- **{repeat_customers:,} pelanggan ({repeat_pct:.2f}%)**
  melakukan transaksi lebih dari satu kali.

Kelompok yang paling dominan adalah {dominant_frequency_group}.
Informasi ini memberikan gambaran mengenai proporsi pelanggan yang
melakukan pembelian berulang pada periode analisis.
"""
    )
else:
    st.info("Belum ada data frekuensi transaksi untuk periode yang dipilih.")
plt.close(fig)

