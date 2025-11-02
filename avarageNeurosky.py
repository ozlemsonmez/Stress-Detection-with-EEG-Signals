import socket
import json
from datetime import datetime
from firebase_admin import credentials, firestore, initialize_app
import math

from google.cloud.firestore import FieldFilter

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"

# Firebase Firestore ayarları
cred = credentials.Certificate(r"C:/Users/melek/Desktop/ap/firebase-adminsdk.json")
initialize_app(cred)
db = firestore.client()

stress_levels = []
data_count = 0

# Sigmoid fonksiyonu tanımla
def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def tersine_puanla(puan):
    """Tersine puanlama (4↔1, 3↔2, 2↔3, 1↔4)"""
    return 5 - puan  # 4→1, 3→2, 2→3, 1→4 dönüşümü

def puan_hesapla(cevaplar):
    """Verilen cevap listesi üzerinden toplam puanı hesapla"""
    # Tersine puanlanacak soru numaraları (0-index ile uyumlu olacak şekilde düzeltilmiş)
    tersine_sorular = {0, 1, 4, 7, 9, 10, 14, 15, 18, 19} 

    # Yeni puan dizisi oluştur
    duzeltilmis_puanlar = [
        tersine_puanla(cevap) if i in tersine_sorular else cevap
        for i, cevap in enumerate(cevaplar)
    ]

    # Toplam puanı hesapla
    toplam_puan = sum(duzeltilmis_puanlar)

    # Formüle göre yeni puanı hesapla
    yuzde_puan = ((toplam_puan - 20) / (80 - 20)) * (100 - 0) + 0
    yuzde_puan = round(yuzde_puan, 2)  # Sonucu yuvarla
    
    return yuzde_puan


def get_general_user_info():
    try:
        users_ref = db.collection('users')
        query = users_ref.where(filter=FieldFilter('isActive', '==', True)).limit(1)  # Sadece 1 kullanıcı çekiyoruz
        results = query.get()

        if results:
            user_doc = results[0]
            user_id = user_doc.id
            user_data = user_doc.to_dict()
            start_date = user_data.get('startDateTime')
            end_date = user_data.get('endDateTime')
            type = user_data.get('type')

            print(f"Genel kullanıcı ID: {user_id}")
            print(f"Start Date: {start_date}")
            print(f"End Date: {end_date}")

            return user_id, start_date, end_date, type
        else:
            print("Genel tipinde kullanıcı bulunamadı.")
            return None, None, None, None

    except Exception as e:
        print("Genel kullanıcıyı alırken hata oluştu:", e)
        return None, None, None


genel_avg_stress_level = None
genel_avg_stress_level_sinif = None
oneri_avg_stress_level = None
oneri_avg_stress_level_sinif = None


def save_data_to_firestore(data, user_id, start_date_time, end_date_time, type):
    global stress_levels, data_count
    global genel_avg_stress_level, genel_avg_stress_level_sinif, oneri_avg_stress_level, oneri_avg_stress_level_sinif
    try:
        # JSON verisini çözümle
        parsed_data = json.loads(data)

        # Alfa ve beta değerlerini al
        low_alpha = int(parsed_data['eegPower'].get('lowAlpha', None))
        high_alpha = int(parsed_data['eegPower'].get('highAlpha', None))
        low_beta = int(parsed_data['eegPower'].get('lowBeta', None))
        high_beta = int(parsed_data['eegPower'].get('highBeta', None))

        # StressLevel hesapla ve sigmoid fonksiyonuna uygula
        stress_level = round(sigmoid((low_beta + high_beta) / (low_alpha + high_alpha)) * 100)
        stress_level = (stress_level - 50) * 2

        if (end_date_time is not None and type == 'genel'):
            query = db.collection('eegReadings').where(filter=FieldFilter('userId', '==', user_id))\
                                                .where(filter=FieldFilter('startDateTime', '==', start_date_time))\
                                                .where(filter=FieldFilter('endDateTime', '==', start_date_time))\
                                                .where(filter=FieldFilter('type', '==', 'genel'))
            results = query.get()

            if end_date_time is not None:
                stress_levels = []
                for result in results:
                    stress_levels.append(result.get('stressLevel')) 

                genel_avg_stress_level = round(sum(stress_levels) / len(stress_levels))
                userRef.update({
                    'avgStressLevel': genel_avg_stress_level,
                    'endDateTime': None,
                })
                # Renk belirleme
                if genel_avg_stress_level <= 33:
                    genel_avg_stress_level_sinif = 'Düşük'
                elif genel_avg_stress_level <= 66:
                    genel_avg_stress_level_sinif = 'Orta'
                else:
                    genel_avg_stress_level_sinif = 'Yüksek'
            print(f"\nStres Seviyesi: {genel_avg_stress_level_sinif} {genel_avg_stress_level}{RESET}\n")
        
        if(end_date_time is not None and type in ['nefes', 'müzik', 'meditasyon']):
            query = db.collection('eegReadings').where(filter=FieldFilter('userId', '==', user_id))\
                                                .where(filter=FieldFilter('startDateTime', '==', start_date_time))\
                                                .where(filter=FieldFilter('endDateTime', '==', start_date_time))\
                                                .where(filter=FieldFilter('type', 'in', ['nefes', 'müzik', 'meditasyon']))
            results = query.get()

            if end_date_time is not None:
                stress_levels = []
                for result in results:
                    stress_levels.append(result.get('stressLevel'))

                oneri_avg_stress_level = round(sum(stress_levels) / len(stress_levels))
                
                userRef.update({
                    'endDateTime': None,
                })
                # Renk belirleme
                if oneri_avg_stress_level <= 33:
                    oneri_avg_stress_level_sinif = 'Düşük'
                elif oneri_avg_stress_level <= 66:
                    oneri_avg_stress_level_sinif = 'Orta'
                else:
                    oneri_avg_stress_level_sinif = 'Yüksek'
                print(f"\nStres Seviyesi: {oneri_avg_stress_level_sinif} {oneri_avg_stress_level}{RESET}\n")

        if type == 'bitir':
            query = db.collection('anketler').where(filter=FieldFilter('userId', '==', user_id))\
                                            .where(filter=FieldFilter('dateTime', '==', start_date_time))\
                                            .limit(1)
            results = query.get()

            if results:
                anket_doc = results[0]
                anket_data = anket_doc.to_dict()
                puanlar = anket_data.get('STAIList', [])
                yuzde_puan = puan_hesapla(puanlar)

            genel_level = genel_avg_stress_level
            oneri_level = oneri_avg_stress_level
            genel_sinif = genel_avg_stress_level_sinif
            oneri_sinif = oneri_avg_stress_level_sinif

            if yuzde_puan <= 33:
                stai_sinif = 'Düşük'
            elif yuzde_puan <= 66:
                stai_sinif = 'Orta'
            else:
                stai_sinif = 'Yüksek'

            data = {
                'genelEEGSonuc': genel_level,
                'oneriEEGSonuc': oneri_level,
                'genelEEGSinif': genel_sinif,
                'oneriEEGSinif': oneri_sinif,
                'STAISonuc': yuzde_puan,
                'STAISinif': stai_sinif,
                'userId': user_id,
                'startDateTime': start_date_time,
                'userRef': userRef,
            }

            db.collection('sonuclar').add(data)
            #1 kez kaydettikten sonra if'i kapat
            userRef.update({
                'type': None,
            })
                

        if (type in ['nefes', 'müzik', 'meditasyon', 'genel']):
        
            # Firestore için veri hazırla
            firestore_data = {
                'eSenseAttention': int(parsed_data['eSense'].get('attention', None)),
                'eSenseMeditation': int(parsed_data['eSense'].get('meditation', None)),
                'delta': int(parsed_data['eegPower'].get('delta', None)),
                'theta': int(parsed_data['eegPower'].get('theta', None)),
                'lowAlpha': low_alpha,
                'highAlpha': high_alpha,
                'lowBeta': low_beta,
                'highBeta': high_beta,
                'lowGamma': int(parsed_data['eegPower'].get('lowGamma', None)),
                'highGamma': int(parsed_data['eegPower'].get('highGamma', None)),
                'poorSignalLevel': int(parsed_data.get('poorSignalLevel', None)),
                'stressLevel': stress_level,
                'avgStressLevel': genel_avg_stress_level,
                'timestamp': datetime.now(),
                'userRef': userRef,
                'startDateTime': start_date_time,
                'endDateTime': end_date_time if end_date_time is not None else start_date_time,
                'userId': user_id,
                'type': type,
            }

            # Firestore'a kaydet
            db.collection('eegReadings').add(firestore_data)
            print("Veri Firestore'a kaydedildi:", firestore_data)
            print("--------------------")
        

    except Exception as e:
        print("Firestore'a kaydedilirken hata oluştu:", e)

# ThinkGear Connector bağlantı bilgileri
host = "127.0.0.1"
port = 13854

try:
    # ThinkGear Connector'a bağlan
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    # JSON formatında veri almak için komut gönder
    sock.send(b'{"enableRawOutput": false, "format": "Json"}\n')
    print("Bağlantı başarılı, veri bekleniyor...")

    while True:
        user_id, start_date_time, end_date_time, type = get_general_user_info()
        userRef = db.collection('users').document(user_id)
        data = sock.recv(1024).decode("latin1")
        if data:
            print("Alınan veri:", data)

            # Eğer gelen veri 'blinkStrength' içeriyorsa atla
            if 'blinkStrength' in data:
                continue
            
            if  user_id is not None:
                save_data_to_firestore(data, user_id, start_date_time, end_date_time, type)

except Exception as e:
    print("Bağlantı hatası:", e)

finally:
    sock.close()
