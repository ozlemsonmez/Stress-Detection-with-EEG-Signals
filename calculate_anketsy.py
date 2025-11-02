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

def convert_attrakdiff_scores(raw_scores):
    """1-7 arası değerleri -3 ile +3 arasına çevirir ve ters puanlama yapar"""
    # Ters puanlama yapılacak sorular (0-tabanlı indeks)
    ters_puanlama_sorulari = [1, 2, 5, 7, 8, 11, 14, 20, 27]  # 2,3,6,8,9,12,15,21,28. sorular (1-tabanlı indeks)
    
    converted_scores = []
    for i, score in enumerate(raw_scores):
        # Ters puanlama için: 8 - orijinal puan
        if i in ters_puanlama_sorulari:
            score = 8 - score
        converted_scores.append(score - 4)
    
    return converted_scores

def get_anket_sonuclari():
    try:
        # anketler koleksiyonundan tüm dökümanları al
        anketler_ref = db.collection('anketler')
        docs = anketler_ref.stream()
        
        # Kullanıcı ID'sine göre sonuçları grupla
        user_sonuclar = {}
        for doc in docs:
            veri = doc.to_dict()
            user_id = veri.get('userId')
            attrakdiff_list = veri.get('AttrakDiffList', [])
            
            try:
                sonuc = {
                    'id': doc.id,
                    'userId': user_id,
                    'timestamp': veri.get('timestamp', 0)
                }
                
                # AttrakDiff hesaplaması
                if attrakdiff_list:
                    raw_scores = [float(score) for score in attrakdiff_list]
                    converted_scores = convert_attrakdiff_scores(raw_scores)
                    sonuc.update({
                        'AttrakDiffList': attrakdiff_list,
                        'converted_scores': converted_scores,
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
    sonuclar = get_anket_sonuclari()
    if sonuclar:
        print("\n=== ATRAKDIFF SONUÇLARI ===\n")
        for sonuc in sonuclar:
            if 'AttrakDiffList' in sonuc:
                print(f"Kullanıcı ID: {sonuc['userId']}")
                print(f"Ham Yanıtlar: {sonuc['AttrakDiffList']}")
                print(f"Dönüştürülmüş Yanıtlar: {sonuc['converted_scores']}")
                print(f"Ortalama Skor: {sum(sonuc['converted_scores']) / len(sonuc['converted_scores'])}")
                print("-" * 50)
        
        print("\n=== ÖZET ===\n")
        print(f"Toplam Anket Sayısı: {len(sonuclar)}")
        
        # Ortalama skorları hesapla
        ortalama_skorlar = {}
        for sonuc in sonuclar:
            if 'converted_scores' in sonuc:
                for i, skor in enumerate(sonuc['converted_scores']):
                    if i not in ortalama_skorlar:
                        ortalama_skorlar[i] = []
                    ortalama_skorlar[i].append(skor)
        
        for i, skorlar in ortalama_skorlar.items():
            ortalama = sum(skorlar) / len(skorlar)
            print(f"{i+1}. Soru: {ortalama:.2f}")

        attrakdiff_skoru = sum(sum(skorlar) for skorlar in ortalama_skorlar.values())
        print(f"\nToplam AttrakDiff Skoru: {attrakdiff_skoru / 28 / len(sonuclar):.2f}")

