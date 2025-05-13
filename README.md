# Motorcycle Expert System

A Flask-based API for diagnosing motorcycle damage using a forward-chaining expert system.

## Penjelasan Program

Motorcycle Expert System adalah aplikasi berbasis Flask yang dirancang untuk mendiagnosis kerusakan sepeda motor secara otomatis menggunakan pendekatan *forward chaining* dalam sistem pakar. Program ini memungkinkan pengguna, seperti teknisi atau admin, untuk memasukkan gejala kerusakan melalui antarmuka API dan mendapatkan diagnosis berupa jenis kerusakan, penyebab, dan solusi. Berikut adalah alur kerja program dari awal hingga akhir:

1. **Inisialisasi Aplikasi**: Program dimulai dengan menjalankan `main.py`, yang memanggil fungsi `create_app()` di `app/__init__.py`. Fungsi ini menginisialisasi aplikasi Flask, mengatur konfigurasi seperti koneksi ke database MySQL (melalui `SQLAlchemy`), CORS untuk akses lintas domain, dan memuat pengaturan dari `config.py` (misalnya, `SECRET_KEY` dan `DATABASE_URL` dari file `.env`).

2. **Pengisian Database**: Endpoint `/api/seed` digunakan untuk mengisi database dengan data awal, termasuk daftar sepeda motor (`motorcycles`), gejala (`symptoms`), kerusakan (`damages`), aturan (`rules` dan `rule_symptoms`), penyebab (`causes`), solusi (`solutions`), dan pengguna (`users`). Data ini membentuk *knowledge base* sistem, yang menjadi dasar inferensi.

3. **Autentikasi Pengguna**: Pengguna mengakses sistem melalui endpoint `/api/login`, yang memverifikasi kredensial (username dan password) dan menghasilkan token JWT (JSON Web Token) untuk autentikasi. Token ini diperlukan untuk mengakses endpoint terproteksi seperti `/api/consultations` atau endpoint admin seperti `/api/motorcycles` (POST).

4. **Diagnosis Kerusakan**: Inti dari sistem adalah endpoint `/api/diagnose`, yang menerima input berupa daftar ID gejala (`symptom_ids`) dan ID sepeda motor (`motorcycle_id`). Input ini diproses oleh kelas `ForwardChainingEngine` di `expert_system.py`. Sistem menggunakan *forward chaining* untuk mencocokkan gejala dengan aturan yang tersimpan di *knowledge base*. Jika aturan terpenuhi, sistem menyimpulkan kerusakan, mengambil penyebab dan solusi terkait, lalu menyimpan hasilnya di tabel `consultations` dan `consultation_symptoms`. Hasil diagnosis dikembalikan sebagai respons JSON berisi `consultation_id` dan detail diagnosis.

5. **Riwayat Konsultasi**: Endpoint `/api/consultations` memungkinkan pengguna terautentikasi untuk melihat riwayat diagnosis. Admin dapat melihat semua konsultasi, sedangkan pengguna biasa hanya melihat konsultasi mereka sendiri, berdasarkan `user_id` yang terkait dengan token JWT.

6. **Manajemen Data**: Endpoint seperti `/api/symptoms`, `/api/damages`, dan `/api/rules` memungkinkan admin untuk menambah atau mengelola data di *knowledge base*, seperti menambahkan gejala baru atau aturan inferensi.

Program ini menggunakan pendekatan *forward chaining*, di mana sistem memulai dari fakta (gejala yang dimasukkan) dan menerapkan aturan untuk mencapai kesimpulan (kerusakan). Proses ini meniru cara seorang teknisi mendiagnosis kerusakan dengan mencocokkan gejala yang diamati dengan pengetahuan di buku panduan. Sistem dirancang modular dengan file seperti `routes.py` untuk endpoint API, `models.py` untuk skema database, dan `expert_system.py` untuk logika inferensi, memastikan kode yang terorganisir dan mudah dipelihara.

## Knowledge Base

*Knowledge base* adalah inti dari sistem pakar ini, menyimpan pengetahuan domain tentang gejala, kerusakan, aturan, penyebab, dan solusi sepeda motor dalam database MySQL. Berikut adalah komponen *knowledge base* yang digunakan oleh `ForwardChainingEngine` untuk inferensi:

### 1. Gejala (Symptoms)
Tabel ini berisi daftar gejala yang dapat diamati pada sepeda motor, sebagai fakta awal untuk proses *forward chaining*.

| ID  | Kode | Nama                            | Deskripsi |
|-----|------|---------------------------------|-----------|
| 1   | G1   | Motor Tidak Mau Bergerak        |           |
| 2   | G2   | Mesin Menyala                   |           |
| 3   | G3   | Timbul Bunyi Berdecit           |           |
| 4   | G4   | Lebar Drive Belt Kurang Dari Atau Sama Dengan 18,9mm | |
| 8   | G8   | Tenaga Motor Kurang             |           |
| 10  | G10  | Permukaan Pully Berminyak       |           |
| ... | ...  | ...                             |           |

**Catatan**: Tabel ini berisi 29 gejala (G1 hingga G29) seperti yang diisi oleh endpoint `/api/seed`. Hanya sebagian ditampilkan untuk contoh.

### 2. Kerusakan (Damages)
Tabel ini berisi daftar kerusakan yang mungkin, sebagai kesimpulan dari proses inferensi.

| ID  | Kode | Nama                            | Deskripsi |
|-----|------|---------------------------------|-----------|
| 1   | K1   | Drive Belt Aus                  |           |
| 4   | K4   | Drive Belt Putus                |           |
| 5   | K5   | Drive Belt Terkontaminasi Minyak |           |
| ... | ...  | ...                             |           |

**Catatan**: Tabel ini berisi 15 kerusakan (K1 hingga K15) seperti yang diisi oleh `/api/seed`. Hanya sebagian ditampilkan.

### 3. Aturan (Rules dan Rule Symptoms)
Tabel ini mendefinisikan aturan inferensi yang menghubungkan gejala dengan kerusakan, sebagai logika *forward chaining*.

#### Tabel Rules
| ID  | Damage ID |
|-----|-----------|
| 1   | 1         |
| 2   | 4         |
| 3   | 5         |

#### Tabel Rule Symptoms
| Rule ID | Symptom ID |
|---------|------------|
| 1       | 4          |
| 2       | 1          |
| 2       | 2          |
| 2       | 7          |
| 3       | 8          |
| 3       | 10         |

**Catatan**: Aturan diartikan sebagai:  
- Aturan 1: Jika G4, maka K1 (Drive Belt Aus).  
- Aturan 2: Jika G1, G2, dan G7, maka K4 (Drive Belt Putus).  
- Aturan 3: Jika G8 dan G10, maka K5 (Drive Belt Terkontaminasi Minyak).

### 4. Penyebab (Causes)
Tabel ini berisi penyebab dari setiap kerusakan, memberikan konteks tambahan untuk diagnosis.

| ID  | Damage ID | Deskripsi                                      |
|-----|-----------|-----------------------------------------------|
| 1   | 1         | Umur pakai drive belt sudah terlalu lama.     |
| 2   | 4         | Drive belt sudah aus parah sehingga menjadi putus. |
| 3   | 5         | Kebocoran oli transmisi atau kebocoran oli dari bagian mesin. |

### 5. Solusi (Solutions)
Tabel ini berisi solusi untuk setiap kerusakan, sebagai rekomendasi perbaikan.

| ID  | Damage ID | Deskripsi                                      |
|-----|-----------|-----------------------------------------------|
| 1   | 1         | Ganti drive belt dengan yang baru sesuai spesifikasi pabrikan. |
| 2   | 4         | Ganti drive belt yang putus dengan yang baru. |
| 3   | 5         | Bersihkan permukaan pully dari minyak dan ganti drive belt dengan yang baru. |

**Ringkasan Knowledge Base**: *Knowledge base* ini digunakan oleh `ForwardChainingEngine` untuk mendiagnosis kerusakan. Gejala dari pengguna (misalnya, G8 dan G10) dicocokkan dengan aturan (misalnya, Aturan 3) untuk menyimpulkan kerusakan (K5). Penyebab dan solusi terkait diambil untuk melengkapi diagnosis. Data ini diisi melalui endpoint `/api/seed` dan dapat diperbarui melalui endpoint seperti `/api/rules`, `/api/symptoms`, atau `/api/damages`.

## Setup

1. **Install Python 3.8+** dan MySQL.
2. **Clone the repository**:
   ```bash
   git clone https://github.com/akhmadzaqiriyadi/Motorcycle-Expert-System.git
   cd motorcycle_expert_system