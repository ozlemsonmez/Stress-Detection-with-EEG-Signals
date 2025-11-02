# ANSI Renk Kodları
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"

puanlar = [1,4,3,3,2,2,4,2,3,1,4,3,3,2,2,3,3,1,2,2]  # 20 soruluk puan listesi

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
    
    return toplam_puan, duzeltilmis_puanlar, yuzde_puan

# Puanları işle ve sonucu yazdır
toplam_puan, yeni_puanlar, yuzde_puan = puan_hesapla(puanlar)

# Renk belirleme
if yuzde_puan <= 33:
    renk = GREEN
elif yuzde_puan <= 66:
    renk = YELLOW
else:
    renk = RED

#print("\nOrijinal Cevaplar:", puanlar)
#print("Düzeltilmiş Cevaplar:", yeni_puanlar)
#print(f"\nToplam Puan: {toplam_puan}")
print("--------------------------------")
print(f"Yüzdelik Puan: {renk}{yuzde_puan}{RESET}")
print("--------------------------------")
