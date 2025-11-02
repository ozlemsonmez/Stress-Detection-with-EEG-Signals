import firebase_admin
from firebase_admin import credentials, firestore

# Firebase Firestore ayarları
cred = credentials.Certificate(r"C:\Users\melek\Desktop\ap\firebase-adminsdk.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# 'eegReadings' koleksiyonundaki tüm belgeleri sil
collection_ref = db.collection('eegReadings')

# Tüm belgeleri al
# İlk belgeyi atlamak için bir sayaç kullan
counter = 0

# Tüm belgeleri al
docs = collection_ref.stream()

# Her belgeyi sil
for doc in docs:
    if counter == 0:
        counter += 1
        continue
    doc.reference.delete()
    print(f"Silinen belge ID: {doc.id}")
    counter += 1

print("Tüm kayıtlar silindi.") 