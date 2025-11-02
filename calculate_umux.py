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

def convert_umux_scores(raw_scores):
    """UMUX-Lite puanlarını hesaplar"""
    # UMUX-Lite formülü: ((Soru1/7)+(Soru2/7))/2*100
    q1 = raw_scores[0] / 7.0
    q2 = raw_scores[1] / 7.0
    umux_score = ((q1 + q2) / 2) * 100
    
    return umux_score

def get_umux_sonuclari():
    try:
        # anketler koleksiyonundan UMUX anketlerini al
        anketler_ref = db.collection('anketler')
        docs = anketler_ref.stream()
        
        # Kullanıcı ID'sine göre sonuçları grupla
        user_sonuclar = {}
        for doc in docs:
            veri = doc.to_dict()
            user_id = veri.get('userId')
            umux_list = veri.get('UMUXLiteList', [])
            
            try:
                sonuc = {
                    'id': doc.id,
                    'userId': user_id,
                    'timestamp': veri.get('timestamp', 0)
                }
                
                # UMUX hesaplaması
                if umux_list:
                    raw_scores = [float(score) for score in umux_list]
                    umux_score = convert_umux_scores(raw_scores)
                    
                    sonuc.update({
                        'UMUXLiteList': umux_list,
                        'umux_score': umux_score
                    })
                
                # Eğer bu kullanıcı için daha önce sonuç kaydedilmemişse veya
                # yeni sonuç daha yeniyse, güncelle
                if user_id not in user_sonuclar or \
                   sonuc['timestamp'] > user_sonuclar[user_id]['timestamp']:
                    user_sonuclar[user_id] = sonuc
                    
            except (ValueError, TypeError) as e:
                print(f"Hesaplama hatası (ID: {doc.id}): {e}")
                continue
        
        # Sadece unique sonuçları listeye dönüştür
        return list(user_sonuclar.values())
    
    except Exception as e:
        print(f"Veri çekme hatası: {e}")
        return None

# Test için örnek kullanım
if __name__ == "__main__":
    sonuclar = get_umux_sonuclari()
    if sonuclar:
        print("\n=== UMUX SONUÇLARI ===\n")
        for sonuc in sonuclar:
            if 'UMUXLiteList' in sonuc:
                print(f"Kullanıcı ID: {sonuc['userId']}")
                print(f"Ham Yanıtlar: {sonuc['UMUXLiteList']}")
                print(f"UMUX Skoru: {sonuc['umux_score']:.2f}")
                print("-" * 50)
        
        print("\n=== ÖZET ===\n")
        print(f"Toplam Anket Sayısı: {len(sonuclar)}")
        
        # Sorulara göre ortalama hesapla
        soru1_toplam = 0
        soru2_toplam = 0
        umux_sayisi = 0
        toplam_umux = 0
        
        for sonuc in sonuclar:
            if 'UMUXLiteList' in sonuc and len(sonuc['UMUXLiteList']) >= 2:
                soru1_toplam += float(sonuc['UMUXLiteList'][0])
                soru2_toplam += float(sonuc['UMUXLiteList'][1])
                umux_sayisi += 1
                
                if 'umux_score' in sonuc:
                    toplam_umux += sonuc['umux_score']
        
        if umux_sayisi > 0:
            print(f"Soru 1 Ortalama: {soru1_toplam / umux_sayisi:.2f}/7")
            print(f"Soru 2 Ortalama: {soru2_toplam / umux_sayisi:.2f}/7")
            ortalama_umux = toplam_umux / umux_sayisi
            print(f"\nOrtalama UMUX-Lite Skoru: {ortalama_umux:.2f}/100") 