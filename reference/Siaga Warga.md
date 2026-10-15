Product Requirement Document - PRD

Mata Kuliah : Analisis & Perancangan Sistem Informasi

Nama Proyek : Siaga Warga

: 1.0

Versi

:10/11/2026

Tanggal

1. Pendahuluan

1.1 Latar Belakang

Seiring dengan meningkatnya partisipasi warga dalam mewujudkan lingkungan yang

aman dan tertata, pemerintah telah menyediakan berbagai kanal pengaduan publik. Warga kini

dapat dengan mudah melaporkan berbagai isu infrastruktur dan lingkungan, mulai dari jalan

berlubang, lampu jalan mati, tumpukan sampah, saluran air tersumbat, hingga kondisi darurat

seperti pohon tumbang.

Namun, kanal pengaduan konvensional yang ada saat ini umumnya hanya berfungsi

sebagai agregator informasi tanpa kemampuan analisis urgensi. Sistem yang ada cenderung

mengurutkan laporan secara kronologis atau sekadar berdasarkan volume keluhan terbanyak.

Hal ini menciptakan celah operasional yang berbahaya: ketika ratusan laporan masuk secara

bersamaan, petugas kesulitan menentukan masalah mana yang harus dieksekusi terlebih dahulu.

Sebagai contoh, tumpukan sampah di pasar mungkin menghasilkan 15 laporan warga,

sementara pohon tumbang yang memblokir jalan utama hanya menghasilkan 3 laporan. Jika

sistem hanya bertumpu pada kuantitas keluhan, petugas akan diarahkan untuk mengurus

sampah terlebih dahulu, padahal pohon tumbang memiliki risiko keselamatan dan dampak

kemacetan yang jauh lebih kritis.

Oleh karena itu, dibutuhkan sebuah inovasi yang memberikan nilai tambah (added value)

dibandingkan sekadar aplikasi pelaporan biasa. SiagaWarga hadir sebagai platform Intelligent

Citizen Reporting & Response Prioritization. Sistem ini tidak hanya menerima laporan, tetapi

secara cerdas melakukan triase (pemilahan) otomatis dengan menghitung Priority Score pada

setiap laporan. Dengan pendekatan ini, SiagaWarga mengubah tumpukan data pengaduan


menjadi peta prioritas tindakan yang terstruktur, memastikan petugas lapangan selalu

menangani masalah yang paling mendesak terlebih dahulu.

## 1.2 Tujuan Proyek

Target utama pengembangan Suara Kampus adalah:

- a. Membangun dan meluncurkan purwarupa (prototipe) atau Minimum Viable Product (MVP) platform SiagaWarga, yang terdiri dari dua antarmuka: aplikasi pelaporan yang ramah pengguna untuk warga, dan dasbor manajemen (Command Center) yang interaktif untuk petugas.

- b. Mengembangkan dan melakukan uji coba algoritma Priority Score (0-100) untuk memastikan sistem mampu memproses 5 parameter (tingkat bahaya, lokasi, dampak, jumlah pelapor, waktu tunggu) secara otomatis dan akurat ke dalam kategori P1, P2, dan P3.

- c. Mengimplementasikan sistem ini dalam skala terbatas (misalnya: simulasi pada satu kelurahan atau kecamatan percontohan) untuk memvalidasi fungsionalitas aplikasi dan mendapatkan umpan balik (feedback) langsung dari petugas lapangan.

- d. Menghasilkan data komparatif yang membuktikan bahwa SiagaWarga mampu memangkas waktu penentuan keputusan (triase) petugas secara signifikan dibandingkan kanal pengaduan konvensional, sehingga menjadi jawaban konkret atas pertanyaan juri terkait pembeda inovasi ini.

## 1.3 Ruang Lingkup (Scope)

Batasan Aplikasi (In-Scope):

- a. Registrasi dan login warga menggunakan email atau nomor HP, serta autentikasi petugas dan admin berdasarkan hak akses.

- b. Pembuatan laporan dengan foto, kategori, deskripsi, dan lokasi kejadian seperti jalan rusak, sampah menumpuk, atau lampu jalan mati.

- c. Klasifikasi laporan dan penentuan tingkat keparahan untuk membantu proses penilaian prioritas.


- d. Perhitungan skor prioritas berdasarkan parameter yang ditetapkan, seperti tingkat keparahan, dampak lokasi, jumlah warga terdampak, dan waktu tunggu.

- e. Menampilkan daftar laporan, skor prioritas, kategori, status, serta pengurutan laporan berdasarkan urgensi.

- f. Petugas dapat memperbarui status laporan, sedangkan warga dapat memantau perkembangan laporan yang dikirim.

- g. Ringkasan jumlah laporan berdasarkan kategori, status, dan tingkat prioritas untuk membantu pemantauan.

Batasan Aplikasi (Out-of-Scope):

- a. Integrasi langsung dengan database kependudukan, sistem pengaduan pemerintah, atau layanan instansi eksternal

- b. Pengembangan aplikasi Android atau IOS

- c. Fitur chat warga dengan petugas serta integrasi notifikasi melalui WhatsApp atau SMS.

- d. Pemantauan pergerakan petugas secara langsung selama proses penanganan laporan.

- e. Penggunaan sensor fisik untuk mendeteksi kerusakan jalan, banjir, atau kondisi lingkungan secara otomatis.

- f. Validasi NIK secara langsung melalui database Dukcapil atau layanan identitas pemerintah.

- g. Penugasan petugas, pengerahan tim lapangan, dan penyelesaian masalah secara otomatis tanpa keputusan pihak berwenang.

## 2. Target Pengguna (User Persona)

- a. Warga (Citizen)

- 1) Pengguna yang melaporkan permasalahan umum di lingkungan sekitar.

- 2) Registrasi dan login.

- 3) Membuat laporan disertai foto, lokasi, kategori, dan deskripsi.

- 4) Memantau status laporan.

- 5) Melihat riwayat laporan pribadi.

- b. Petugas (Officer)

- 1) Pengguna yang memantau, memprioritaskan, dan mengelola laporan warga.


- 2) Melihat seluruh laporan sesuai kewenangannya.

- 3) Memantau skor dan antrean prioritas.

- 4) Memperbarui status laporan.

- 5) Melihat statistik laporan.

## 3. Kebutuhan Sistem (System Requirements)

## 3.1 Kebutuhan Fungsional (Functional Requirements)

| Kode | Kebutuhan Fungsional | Deskripsi |
| --- | --- | --- |
|   | KF-01 Registrasi akun | Sistem menyediakan fitur registrasi bagi warga menggunakan nama, email atau nomor telepon, dan kata sandi tanpa mewajibkan NIK. |
|   | KF-02 Login dan logout | Sistem memungkinkan warga dan petugas masuk serta keluar dari akun sesuai hak akses masing-masing. |
|   | KF-03 Membuat laporan | Sistem memungkinkan warga membuat laporan permasalahan lingkungan, seperti jalan rusak, sampah menumpuk, lampu jalan mati, dan saluran air tersumbat. |
|   | KF-04 Mengunggah foto | Sistem memungkinkan warga melampirkan foto sebagai bukti permasalahan yang dilaporkan. |
|   |   | KF-05 Menentukan lokasi laporan Sistem memungkinkan warga menentukan lokasi permasalahan melalui GPS atau memilih titik pada peta. |
|   | KF-06 Mengisi detail laporan | Sistem menyediakan fitur pemilihan kategori dan pengisian deskripsi permasalahan. |


|   | KF-07 Melihat laporan | Sistem memungkinkan warga melihat laporan yang telah dibuat dan melihat laporan di sekitar tanpa menampilkan informasi pribadi pelapor. |
| --- | --- | --- |
|   |   | KF-08 Memantau status laporan Sistem memungkinkan warga memantau perkembangan laporan dari tahap verifikasi hingga penyelesaian. |
|   | KF-09 Mengelola laporan | Sistem memungkinkan petugas melihat dan memeriksa seluruh laporan yang masuk. |
|   | KF-10 Memverifikasi laporan | Sistem memungkinkan petugas memvalidasi laporan sebelum ditindaklanjuti. |
|   | KF-11 Klasifikasi laporan berbantuan AI | Sistem membantu mengidentifikasi kategori dan indikasi tingkat keparahan permasalahan berdasarkan data laporan atau foto. |
|   |   | KF-12 Menghitung skor prioritas Sistem menghitung skor prioritas laporan berdasarkan tingkat bahaya, dampak lokasi, jumlah warga terdampak, frekuensi laporan serupa, dan waktu tunggu. |
|   | KF-13 Menampilkan urutan prioritas | Sistem menampilkan laporan berdasarkan skor prioritas agar petugas dapat menentukan laporan yang perlu ditangani terlebih dahulu. |
|   |   | KF-14 Menampilkan peta laporan Sistem menampilkan persebaran lokasi laporan pada peta dengan penanda berdasarkan tingkat prioritas. |
|   | KF-15 Memperbarui status laporan | Sistem memungkinkan petugas memperbarui status laporan menjadi diverifikasi, ditugaskan, dalam penanganan, atau selesai. |


|   | KF-16 Mencatat penanganan laporan | Sistem memungkinkan petugas menambahkan catatan tindak lanjut dan hasil penyelesaian laporan. |
| --- | --- | --- |
|   | KF-17 Mendeteksi laporan serupa | Sistem membantu mengidentifikasi laporan dengan kategori, lokasi, dan waktu yang berdekatan untuk mengurangi duplikasi laporan. |
|   |   | KF-18 Mencatat riwayat laporan Sistem menyimpan riwayat perubahan status, waktu perubahan, dan catatan penanganan untuk setiap laporan. |

*Tabel 3. 1 Kebutuhan Fungsional*

## 3.2 Kebutuhan Non-Fungsional (Non-Functional Requirements)

| Kode | Aspek | Kebutuhan Nonfungsional |
| --- | --- | --- |
| KNF-01 Usability |   | Antarmuka harus mudah dipahami sehingga warga dapat membuat laporan tanpa memerlukan panduan teknis yang rumit. |
| KNF-02 | Performance | Halaman utama, dashboard, dan daftar laporan ditargetkan dapat dimuat dalam waktu maksimal 3 detik pada kondisi jaringan dan beban pengujian yang ditentukan. |
| KNF-03 | Security | Sistem harus melindungi akun pengguna menggunakan autentikasi dan penyimpanan kata sandi yang aman, serta menerapkan pembatasan akses berdasarkan role. |
| KNF-04 Privacy |   | Sistem hanya mengumpulkan data pribadi yang diperlukan dan tidak mewajibkan NIK untuk |


|   |   | registrasi. Identitas pelapor tidak ditampilkan kepada pengguna umum. |
| --- | --- | --- |
| KNF-05 Reliability |   | Sistem harus menyimpan laporan dan perubahan status secara konsisten serta memberikan pesan jika proses penyimpanan gagal. |
| KNF-06 | Availability | Sistem ditargetkan memiliki ketersediaan layanan minimal 99% selama periode pengujian atau operasional yang disepakati, di luar pemeliharaan terjadwal. |
|   | KNF-07 Compatibility | Sistem harus dapat digunakan melalui browser modern pada perangkat desktop maupun ponsel. |
| KNF-08 | Responsive design | Tampilan sistem harus menyesuaikan ukuran layar agar formulir laporan dan dashboard tetap dapat digunakan pada perangkat berbeda. |
|   | KNF-09 Maintainability | Kode program harus terstruktur agar kategori laporan, bobot prioritas, dan alur status dapat diperbarui tanpa mengubah keseluruhan sistem. |
| KNF-10 | Accuracy | Perhitungan priority score harus konsisten dengan formula yang ditetapkan dan dapat dijelaskan kepada petugas. Hasil AI harus diperlakukan sebagai rekomendasi, bukan keputusan final yang selalu benar. |
| KNF-11 | Data integrity | Setiap laporan harus memiliki identitas unik dan keterkaitan yang benar dengan pelapor, lokasi, serta riwayat penanganannya. |


| KNF-12 | Auditability | Perubahan status dan catatan penanganan harus memiliki waktu pencatatan dan identitas petugas agar proses penanganan dapat ditelusuri. |
| --- | --- | --- |

*Tabel 3. 2 Kebutuhan Non-Fungsional*

## 4. Pemodelan Sistem (System Modeling)

## 4.1 Pendekatan Berorientasi Objek (UML)

## 1. Use Case Diagram:

*Gambar 4. 1 Use Case Diagram*


## 2. Activity Diagram:


## 3. Class Diagram:

*Gambar 4. 2 Class Diagram*


## 4. Sequence Diagram:


*Gambar 4. 3 Sequence Diagram*


## 5. Arsitektur Informasi & User Flow

## 5.1 Sitemap / Information Architecture

Gambar 5. 1 Sitemap


## 5.2 User Flow
