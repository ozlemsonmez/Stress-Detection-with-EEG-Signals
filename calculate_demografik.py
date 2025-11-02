# Demografik Bilgiler Okuma Scripti
# anketler tablosundan demografikList listesini alır ve data = [...] formatında çıktı üretir (her kullanıcıdan sadece en güncel kayıt)

from firebase_admin import credentials, firestore, initialize_app

# Firebase yapılandırması
cred = credentials.Certificate("firebase-adminsdk.json")
initialize_app(cred)
db = firestore.client()

def get_demografik_bilgiler_data_format():
    try:
        anketler_ref = db.collection('anketler')
        docs = anketler_ref.stream()
        user_latest = {}
        for doc in docs:
            veri = doc.to_dict()
            user_id = veri.get('userId', '-')
            demografikList = veri.get('demografikList', [])
            timestamp = veri.get('timestamp', 0)
            if demografikList:
                if user_id not in user_latest or timestamp > user_latest[user_id]['timestamp']:
                    user_latest[user_id] = {'demografikList': demografikList, 'timestamp': timestamp}
        data = []
        for kayit in user_latest.values():
            d = kayit['demografikList']
            # Sıralama: Cinsiyet, Yaş, Bölüm, Eğitim Düzeyi, EEG Kullandı, Son 24 saatte ilaç
            data.append({
                "Cinsiyet": d[0] if len(d) > 0 else "",
                "Yaş": d[1] if len(d) > 1 else "",
                "Bölüm": d[2] if len(d) > 2 else "",
                "Eğitim Düzeyi": d[3] if len(d) > 3 else "",
                "EEG Kullandı": d[6] if len(d) > 6 else "",
                "Son 24 saatte ilaç": d[9] if len(d) > 9 else ""
            })
        print("data = [")
        for item in data:
            print(f"    {item},")
        print("]")
        print(f"\nToplam kullanıcı sayısı: {len(data)}")
    except Exception as e:
        print(f"Veri çekme hatası: {e}")

if __name__ == "__main__":
    get_demografik_bilgiler_data_format() 