import streamlit as st
import json
import os
from datetime import datetime, timedelta

# Sayfa ayarları
st.set_page_config(page_title="Karos Boss Timer", page_icon="⚔️", layout="wide")

# Arayüzü güzelleştirmek için özel CSS kodumuz
st.markdown("""
    <style>
    [data-testid="stExpander"] details summary p {
        font-size: 26px !important;
        font-weight: 800 !important;
        color: #FF4B4B !important; 
    }
    div.stButton > button {
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚔️ Karos Online - Ortak Boss Takip Paneli")

# Verilerin ortak tutulacağı dosya
DOSYA_ADI = "karos_boss_sureleri.json"

# Haritalar ve o haritadaki boss'un yeniden doğma süresi (Dakika cinsinden)
HARITALAR = {
    "Lüpinel": 180,  # 3 saat
    "Tempreon": 180,  # 3 saat
    "Petrok": 300,  # 5 saat
    "Bahalasong": 360,  # 6 saat
    "Seron Adası": 540  # 9 saat
}

KANALLAR = ["Kanal 1", "Kanal 2", "Kanal 3"]


# Veri okuma fonksiyonu
def verileri_oku():
    if os.path.exists(DOSYA_ADI):
        with open(DOSYA_ADI, "r") as f:
            return json.load(f)
    return {}


# Veri kaydetme fonksiyonu
def verileri_kaydet(veriler):
    with open(DOSYA_ADI, "w") as f:
        json.dump(veriler, f)


# Aktif verileri çek
aktif_veriler = verileri_oku()

# Başlangıç verilerini oluştur ve eksik verileri tamamla
guncellendi_mi = False
for harita in HARITALAR.keys():
    if harita not in aktif_veriler:
        aktif_veriler[harita] = {}
        guncellendi_mi = True
    for kanal in KANALLAR:
        if kanal not in aktif_veriler[harita]:
            aktif_veriler[harita][kanal] = {
                "cikis_zamani": None,
                "eski_cikis_zamani": None,
                "geri_alinabilir": False
            }
            guncellendi_mi = True
        elif "geri_alinabilir" not in aktif_veriler[harita][kanal]:
            aktif_veriler[harita][kanal]["geri_alinabilir"] = False
            guncellendi_mi = True

if guncellendi_mi:
    verileri_kaydet(aktif_veriler)

# ---> SAAT DÜZELTMESİ BURADA <---
# Sunucu saati (UTC) üzerine 3 saat ekleyerek Türkiye saatini (UTC+3) buluyoruz.
su_an = datetime.utcnow() + timedelta(hours=3)

# Ekranı yenileme butonu
col_btn, _ = st.columns([1, 5])
with col_btn:
    if st.button("🔄 Ekranı Yenile / Senkronize Et", use_container_width=True):
        st.rerun()

st.markdown("---")

# Haritaları açılır kapanır paneller halinde gösterelim
for harita, bekleme_suresi in HARITALAR.items():
    saat_gosterimi = bekleme_suresi // 60
    with st.expander(f"🗺️ {harita} Bossları (Yeniden Doğma: {saat_gosterimi} Saat)", expanded=True):

        kanallar_col = st.columns(3)

        for i, kanal in enumerate(KANALLAR):
            with kanallar_col[i]:
                st.markdown(f"### {kanal}")

                detaylar = aktif_veriler[harita][kanal]
                cikis_zamani_str = detaylar.get("cikis_zamani")
                eski_cikis_str = detaylar.get("eski_cikis_zamani")
                geri_alinabilir = detaylar.get("geri_alinabilir", False)

                # Süre hesaplama ve gösterme
                if cikis_zamani_str:
                    cikis_zamani = datetime.strptime(cikis_zamani_str, "%Y-%m-%d %H:%M:%S")
                    if su_an < cikis_zamani:
                        kalan_sure = cikis_zamani - su_an

                        kalan_saat = int(kalan_sure.total_seconds() // 3600)
                        kalan_dakika = int((kalan_sure.total_seconds() % 3600) // 60)
                        kalan_saniye = int(kalan_sure.total_seconds() % 60)

                        st.warning(f"⏳ Kalan Süre: **{kalan_saat} sa {kalan_dakika} dk {kalan_saniye} sn**")
                        st.info(f"🕒 Çıkış Saati: **{cikis_zamani.strftime('%H:%M:%S')}**")
                    else:
                        st.success("🟢 BOSS ÇIKTI (Veya Çıkmak Üzere)")
                else:
                    st.success("🟢 BOSS ÇIKTI (Veya Çıkmak Üzere)")

                # Hızlı İşlem Butonları
                btn_col1, btn_col2 = st.columns(2)

                with btn_col1:
                    if st.button(f"⚔️ Kesildi", key=f"btn_kes_{harita}_{kanal}", use_container_width=True):
                        aktif_veriler[harita][kanal]["eski_cikis_zamani"] = cikis_zamani_str
                        aktif_veriler[harita][kanal]["geri_alinabilir"] = True

                        yeni_cikis = su_an + timedelta(minutes=bekleme_suresi)
                        aktif_veriler[harita][kanal]["cikis_zamani"] = yeni_cikis.strftime("%Y-%m-%d %H:%M:%S")
                        verileri_kaydet(aktif_veriler)
                        st.rerun()

                with btn_col2:
                    if st.button(f"↩️ Geri Al", key=f"btn_geri_{harita}_{kanal}", disabled=not geri_alinabilir,
                                 use_container_width=True):
                        aktif_veriler[harita][kanal]["cikis_zamani"] = eski_cikis_str
                        aktif_veriler[harita][kanal]["geri_alinabilir"] = False
                        verileri_kaydet(aktif_veriler)
                        st.rerun()

                # Manuel Saat Girişi Bölümü
                with st.expander("⚙️ Manuel Saat Gir"):
                    manuel_saat = st.time_input("Kesilme saati:", value=su_an.time(), key=f"saat_{harita}_{kanal}")

                    if st.button("Kaydet", key=f"btn_manuel_{harita}_{kanal}", use_container_width=True):
                        aktif_veriler[harita][kanal]["eski_cikis_zamani"] = cikis_zamani_str
                        aktif_veriler[harita][kanal]["geri_alinabilir"] = True

                        kesilme_zamani = su_an.replace(hour=manuel_saat.hour, minute=manuel_saat.minute, second=0,
                                                       microsecond=0)

                        if kesilme_zamani > su_an:
                            kesilme_zamani -= timedelta(days=1)

                        yeni_cikis = kesilme_zamani + timedelta(minutes=bekleme_suresi)
                        aktif_veriler[harita][kanal]["cikis_zamani"] = yeni_cikis.strftime("%Y-%m-%d %H:%M:%S")

                        verileri_kaydet(aktif_veriler)
                        st.rerun()