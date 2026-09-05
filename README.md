# DataScience Copilot 🤖📊

> 🌍 **DataScience Copilot — an intelligent assistant that automates EDA, model recommendation and hyperparameter optimization, built with LangChain + Streamlit.**
>
> _(Details in Turkish below.)_

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.1+-green.svg)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Akıllı veri bilimi asistanı - Otomatik EDA, model önerisi ve hiperparametre optimizasyonu**

[Özellikler](#-özellikler) • [Kurulum](#-kurulum) • [Kullanım](#-kullanım) • [Mimari](#-mimari) • [Katkı](#-katkı)

</div>

## 🎯 Genel Bakış

**DataScience Copilot**, veri analizi süreçlerini otomatikleştiren akıllı bir asistan sistemidir. Kullanıcıların veri yükleyip, otomatik analizler gerçekleştirebileceği, model önerileri alabileceği ve detaylı raporlar oluşturabileceği kapsamlı bir platform sunar.

### 🤖 Temel Yetenekler
- **Akıllı Veri Analizi**: Otomatik EDA ve istatistiksel analiz
- **Model Öneri Sistemi**: Problem tipine göre optimize model seçimi
- **Hiperparametre Optimizasyonu**: Otomatik tuning ve optimizasyon
- **Görselleştirme**: Interactive chart'lar ve dashboard'lar

## ✨ Özellikler

### 📊 Veri Analizi
- [x] **Otomatik EDA** - Eksik veri analizi, korelasyon matrisi, dağılım grafikleri
- [x] **Veri Temizleme** - Akıllı ön işleme ve feature engineering
- [x] **İstatistiksel Analiz** - Deskriptif istatistikler, anormallik tespiti
- [x] **Data Profiling** - Otomatik veri profili oluşturma

### 🤖 Makine Öğrenmesi
- [x] **Akıllı Model Önerisi** - Problem tipine göre otomatik model seçimi
- [x] **AutoML** - Otomatik hiperparametre optimizasyonu
- [x] **Model Değerlendirme** - Kapsamlı metrikler ve cross-validation
- [x] **Model Yorumlama** - SHAP, feature importance analizi

### 🎨 Görselleştirme & Raporlama
- [x] **Interactive Dashboard** - Gerçek zamanlı veri görselleştirme
- [x] **Otomatik Raporlar** - PDF ve HTML formatında detaylı raporlar
- [x] **Custom Charts** - Çeşitli grafik türleri ve özelleştirme

### 🔧 Teknik Özellikler
- [x] **Multi-format Support** - CSV, Excel, JSON, SQL veri girişi
- [x] **Real-time Processing** - Canlı veri işleme ve analiz
- [x] **Memory Management** - Oturum bazlı hafıza yönetimi
- [x] **API Entegrasyonu** - RESTful API endpoints

## 🚀 Hızlı Başlangıç

### Ön Koşullar
- Python 3.8 veya üzeri
- Google Gemini API anahtarı
- 4GB+ RAM

### Kurulum

1. **Repository'yi klonlayın**:
```bash
git clone https://github.com/username/data-science-copilot.git
cd data-science-copilot
```

2. **Sanal ortam oluşturun**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

3. **Gerekli paketleri yükleyin**:
```bash
pip install -r requirements.txt
```

4. **Çevre değişkenlerini ayarlayın**:
```bash
cp .env .env
```

5. **Uygulamayı başlatın**:

```bash
streamlit run frontend/app.py
```

Veya Python ile:
```bash
python main.py
```

## Docker Compose

Tum stack artik Docker Compose ile ayaga kaldirilabilir:

```bash
docker compose up --build
```

Servisler:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

Notlar:
- Compose, `db + backend + frontend` servisini birlikte kurar.
- Backend container icinde `DATABASE_URL` otomatik olarak `db` servisine baglanir.
- Frontend, backend'e ayni-origin proxy uzerinden gider.
- Docker Desktop / Docker daemon acik olmali.
## Dosya Yapısı

data_science_copilot/
├── frontend/                 # Streamlit kullanıcı arayüzü
├── backend/                  # FastAPI backend servisleri
├── ai_engine/               # LangChain + Gemini AI motoru
│   ├── chains/              # Veri analizi chain'leri
│   ├── agents/              # Akıllı agent'lar
│   ├── tools/               # Özelleştirilmiş tool'lar
│   └── memory/              # Oturum hafıza yönetimi
├── data_processing/         # Veri işleme modülleri
│   └── sample_datasets/     # Örnek veri setleri (tips, titanic, penguins, diamonds)
├── automl_engine/           # Otomatik ML motoru
├── visualization/           # Görselleştirme motoru
├── tests/                   # Unit test'ler
└── docs/                    # Dokümantasyon

## 📚 Örnek Veri Setleri

Uygulama, hızlı test için hazır veri setleri içerir. Bu veri setleri `data_processing/sample_datasets/` klasöründe saklanır.

### Mevcut Veri Setleri

1. **tips.csv** - Restoran bahşiş verileri
2. **titanic.csv** - Titanic yolcu verileri
3. **penguins.csv** - Penguen türleri verileri
4. **diamonds.csv** - Elmas özellikleri verileri

### Veri Setlerini İndirme

Veri setlerini şu adresten indirebilirsiniz:
- GitHub Repository: https://github.com/mwaskom/seaborn-data
- Doğrudan CSV indirme: https://raw.githubusercontent.com/mwaskom/seaborn-data/master/

İndirdiğiniz CSV dosyalarını `data_processing/sample_datasets/` klasörüne koyun. Veri setleri otomatik olarak `data_upload.py` sayfasından yüklenebilir.


Proje Notları Yapılacaklar:
1. Llm önerilerine tümünü uygula butonu getirilecek böylece kullanıcı tek tek öneri uygulatmayacak
2. EDA modülü llm önerileri kısmı incelenecek tekrardan (önemli)
3. Feature Engineering e llm önerisi kısmı getir (opsiyonel)
4. Feature engineering Yeni özellik kısmı ele alınacak (önemli)
5. Llm önerilerindeki kartlar imleçle sağa sola fırlat (sağa öneri uygula sol öneri uygulanmasın) (opsiyonel)
6. Bütün modüllere düzgün debug sistemi ve log çıktıları ekle (tasarımı güzel dili sade ve basit olmalı) (önemli)
7. Tam otomatik sistem oluştur (opsiyonel)
8. On-premise sistemler 
9. Frontend gelişecek
10. MlFLow eklenecek
