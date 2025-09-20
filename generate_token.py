import os
import sys
from urllib.parse import urlparse, parse_qs
import requests
from dotenv import load_dotenv

# Add project root to path to allow imports from other files
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import spotify
except ImportError:
    print("Hata: `spotify.py` dosyası bulunamadı. Script'in ana proje dizininde olduğundan emin olun.")
    sys.exit(1)

def main():
    """
    A command-line tool to generate a Spotify refresh token.
    """
    load_dotenv()

    # Check if necessary environment variables are set
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

    if not client_id or not redirect_uri:
        print("Hata: Lütfen .env dosyanızda SPOTIFY_CLIENT_ID ve SPOTIFY_REDIRECT_URI değişkenlerini ayarlayın.")
        return

    # 1. Get authorization URL
    auth_url = spotify.get_auth_url()

    print("-" * 60)
    print("Spotify Refresh Token Oluşturucu")
    print("-" * 60)
    print("\n1. Adım: Aşağıdaki URL'yi kopyalayıp tarayıcınızda açın:")
    print("\n" + auth_url + "\n")
    print("2. Adım: Spotify'a giriş yapın ve uygulamaya izin verin.")
    print("3. Adım: İzin verdikten sonra tarayıcınız 'sayfa bulunamadı' gibi bir hata verebilir, bu normaldir.")
    print("   Tarayıcının adres çubuğundaki URL'nin tamamını kopyalayın.")

    # 2. Get the redirected URL from user
    callback_url = input("\n4. Adım: Kopyaladığınız URL'yi buraya yapıştırın ve Enter'a basın:\n> ")

    # 3. Parse the authorization code from the URL
    try:
        parsed_url = urlparse(callback_url)
        query_params = parse_qs(parsed_url.query)
        auth_code = query_params.get("code", [None])[0]

        if not auth_code:
            print("\nHata: URL içinde 'code' parametresi bulunamadı. Lütfen doğru URL'yi kopyaladığınızdan emin olun.")
            return

    except Exception:
        print("\nHata: Geçersiz bir URL girdiniz.")
        return

    # 4. Exchange the code for tokens
    print("\nYetkilendirme kodu alınıyor, token'lar için Spotify'a istek gönderiliyor...")
    try:
        token_data = spotify.get_token_data_from_code(auth_code)
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        if not refresh_token:
            print("\nHata: Spotify'dan refresh_token alınamadı. Yetkilerde bir sorun olabilir.")
            print("Gelen yanıt:", token_data)
            return

        print("\n" + "=" * 60)
        print("BAŞARILI!")
        print("Aşağıdaki Refresh Token'ı kopyalayıp .env dosyanızdaki")
        print("MY_SPOTIFY_REFRESH_TOKEN değişkenine yapıştırın.")
        print("-" * 60)
        print(f"\nRefresh Token: {refresh_token}\n")
        print("=" * 60)

    except requests.exceptions.HTTPError as e:
        print(f"\nHata: Spotify'dan token alınırken bir sorun oluştu (HTTP {e.response.status_code}).")
        print("Spotify'ın yanıtı:", e.response.json())
        print("\nLütfen .env dosyanızdaki SPOTIFY_CLIENT_ID ve SPOTIFY_CLIENT_SECRET'ın doğru olduğundan emin olun.")
        print("Ayrıca Spotify Developer Dashboard'daki Redirect URI'nin .env dosyanızdaki ile aynı olduğunu kontrol edin.")

if __name__ == "__main__":
    main()
