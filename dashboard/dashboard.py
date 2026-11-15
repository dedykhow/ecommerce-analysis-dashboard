
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



# ==========================================
# 3. ANALISIS TREN PENJUALAN
# ==========================================

st.divider()

st.header("Pertanyaan 1: Tren Penjualan")

st.subheader("Bagaimana Perkembangan Tren Penjualan Bulanan?")

st.markdown("""
Visualisasi ini menampilkan perkembangan nilai penjualan bulanan selama Januari 2017 hingga Agustus 2018. Nilai penjualan dihitung berdasarkan total harga produk (`price`) dari pesanan berstatus delivered, tanpa memasukkan biaya pengiriman.
""")

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

# Menggabungkan data pesanan dengan item transaksi
sales_df = delivered_orders[
    ['order_id', 'order_purchase_timestamp']
].merge(
    order_items_df[['order_id', 'price']],
    on='order_id',
    how='inner'
)

# Filter periode Januari 2017 - Agustus 2018
sales_df = sales_df[
    sales_df['order_purchase_timestamp'].between(
        '2017-01-01',
        '2018-08-31 23:59:59'
    )
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
    "Tren Penjualan Bulanan (Januari 2017 - Agustus 2018)"
)
ax.set_xlabel("Bulan")
ax.set_ylabel("Total Penjualan (Juta R$)")
ax.tick_params(axis='x', rotation=45)
ax.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()
st.pyplot(fig, width="content")

st.markdown("#### Explanatory Analysis")

st.markdown("""
Berdasarkan grafik, nilai penjualan menunjukkan kecenderungan meningkat selama periode Januari 2017 hingga Agustus 2018, meskipun terdapat beberapa fluktuasi bulanan.

- Penjualan terendah terjadi pada Januari 2017 sebesar R$ 111.798,36.
- Penjualan tertinggi terjadi pada November 2017 sebesar R$ 987.648,07.
- Setelah mencapai puncak pada November 2017, penjualan mengalami penurunan pada Desember 2017, kemudian kembali meningkat pada awal 2018.
- Pada periode Maret hingga Mei 2018, penjualan relatif stabil di kisaran R$950 ribu hingga R$ 980 ribu per bulan.

Secara keseluruhan, nilai penjualan pada Agustus 2018 mencapai R$838.576,64 atau sekitar 7,5 kali dibandingkan Januari 2017. Hal ini menunjukkan perkembangan nilai penjualan yang positif selama periode analisis.
""")

plt.close(fig)



# ==========================================
# 4. ANALISIS KATEGORI PRODUK
# ==========================================

st.divider()

st.header("Pertanyaan 2: Kategori Produk")

st.subheader("Kategori Produk Apa yang Memberikan Kontribusi Nilai Penjualan Terbesar?")

st.markdown("""
Visualisasi ini menampilkan 10 kategori produk dengan nilai penjualan tertinggi selama Januari 2017 hingga Agustus 2018. Nilai penjualan dihitung berdasarkan total harga produk (`price`), tanpa memasukkan biaya pengiriman.
""")

# Mengambil pesanan dalam periode analisis
orders_category = delivered_orders[
    delivered_orders['order_purchase_timestamp'].between(
        '2017-01-01',
        '2018-08-31 23:59:59'
    )
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

# Warna khusus untuk kategori tertinggi
colors = [
    '#F4A261' if category == 'health_beauty' else '#A9B9C9'
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
    "10 Kategori Produk dengan Nilai Penjualan Tertinggi"
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

st.markdown("""
Berdasarkan grafik, kategori `health_beauty` memberikan kontribusi nilai penjualan terbesar selama periode Januari 2017 hingga Agustus 2018.

- Kategori `health_beauty` menempati posisi pertama dengan nilai penjualan sebesar R$ 1.229.557,50 atau sekitar 9,46% dari total penjualan kategori yang memiliki informasi kategori.
- Posisi kedua ditempati `watches_gifts` dengan nilai penjualan R$ 1.163.187,91 atau sekitar 8,94%.
- Posisi ketiga ditempati `bed_bath_table` dengan nilai penjualan R$ 1.022.955,77 atau sekitar 7,87%.
- Menariknya, `bed_bath_table` memiliki jumlah item terjual terbanyak di antara 10 kategori teratas, yaitu 10.945 item, tetapi nilai penjualannya berada di posisi ketiga.

Temuan ini menunjukkan bahwa kategori dengan jumlah item terjual terbanyak belum tentu menghasilkan nilai penjualan terbesar. Kontribusi nilai penjualan juga dipengaruhi oleh harga produk yang terjual.

Perhitungan persentase menggunakan total penjualan dari item transaksi yang memiliki informasi kategori produk dalam bahasa Inggris. Sebanyak 1.557 item transaksi tidak disertakan dalam perhitungan kategori karena informasi kategori dalam bahasa Inggris tidak tersedia.
""")
plt.close(fig)



# ==========================================
# 5. SEGMENTASI PELANGGAN RFM
# ==========================================

st.divider()

st.header("Pertanyaan 3: Segmentasi Pelanggan")

st.subheader("Bagaimana Karakteristik Pelanggan Berdasarkan Recency, Frequency, dan Monetary?")

st.markdown("""
Visualisasi ini menampilkan distribusi pelanggan berdasarkan hasil segmentasi RFM selama periode Januari 2017 hingga Agustus 2018. Segmentasi dilakukan menggunakan nilai Recency, Frequency, dan Monetary dari transaksi berstatus delivered.
""")

# Mengambil pesanan delivered pada periode analisis
rfm_orders = delivered_orders[
    delivered_orders['order_purchase_timestamp'].between(
        '2017-01-01',
        '2018-08-31 23:59:59'
    )
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
reference_date = pd.Timestamp('2018-08-30')

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

# Skor Recency
rfm_df['R_score'] = np.select(
    [
        rfm_df['recency'] <= 30,
        rfm_df['recency'] <= 60,
        rfm_df['recency'] <= 90,
        rfm_df['recency'] <= 180
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

# Highlight segmen Tidak Aktif
colors = [
    '#F4A261' if segment == 'Tidak Aktif' else '#A9B9C9'
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

ax.set_title("Distribusi Pelanggan Berdasarkan Segmen RFM")
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

st.markdown("""
Berdasarkan hasil segmentasi RFM terhadap 93.096 pelanggan, diperoleh enam kelompok pelanggan dengan karakteristik perilaku transaksi yang berbeda.

**Karakteristik Masing-Masing Segmen**

1. **Tidak Aktif (36,06%)**

   Merupakan kelompok pelanggan terbesar dengan 33.570 pelanggan. Rata-rata Recency mencapai 338 hari, Frequency sekitar 1,01 kali, dan Monetary sebesar R$ 56,08. Hal ini menunjukkan bahwa pelanggan dalam kelompok ini sudah cukup lama tidak melakukan transaksi, dengan frekuensi dan nilai pembelian yang relatif rendah.

2. **Tidak Aktif - Bernilai Tinggi (22,89%)**

   Terdiri dari 21.306 pelanggan dengan rata-rata Recency 335 hari, Frequency 1,06 kali, dan Monetary R$ 271,32. Meskipun sudah lama tidak melakukan transaksi, kelompok ini memiliki nilai pembelian rata-rata yang tinggi. Total nilai pembelian historisnya mencapai R$ 5.780.808,16.

3. **Perlu Perhatian (15,92%)**

   Terdiri dari 14.822 pelanggan dengan rata-rata Recency 122 hari, Frequency 1 kali, dan Monetary R$ 55,99. Kelompok ini belum melakukan pembelian berulang dan memiliki jarak waktu transaksi terakhir yang cukup panjang dibandingkan kelompok pelanggan yang lebih baru bertransaksi.

4. **Bernilai Tinggi (15,85%)**

   Terdiri dari 14.757 pelanggan dengan rata-rata Recency 93 hari, Frequency 1 kali, dan Monetary R$ 267,44. Kelompok ini memiliki nilai pembelian rata-rata yang tinggi, tetapi belum menunjukkan perilaku pembelian berulang.

5. **Potensial (7,96%)**

   Terdiri dari 7.408 pelanggan dengan rata-rata Recency sekitar 29 hari, Frequency 1 kali, dan Monetary R$ 55,10. Kelompok ini relatif baru melakukan transaksi, tetapi belum menunjukkan pembelian berulang.

6. **Pembelian Ulang (1,32%)**

   Merupakan kelompok pelanggan terkecil dengan 1.233 pelanggan. Rata-rata Recency sekitar 91 hari, Frequency 2,15 kali, dan Monetary R$ 268,89. Kelompok ini menunjukkan perilaku pembelian berulang dengan nilai pembelian rata-rata yang relatif tinggi.

**Temuan Utama**

Dari hasil segmentasi tersebut, terdapat beberapa temuan penting:

- Segmen Tidak Aktif merupakan kelompok terbesar, mencakup 36,06% dari seluruh pelanggan.
- Jika digabungkan dengan segmen Tidak Aktif - Bernilai Tinggi, kedua kelompok pelanggan tidak aktif mencakup sekitar 58,95% dari total pelanggan.
- Segmen Tidak Aktif - Bernilai Tinggi memiliki total nilai pembelian historis terbesar di antara seluruh segmen, yaitu R$5.780.808,16.
- Segmen Pembelian Ulang hanya mencakup 1,32% pelanggan, menunjukkan bahwa proporsi pelanggan yang melakukan transaksi berulang relatif kecil.

Secara keseluruhan, hasil segmentasi menunjukkan bahwa sebagian besar pelanggan belum menunjukkan perilaku pembelian berulang. Selain itu, terdapat kelompok pelanggan yang sudah lama tidak bertransaksi tetapi memiliki nilai pembelian historis tinggi.
""")
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
    "Proporsi Pelanggan Berdasarkan Frekuensi Transaksi",
    fontweight='bold'
)

plt.tight_layout()
st.pyplot(fig, width="content")
st.markdown("#### Explanatory Analysis")

st.markdown("""
**Analisis Frekuensi Transaksi Pelanggan**

Distribusi frekuensi transaksi menunjukkan bahwa mayoritas pelanggan hanya melakukan satu kali pembelian selama periode pengamatan.

- Sebanyak 90.307 pelanggan (97,00%) hanya melakukan satu kali transaksi.
- Sebanyak 2.789 pelanggan (3,00%) melakukan pembelian lebih dari satu kali.

Temuan ini menunjukkan bahwa proporsi pelanggan yang melakukan pembelian berulang masih sangat kecil dibandingkan pelanggan yang hanya melakukan satu kali transaksi.

Dengan demikian, perilaku pembelian berulang menjadi salah satu aspek penting yang perlu diperhatikan dalam analisis karakteristik pelanggan.
""")
plt.close(fig)

