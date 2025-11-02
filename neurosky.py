import socket
import json
from datetime import datetime
from firebase_admin import credentials, firestore, initialize_app
import math

# Firebase Firestore ayarları
cred = credentials.Certificate(r"C:/Users/melek/Desktop/ap/firebase-adminsdk.json")
initialize_app(cred)
db = firestore.client()

stress_levels = []
data_count = 0

# Sigmoid fonksiyonu tanımla
def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def save_data_to_firestore(data):
    global stress_levels, data_count
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
        if data_count < 10:
            stress_levels.append(stress_level)
            print(stress_levels)
            data_count += 1

        if data_count < 10:
            avg_stress_level = None
        elif data_count == 10:
            avg_stress_level = round(sum(stress_levels) / 10)
        print(avg_stress_level)
        
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
            'avgStressLevel': avg_stress_level,
            'timestamp': datetime.now(),
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
        data = sock.recv(1024).decode("latin1")
        if data:
            print("Alınan veri:", data)
            # eğer datadan blinkStrength geliyorsa bu işlemi atla
            if 'blinkStrength' in data:
                continue
            save_data_to_firestore(data)

except Exception as e:
    print("Bağlantı hatası:", e)

finally:
    sock.close()
