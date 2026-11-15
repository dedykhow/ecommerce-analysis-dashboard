# E-Commerce Public Dataset Analysis

## Deskripsi Proyek

Proyek ini merupakan analisis data E-Commerce Public Dataset untuk memahami perkembangan penjualan, kontribusi kategori produk, dan karakteristik pelanggan berdasarkan perilaku transaksi.

Analisis dilakukan menggunakan Python dan disajikan melalui dashboard interaktif menggunakan Streamlit.

## Fitur Dashboard

Dashboard menyajikan empat visualisasi utama:

1. **Tren Penjualan Bulanan**  
   Menampilkan perkembangan nilai penjualan dari Januari 2017 hingga Agustus 2018.

2. **Kontribusi Penjualan Berdasarkan Kategori Produk**  
   Menampilkan 10 kategori produk dengan nilai penjualan tertinggi.

3. **Segmentasi Pelanggan (RFM)**  
   Mengelompokkan pelanggan berdasarkan Recency, Frequency, dan Monetary.

4. **Proporsi Pelanggan Berdasarkan Frekuensi Transaksi**  
   Menampilkan perbandingan pelanggan dengan satu kali transaksi dan pelanggan dengan transaksi lebih dari satu kali.

## Struktur Direktori

```text
Submission_ECommerce/
├── dashboard/
│   └── dashboard.py
├── data/
│   └── ecommerce_data/
├── Proyek_Analisis_ECommerce.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Persyaratan

- Python
- Streamlit
- Pandas
- NumPy
- Matplotlib
- Seaborn

## Cara Menjalankan Dashboard Secara Lokal

1. Clone atau unduh repository proyek.
2. Buka folder proyek melalui terminal.
3. Buat virtual environment:

```bash
python -m venv .venv
```

4. Aktifkan virtual environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

5. Instal library:

```bash
pip install -r requirements.txt
```

6. Jalankan dashboard:

```bash
streamlit run dashboard/dashboard.py
```

7. Buka alamat lokal yang ditampilkan pada terminal, biasanya:

```text
http://localhost:8501
```

## Sumber Data

Dataset yang digunakan adalah E-Commerce Public Dataset yang disediakan dalam pembelajaran Dicoding, kelas Belajar Fundamental Analisis Data.