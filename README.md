# Spotify Track Sharer & Now Playing Widget

Bu proje, kullanıcıların Spotify'da dinledikleri şarkıları arkadaşlarıyla paylaşmalarına olanak tanıyan bir web uygulaması ve kişisel "Şu Anda Çalınıyor" widget'ı sunan bir API'dir. FastAPI ile oluşturulmuş ve Vercel'de dağıtılmak üzere tasarlanmıştır.

## ✨ Özellikler

-   **Çok Kullanıcılı Paylaşım:** Kullanıcılar Spotify hesaplarıyla giriş yapabilir ve o an dinledikleri şarkıyı genel bir "feed" üzerinde paylaşabilirler.
-   **Kişisel "Şu Anda Çalınıyor" Widget'ı:** `/api/now-playing` endpoint'i, kendi web sitenize veya profilinize ekleyebileceğiniz, o an dinlediğiniz şarkıyı gösteren bir veri çıkışı sağlar.
-   **Otomatik Güncelleme:** Arka planda çalışan bir görev (cron job) ile aktif kullanıcıların dinlediği şarkılar periyodik olarak güncellenir.
-   **Kolay Kurulum:** Vercel ve bir bulut veritabanı (örn: Vercel Postgres) ile kolayca dağıtılabilir.

## 🛠️ Kullanılan Teknolojiler

-   **Backend:** [FastAPI](https://fastapi.tiangolo.com/)
-   **Veritabanı:** [SQLAlchemy](https://www.sqlalchemy.org/) ORM ile PostgreSQL (üretim) ve SQLite (yerel geliştirme)
-   **Dağıtım (Deployment):** [Vercel](https://vercel.com/)
-   **Spotify Entegrasyonu:** [Spotify Web API](https://developer.spotify.com/documentation/web-api)

---

## 🚀 Kurulum ve Dağıtım Rehberi

Bu projeyi kendi Vercel hesabınızda çalıştırmak için aşağıdaki adımları izleyin.

### Adım 1: Projeyi Fork'layın ve Klonlayın

1.  Bu GitHub reposunu kendi hesabınıza **fork'layın**.
2.  Fork'ladığınız repoyu kendi bilgisayarınıza klonlayın:
    ```bash
    git clone https://github.com/KULLANICI_ADINIZ/PROJE_ADI.git
    cd PROJE_ADI
    ```

### Adım 2: Spotify Developer Uygulaması Oluşturun

1.  [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)'a gidin ve giriş yapın.
2.  **"Create App"** butonuna tıklayarak yeni bir uygulama oluşturun.
3.  Uygulamanızı oluşturduktan sonra, **"Client ID"** ve **"Client Secret"** değerlerini bir yere not alın. "Show client secret" diyerek gizli anahtarı görebilirsiniz.
4.  **"Edit Settings"** butonuna tıklayın.
5.  **"Redirect URIs"** bölümüne, Vercel uygulamanızın URL'sini ve ardından `/auth/callback` yolunu ekleyin. Örneğin:
    -   `https://projeniz.vercel.app/auth/callback`
    -   Yerel geliştirme için: `http://127.0.0.1:8000/auth/callback`
6.  Ayarları kaydedin.

### Adım 3: Veritabanı ve Vercel Projesi Oluşturun

1.  **Vercel'e Giriş Yapın:** [Vercel](https://vercel.com/) hesabınıza giriş yapın.
2.  **Yeni Proje Oluşturun:** "Add New... -> Project" seçeneğiyle devam edin ve GitHub'da fork'ladığınız repoyu seçin.
3.  **Veritabanı Oluşturun:** Proje sayfasında "Storage" sekmesine gidin ve "Postgres" seçeneğiyle yeni bir veritabanı oluşturun. Veritabanı oluşturulduktan sonra size bir **`DATABASE_URL`** (bağlantı adresi) verilecektir. Bu adresi kopyalayın.

### Adım 4: Ortam Değişkenlerini Ayarlayın (Environment Variables)

Vercel projenizin ayarlarında ("Settings" -> "Environment Variables"), aşağıdaki değişkenleri tek tek oluşturun ve değerlerini girin:

| Değişken Adı               | Açıklama                                                                                                                              | Örnek Değer                               |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| `SPOTIFY_CLIENT_ID`        | Spotify Developer Dashboard'dan aldığınız Client ID.                                                                                  | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`        |
| `SPOTIFY_CLIENT_SECRET`    | Spotify Developer Dashboard'dan aldığınız Client Secret.                                                                              | `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`        |
| `SPOTIFY_REDIRECT_URI`     | Spotify ayarlarınıza eklediğiniz URI.                                                                                                 | `https://projeniz.vercel.app/auth/callback` |
| `DATABASE_URL`             | Vercel'den veya başka bir sağlayıcıdan aldığınız PostgreSQL bağlantı adresi.                                                           | `postgres://...`                          |
| `MY_SPOTIFY_REFRESH_TOKEN` | Kişisel "Now Playing" widget'ı için kullanılacak olan sizin Spotify refresh token'ınız. (Bir sonraki adımda alınacak).                 | `AQ...`                                   |
| `CRON_SECRET`              | Zamanlanmış görevi tetiklemek için kullanılacak gizli bir anahtar. Karmaşık ve tahmin edilemez bir değer girin.                        | `guvenli-ve-tahmin-edilemez-bir-anahtar`  |

### Adım 5: Kişisel Refresh Token'ınızı Oluşturun

Kişisel "Now Playing" widget'ının (`/api/now-playing`) çalışması için kendi Spotify hesabınızın `refresh_token`'ını almanız gerekir.

1.  Proje dosyalarını bilgisayarınıza klonladığınızdan ve `requirements.txt`'deki paketleri yüklediğinizden emin olun:
    ```bash
    pip install -r requirements.txt
    ```
2.  Proje ana dizininde bir `.env` dosyası oluşturun ve yukarıdaki değişkenleri (özellikle `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI`) yerel geliştirme için doldurun.
3.  Terminalde aşağıdaki komutu çalıştırın:
    ```bash
    python generate_token.py
    ```
4.  Script'in size verdiği adımları izleyin. Tarayıcıda açılan linke gidip izin verdikten sonra, yönlendirildiğiniz sayfanın URL'sini terminale yapıştırın.
5.  Script size bir `Refresh Token` verecektir. Bu token'ı kopyalayın ve Vercel'deki `MY_SPOTIFY_REFRESH_TOKEN` ortam değişkeninin değeri olarak yapıştırın.

### Adım 6: Projeyi Dağıtın (Deploy)

Vercel, GitHub reponuzun `main` dalındaki her değişikliği otomatik olarak dağıtacaktır. Ortam değişkenlerini ayarladıktan sonra Vercel panelinden yeni bir "deployment" tetikleyebilirsiniz.

---

## 💻 Kullanım

-   **Giriş Yapma:** `https://projeniz.vercel.app/auth/login` adresine giderek kendi Spotify hesabınızla giriş yapabilirsiniz.
-   **Paylaşımı Başlatma/Durdurma:** Bu özellik için API endpoint'leri (`/share/start`, `/share/stop`) mevcuttur. Bir arayüz oluşturarak bu endpoint'leri kullanabilirsiniz.
-   **Feed'i Görüntüleme:** `https://projeniz.vercel.app/feed` adresinden o an şarkılarını paylaşan tüm kullanıcıların listesini JSON formatında alabilirsiniz.
-   **Kişisel Widget:** `https://projeniz.vercel.app/api/now-playing` adresinden kendi dinlediğiniz şarkının verisini alabilirsiniz.

## 🕒 Zamanlanmış Görev (Cron Job) Kurulumu

Kullanıcıların dinlediği şarkıların düzenli olarak güncellenmesi için `/tasks/update-playing` endpoint'inin periyodik olarak çağrılması gerekir.

Bunu Vercel'in kendi "Cron Jobs" özelliğiyle yapabilirsiniz:
1.  Vercel projenizin ana dizinine bir `vercel.json` dosyası ekleyin (zaten bu repoda mevcut).
2.  `crons` bölümüne aşağıdaki gibi bir tanım ekleyin:
    ```json
    {
      "crons": [
        {
          "path": "/tasks/update-playing",
          "schedule": "*/2 * * * *"
        }
      ]
    }
    ```
    Bu örnek, görevi her 2 dakikada bir çalıştırır. `schedule` değerini istediğiniz gibi değiştirebilirsiniz. Unutmayın, bu endpoint'i çağırırken `x-cron-secret` başlığını doğru değerle göndermeniz gerekir. Vercel Cron Job ayarlarından özel başlık ekleyebilirsiniz.
