import re
import time
import os
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from groq import Groq
from bs4 import BeautifulSoup  # <-- 1. ADIM: BeautifulSoup kütüphanesini ekledik
from config import GROQ_API_KEY, MODEL_NAME

class SmartShoppingAgent:
    def __init__(self, headless=False):
        # Groq istemcisi
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model_name = MODEL_NAME

        # Chrome ayarları
        chrome_options = Options()

        # Kullanıcı profili - oturum bilgilerini saklar
        user_data = os.path.join(os.getcwd(), "chrome_profile")
        chrome_options.add_argument(f"--user-data-dir={user_data}")

        # Temel ayarlar
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1400,900")
        chrome_options.add_argument("--start-maximized")

        # Headless mod (opsiyonel)
        if headless:
            chrome_options.add_argument("--headless=new")

        # Bot algılamayı azalt
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        try:
            # Otomatik olarak doğru ChromeDriver'ı indir
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"Chrome başlatılamadı: {e}")
            self.driver = None

    def _get_groq_response(self, prompt):
        """Tüm Groq API isteklerini tek merkezden yöneten yardımcı fonksiyon."""
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                temperature=0.1,
                max_tokens=500
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"AI Hatası: {str(e)}"

    # <-- 2. ADIM: Akıllı Sayfa Temizleme Fonksiyonunu Sınıfa Ekledik
    def _get_clean_page_content(self, max_chars=4000):
        """Web sayfasının gereksiz kısımlarını (kodlar, menüler, reklamlar) temizler."""
        try:
            if not self.driver:
                return ""
            
            # Sayfanın HTML kodunu alıp BeautifulSoup'a veriyoruz
            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            
            # Yapay zekanın kafasını karıştıracak tüm çöp alanları siliyoruz
            for element in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
                element.decompose()
                
            # Kalan metni alıp ardışık gereksiz boşlukları temizliyoruz
            text = soup.get_text(separator=" ")
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = " ".join(chunk for chunk in chunks if chunk)
            
            return clean_text[:max_chars]
        except Exception as e:
            print(f"BeautifulSoup temizleme hatası: {e}")
            # Hata durumunda B Planı: Sistem kilitlenmesin diye eski düz metin yöntemine dön
            try:
                return self.driver.find_element(By.TAG_NAME, "body").text[:max_chars]
            except:
                return ""
            
    def _apply_stealth_behavior(self):
        """Web sitesinin bot olduğumuzu anlamaması için insansı hareketler taklit eder."""
        try:
            if not self.driver:
                return
            
            # 1. Sayfa açıldıktan sonra rastgele bir süre (1.5 - 3.5 saniye) hiçbir şey yapmadan bekle (İnsan gibi)
            time.sleep(random.uniform(1.5, 3.5))
            
            # 2. Sayfayı yavaşça aşağı kaydır (Scroll)
            # Bu işlem hem bot korumasını geçmek hem de aşağıda kalan fiyatların/görsellerin yüklenmesini sağlamak için çok önemlidir.
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_to = random.randint(400, min(900, total_height)) # Rastgele bir derinliğe kadar kaydır
            
            for position in range(0, scroll_to, 40): # 40'ar piksel yavaşça kaydır
                self.driver.execute_script(f"window.scrollTo(0, {position});")
                time.sleep(random.uniform(0.05, 0.15)) # Kaydırırken aralarda rastgele milisaniyeler bekle
                
            # 3. Aşağı kaydırdıktan sonra ürünü inceliyormuş gibi rastgele (2 - 4 saniye) bekle
            time.sleep(random.uniform(2.0, 4.0))
            
            # 4. Sayfayı tekrar en yukarı çıkar
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Stealth kamuflaj hatası: {e}")        

    def get_market_analysis(self):
        """Herhangi bir e-ticaret sayfasını analiz eder."""
        try:
            if not self.driver:
                return "Tarayıcı bağlı değil."

            title = self.driver.title
            self._apply_stealth_behavior()
            
            # <-- 3. ADIM: Eski ham body.text kodu yerine yeni temizleyiciyi bağladık (Sınırı 5000 yaptık)
            body_text = self._get_clean_page_content(max_chars=5000)

            prompt = f"""
            Ürün Başlığı: {title}
            Sayfa İçeriği: {body_text}

            Sen evrensel bir alışveriş asistanısın. Bu sayfadaki ürünü incele:
            1. Fiyat makul mü? (Piyasa ortalamasını düşün)
            2. Ürünün öne çıkan özellikleri neler?
            3. Güvenilirlik analizi yap (Fiyat çok mu düşük?)
            Yanıtını samimi ve kısa bir özet olarak ver.
            """
            return self._get_groq_response(prompt)
        except Exception as e:
            return f"Analiz hatası: {str(e)}"

    def extract_price_with_ai(self, html_snippet):
        """Eğer CSS seçiciler başarısız olursa, fiyatı metinden AI ile bulur."""
        prompt = f"Aşağıdaki metin içindeki ürünün satış fiyatını sadece sayı olarak yaz (Örn: 1540.50). Eğer bulamazsan '0' yaz:\n\n{html_snippet}"
        try:
            response_text = self._get_groq_response(prompt)
            price = re.findall(r"\d+\.\d+|\d+", response_text)
            return float(price[0]) if price else 0
        except:
            return 0

    def smart_process(self, user_query, current_url):
        """Sadece analiz yapmaz, kullanıcın niyetini (intent) anlar."""
        prompt = f"""
        Kullanıcı sorusu: {user_query}
        Şu anki URL: {current_url}

        Sen bir alışveriş asistanısın. Kullanıcın niyetini şu kategorilerden birine sok:
        1. ANALIZ: Ürün fiyatı/özellikleri hakkında yorum isterse.
        2. TAKIP: "Takibe al", "listeye ekle" gibi komutlar.
        3. SEPET: "Sepete ekle", "almak istiyorum" gibi komutlar.

        Yanıtını şu formatta ver:
        Eylem: [KATEGORI]
        Cevap: [Kullanıcıya vereceğin doğal dildeki yanıt]
        """
        return self._get_groq_response(prompt)

    def analyze_product_with_ai(self):
        if not self.driver:
            return {"stok": False, "fiyat": "Bilinmiyor"}
        try:
            self._apply_stealth_behavior()
            # <-- 4. ADIM: Bu fonksiyon içindeki kırpmayı da temizlenmiş metne çevirdik
            body_text = self._get_clean_page_content(max_chars=2500)
            return {"stok": "EVET", "fiyat": "Analiz Edildi"}
        except:
            return {"stok": "HATA", "fiyat": "0"}

    def close(self):
        """Tarayıcıyı kapat"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass