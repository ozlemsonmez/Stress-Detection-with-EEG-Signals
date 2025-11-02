import socket
import json
from datetime import datetime
from firebase_admin import credentials, firestore, initialize_app
import math

from google.cloud.firestore import FieldFilter

# Firebase yapılandırması
cred = credentials.Certificate("firebase-adminsdk.json")
initialize_app(cred)
db = firestore.client()

def get_sonuclar():
    try:
        # sonuclar koleksiyonundan tüm dökümanları al
        sonuclar_ref = db.collection('sonuclar')
        docs = sonuclar_ref.stream()
        
        # userId'ye göre sonuçları grupla
        user_sonuclar = {}
        for doc in docs:
            veri = doc.to_dict()
            user_id = veri.get('userId')
            
            if user_id:
                # Eğer bu kullanıcı için daha önce sonuç kaydedilmemişse veya
                # yeni sonuç daha yeniyse, güncelle
                if user_id not in user_sonuclar or \
                   veri.get('timestamp', 0) > user_sonuclar[user_id].get('timestamp', 0):
                    veri['id'] = doc.id
                    user_sonuclar[user_id] = veri
        
        # Sadece unique sonuçları listeye dönüştür
        sonuclar_listesi = list(user_sonuclar.values())
        
        # Users koleksiyonundan kullanıcı bilgilerini al
        users_ref = db.collection('users')
        users_docs = users_ref.stream()
        users_dict = {doc.id: doc.to_dict() for doc in users_docs}
        
        # Sonuçları kullanıcı bilgileriyle eşleştir
        sonuclar_with_users = []
        for sonuc in sonuclar_listesi:
            user_id = sonuc.get('userId')
            if user_id in users_dict:
                user_info = users_dict[user_id]
                sonuclar_with_users.append({
                    'isim': user_info.get('display_name', 'İsimsiz'),
                    'STAISinif': sonuc.get('STAISinif', 'STAI Belirtilmemiş'),
                    'STAISonuc': sonuc.get('STAISonuc', 'STAI Belirtilmemiş'),
                    'genelEEGSonuc': sonuc.get('genelEEGSonuc', 'EEG Belirtilmemiş'),
                    'genelEEGSinif': sonuc.get('genelEEGSinif', 'EEG Belirtilmemiş'),
                    'oneriEEGSonuc': sonuc.get('oneriEEGSonuc', 'EEG Belirtilmemiş'),
                    'oneriEEGSinif': sonuc.get('oneriEEGSinif', 'EEG Belirtilmemiş'),
                })
        
        return sonuclar_with_users
    
    except Exception as e:
        print(f"Veri çekme hatası: {e}")
        return None

def gruplari_analiz_et(sonuclar):
    # Grupları oluştur
    ayni_grup = {
        'düşük': [],
        'orta': [],
        'yüksek': []
    }
    farkli_grup = []
    
    for sonuc in sonuclar:
        stai_sinif = sonuc['STAISinif'].lower()
        eeg_sinif = sonuc['genelEEGSinif'].lower()
        
        # Eğer sınıflar aynıysa
        if stai_sinif == eeg_sinif and stai_sinif in ['düşük', 'orta', 'yüksek']:
            ayni_grup[stai_sinif].append(sonuc)
        # Eğer sınıflar farklıysa
        elif stai_sinif in ['düşük', 'orta', 'yüksek'] and eeg_sinif in ['düşük', 'orta', 'yüksek']:
            farkli_grup.append(sonuc)
    
    return ayni_grup, farkli_grup

def eeg_degisim_analizi(sonuclar):
    # EEG değişim gruplarını oluştur
    degisim_gruplari = {
        'düşme': [],
        'aynı': [],
        'yükselme': []
    }
    
    for sonuc in sonuclar:
        genel_eeg = sonuc.get('genelEEGSonuc', 0)
        oneri_eeg = sonuc.get('oneriEEGSonuc', 0)
        
        try:
            genel_eeg = float(genel_eeg)
            oneri_eeg = float(oneri_eeg)
            
            # Değişim yüzdesini hesapla
            if genel_eeg != 0:
                degisim_yuzdesi = ((oneri_eeg - genel_eeg) / genel_eeg) * 100
                
                # Değişim durumuna göre grupla
                if degisim_yuzdesi < 0:  # %5'ten fazla düşüş
                    degisim_gruplari['düşme'].append(sonuc)
                elif degisim_yuzdesi > 0:  # %5'ten fazla yükseliş
                    degisim_gruplari['yükselme'].append(sonuc)
                else:  # %5'ten az değişim
                    degisim_gruplari['aynı'].append(sonuc)
        except (ValueError, TypeError):
            continue
    
    return degisim_gruplari

# Test için örnek kullanım
if __name__ == "__main__":
    sonuclar = get_sonuclar()
    if sonuclar:
        '''
        # STAI ve EEG analizi
        ayni_grup, farkli_grup = gruplari_analiz_et(sonuclar)
        
        print("\n=== AYNI GRUP SONUÇLARI ===\n")
        for seviye in ['düşük', 'orta', 'yüksek']:
            if ayni_grup[seviye]:
                print(f"\n{seviye.upper()} SEVİYE (STAI ve EEG aynı):")
                print("-" * 50)
                for sonuc in ayni_grup[seviye]:
                    print(f"İsim: {sonuc['isim']}")
                    print(f"STAI Sınıf: {sonuc['STAISinif']}")
                    print(f"STAI Sonuç: {sonuc['STAISonuc']}")
                    print(f"Genel EEG Sonuç: {sonuc['genelEEGSonuc']}")
                    print(f"Genel EEG Sınıf: {sonuc['genelEEGSinif']}")
                    print("-" * 30)
        
        print("\n=== FARKLI GRUP SONUÇLARI ===\n")
        if farkli_grup:
            for sonuc in farkli_grup:
                print(f"İsim: {sonuc['isim']}")
                print(f"STAI Sınıf: {sonuc['STAISinif']}")
                print(f"STAI Sonuç: {sonuc['STAISonuc']}")
                print(f"Genel EEG Sonuç: {sonuc['genelEEGSonuc']}")
                print(f"Genel EEG Sınıf: {sonuc['genelEEGSinif']}")
                print("-" * 30)
        
        print("\n=== STAI ve EEG ÖZET ===\n")
        print(f"Toplam Kişi Sayısı: {len(sonuclar)}")
        print(f"Aynı Grup Sayısı: {sum(len(grup) for grup in ayni_grup.values())}")
        print(f"Farklı Grup Sayısı: {len(farkli_grup)}")
        print("\nAynı Grup Dağılımı:")
        for seviye in ['düşük', 'orta', 'yüksek']:
            print(f"{seviye.upper()}: {len(ayni_grup[seviye])} kişi")
        
        '''
        # EEG değişim analizi
        degisim_gruplari = eeg_degisim_analizi(sonuclar)
        
        print("\n=== EEG DEĞİŞİM ANALİZİ ===\n")
        for durum in ['düşme', 'aynı', 'yükselme']:
            if degisim_gruplari[durum]:
                print(f"\n{durum.upper()} DURUMU:")
                print("-" * 50)
                for sonuc in degisim_gruplari[durum]:
                    print(f"İsim: {sonuc['isim']}")
                    print(f"Genel EEG Sonuç: {sonuc['genelEEGSonuc']}")
                    print(f"Öneri EEG Sonuç: {sonuc['oneriEEGSonuc']}")
                    print(f"Değişim: {((float(sonuc['oneriEEGSonuc']) - float(sonuc['genelEEGSonuc'])) / float(sonuc['genelEEGSonuc']) * 100):.2f}%")
                    print("-" * 30)
        
        print("\n=== EEG DEĞİŞİM ÖZET ===\n")
        print(f"Toplam Kişi Sayısı: {len(sonuclar)}")
        print(f"Düşme Gösteren: {len(degisim_gruplari['düşme'])} kişi")
        print(f"Aynı Kalan: {len(degisim_gruplari['aynı'])} kişi")
        print(f"Yükselme Gösteren: {len(degisim_gruplari['yükselme'])} kişi")
        

