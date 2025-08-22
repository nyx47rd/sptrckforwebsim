# Bu betik, veritabanı tablolarını bir kereliğine oluşturmak için kullanılır.
# Sadece telefon gibi kısıtlı ortamlarda, gerekli olan minimum paketlerle çalışması için tasarlandı.
#
# KULLANIM:
# 1. Bu dosyanın yanına .env adında bir dosya oluşturun.
# 2. .env dosyasının içine `DATABASE_URL=sizin_render_url_adresiniz` şeklinde veritabanı adresinizi yazın.
# 3. Terminalde `pip install sqlalchemy psycopg2-binary python-dotenv` komutunu çalıştırın.
# 4. `python create_tables.py` komutunu çalıştırın.

import os
import datetime
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship, declarative_base

print("Gerekli paketler yükleniyor ve ortam değişkenleri okunuyor...")
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("\n--- HATA ---")
    print("DATABASE_URL bulunamadı.")
    print("Lütfen bu betikle aynı dizinde bir .env dosyası oluşturduğunuzdan")
    print("ve içine Render'dan aldığınız veritabanı adresini yazdığınızdan emin olun.")
    print("Örnek: DATABASE_URL=postgresql://kullanici:sifre@host:port/veritabani")
    print("------------")
else:
    try:
        print("Veritabanına bağlanılıyor...")
        engine = create_engine(DATABASE_URL)
        Base = declarative_base()

        # --- Modeller ---
        # Ana uygulamadaki modellerin aynısı, buraya kopyalandı.
        # Bu, `fastapi` gibi büyük paketleri kurma zorunluluğunu ortadan kaldırır.
        class User(Base):
            __tablename__ = "users"
            id = Column(Integer, primary_key=True, index=True)
            spotify_id = Column(String, unique=True, index=True)
            display_name = Column(String)
            profile_pic_url = Column(String, nullable=True)
            token = relationship("Token", uselist=False, back_populates="user")
            active_share = relationship("ActiveShare", uselist=False, back_populates="user")

        class Token(Base):
            __tablename__ = "tokens"
            id = Column(Integer, primary_key=True, index=True)
            user_id = Column(Integer, ForeignKey("users.id"))
            access_token = Column(String)
            refresh_token = Column(String)
            expires_at = Column(DateTime)
            user = relationship("User", back_populates="token")

        class ActiveShare(Base):
            __tablename__ = "active_shares"
            id = Column(Integer, primary_key=True, index=True)
            user_id = Column(Integer, ForeignKey("users.id"), unique=True)
            expires_at = Column(DateTime)
            user = relationship("User", back_populates="active_share")

        print("Tablolar oluşturuluyor...")
        Base.metadata.create_all(bind=engine)

        print("\n--- BAŞARILI! ---")
        print("Veritabanı tabloları başarıyla oluşturuldu.")
        print("Artık Vercel'deki uygulamanız bu veritabanını kullanmaya hazır.")
        print("-----------------")

    except Exception as e:
        print(f"\n--- HATA ---")
        print(f"Bir hata oluştu: {e}")
        print("Lütfen .env dosyasındaki DATABASE_URL adresinizi ve internet bağlantınızı kontrol edin.")
        print("------------")
