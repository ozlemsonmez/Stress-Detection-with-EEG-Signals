import numpy as np
from scipy.stats import wilcoxon

# Öneri öncesi EEG değerleri (%)
eeg_oncesi = [
    18, 25, 30, 15, 18, 33, 34, 36, 36, 49,
    44, 46, 44, 40, 38, 54, 43, 41, 50, 43,
    40, 33, 42, 34, 39, 50, 37, 39
]

# Öneri sonrası EEG değerleri (%)
eeg_sonrasi = [
    17, 21, 25, 13, 21, 34, 35, 31, 44, 43,
    44, 40, 34, 34, 35, 27, 34, 40, 44, 39,
    51, 33, 44, 46, 28, 46, 34, 28
]

# İki bağımlı grup arasında fark var mı?
statistic, p_value = wilcoxon(eeg_oncesi, eeg_sonrasi)

print("Wilcoxon Test İstatistiği:", statistic)
print("p-değeri:", p_value)
