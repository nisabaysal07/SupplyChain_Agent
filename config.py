"""
Configuration Module:
Defines official domains, news agencies, trade press sources, matching dictionaries, 
keyword patterns for filtering, and global search settings for the supply chain analyzer.
"""


# 1) OFFICIAL INSTITUTIONS
OFFICIAL_DOMAINS = {
    "Global": ["wto.org", "imo.org", "icao.int", "gdacs.org", "reliefweb.int"],
    "Turkey": [
        "resmigazete.gov.tr",  
        "ticaret.gov.tr",      
        "uab.gov.tr",          
        "shgm.gov.tr",        
        "mgm.gov.tr",         
        "afad.gov.tr",          
    ],
    "China": ["mofcom.gov.cn", "english.mofcom.gov.cn", "customs.gov.cn", "english.customs.gov.cn"],
    "Taiwan": ["trade.gov.tw", "moea.gov.tw", "customs.gov.tw", "cwa.gov.tw", "twport.com.tw"],
    "South Korea": ["motie.go.kr", "customs.go.kr", "kma.go.kr", "airport.kr"],
    "Vietnam": ["moit.gov.vn", "customs.gov.vn"],
    "Malaysia": ["miti.gov.my", "customs.gov.my"],
    "United States": ["commerce.gov", "bis.doc.gov", "ustr.gov", "cbp.gov", "federalregister.gov"],
}

# 2) NEWS AGENCIES (state-run + international agencies) -> Searched with topic="news"
NEWS_AGENCY_DOMAINS = {
    "Global": ["reuters.com", "apnews.com", "bloomberg.com", "ft.com"],
    "Turkey": ["aa.com.tr"],
    "China": ["xinhuanet.com", "news.cn"],
    "Taiwan": ["focustaiwan.tw", "cna.com.tw"],
    "South Korea": ["yna.co.kr"],
    "Vietnam": ["vnanet.vn", "vietnamplus.vn"],
    "Malaysia": ["bernama.com"],
    "United States": [],
}

# 3) Trade Press: Used EXCLUSIVELY for port/airport logistics queries
TRADE_PRESS_DOMAINS = ["freightwaves.com", "maritime-executive.com"]
USE_TRADE_PRESS_FOR_LOGISTICS = True

SOURCE_DISPLAY_NAMES = {
    "reuters.com": "Reuters", "apnews.com": "AP News", "bloomberg.com": "Bloomberg",
    "ft.com": "Financial Times", "aa.com.tr": "Anadolu Ajansı", "xinhuanet.com": "Xinhua",
    "news.cn": "Xinhua", "focustaiwan.tw": "Focus Taiwan (CNA)", "cna.com.tw": "CNA",
    "yna.co.kr": "Yonhap", "vnanet.vn": "VNA", "vietnamplus.vn": "VietnamPlus (VNA)",
    "bernama.com": "Bernama", "wto.org": "WTO", "imo.org": "IMO", "icao.int": "ICAO",
    "gdacs.org": "GDACS", "reliefweb.int": "ReliefWeb", "resmigazete.gov.tr": "Resmî Gazete",
    "ticaret.gov.tr": "T.C. Ticaret Bakanlığı", "uab.gov.tr": "T.C. Ulaştırma Bakanlığı",
    "shgm.gov.tr": "SHGM", "mgm.gov.tr": "MGM", "afad.gov.tr": "AFAD",
    "mofcom.gov.cn": "MOFCOM", "customs.gov.cn": "China Customs (GACC)",
    "trade.gov.tw": "Taiwan BOFT", "moea.gov.tw": "Taiwan MOEA", "customs.gov.tw": "Taiwan Customs",
    "cwa.gov.tw": "Taiwan CWA", "twport.com.tw": "Taiwan International Ports",
    "motie.go.kr": "Korea MOTIE", "customs.go.kr": "Korea Customs", "kma.go.kr": "KMA",
    "airport.kr": "Incheon Airport", "moit.gov.vn": "Vietnam MOIT", "customs.gov.vn": "Vietnam Customs",
    "miti.gov.my": "Malaysia MITI", "customs.gov.my": "Malaysia Customs",
    "freightwaves.com": "FreightWaves", "maritime-executive.com": "Maritime Executive",
}


# MATCHING DICTIONARIES

COUNTRY_ALIASES = {
    "Turkey": ["turkey", "türkiye", "turkiye", "turkish", "ankara", "türk*"],
    "China": ["china", "chinese", "beijing", "prc", "çin"],
    "Taiwan": ["taiwan", "taiwanese", "chinese taipei", "taipei", "tayvan"],
    "South Korea": ["south korea", "korea", "korean", "seoul", "güney kore", "kore"],
    "Vietnam": ["vietnam", "viet nam", "vietnamese", "hanoi"],
    "Malaysia": ["malaysia", "malaysian", "kuala lumpur", "malezya"],
    "United States": ["united states", "u.s.", "washington", "abd"],
}

# Explicitly defined aliases for ports and airports
LOGISTICS_ALIASES = {
    "Port of Mersin": ["mersin"],
    "Istanbul Airport": ["istanbul airport", "istanbul havalimanı", "ist airport"],
    "Port of Shekou (Shenzhen)": ["shekou", "shenzhen port", "port of shenzhen"],
    "Port of Yantian (Shenzhen)": ["yantian", "shenzhen port", "port of shenzhen"],
    "Port of Ningbo-Zhoushan": ["ningbo", "zhoushan"],
    "Taiwan Taoyuan International Airport": ["taoyuan"],
    "Incheon International Airport": ["incheon"],
    "Port of Kaohsiung": ["kaohsiung"],
    "Tan Son Nhat International Airport": ["tan son nhat"],
    "Cai Mep Port": ["cai mep"],
}

DISRUPTION_TERMS = [
    "strike", "walkout", "industrial action", "closure", "closed", "shut", "shutdown",
    "shut down", "suspend", "suspension", "halt", "delay", "congestion", "backlog", "cancel",
    "cancelled", "canceled", "cancellation", "disrupt", "disruption", "typhoon", "storm", "flood",
    "flooding", "earthquake", "tsunami", "fire", "explosion", "fog", "protest", "blockade",
    "outage", "cyberattack", "lockdown", "evacuat*",
    "grev*", "kapat*", "kapan*", "iptal*", "fırtına*", "sel felaket*", "su baskın*", "deprem*",
    "yangın*", "ertelen*",
]
# Severe country-wide events 
SEVERE_COUNTRY_EVENT_TERMS = [
    "typhoon", "earthquake", "tsunami", "flood", "flooding", "shutdown", "shut",
    "nationwide strike", "general strike", "deprem*", "tayfun*",
]

TRADE_TERMS = [
    "tariff", "duty", "duties", "customs", "import", "export", "quota", "anti-dumping",
    "antidumping", "safeguard", "levy", "surcharge", "free trade", "trade agreement", "trade deal",
    "fta", "sanction", "embargo", "ban", "banned", "licence", "license", "export control",
    "trade remedy", "countervailing",
    "gümrük*", "vergi*", "ithalat*", "ihracat*", "kota*", "damping*", "serbest ticaret*",
    "ek mali yükümlülük*", "gözetim*", "korunma önlem*",
]
RESTRICTION_TERMS = [
    "ban", "banned", "restrict", "restriction", "control", "export control", "licence", "license",
    "licensing", "permit", "quota", "embargo", "sanction", "prohibit", "prohibition", "blacklist",
    "entity list", "yasak*", "kısıtla*", "izin*", "lisans*", "kota*",
]
PRICE_TERMS = ["price", "pricing", "cost", "contract price", "spot price", "fiyat*", "zamlan*"]

SECTOR_TERMS = [
    "electronic", "electronics", "semiconductor", "chip", "computer", "component", "it equipment",
    "information technology", "hs 84", "hs 85", "hs84", "hs85", "drone", "processor", "memory",
    "elektronik*", "bilgisayar*", "yarı iletken*", "bileşen*",
]

PRODUCT_TERMS = {
    "İşlemci": ["processor", "cpu", "semiconductor", "chip"],
    "Anakart": ["motherboard", "mainboard", "printed circuit board", "pcb"],
    "Bellek": ["memory", "dram", "ddr5", "ram module"],
    "SSD": ["ssd", "solid state drive", "nand", "flash memory"],
    "Ekran kartı": ["graphics card", "gpu", "graphics processing unit"],
    "Güç kaynağı": ["power supply", "psu", "power supply unit"],
    "Kasa": ["computer case", "pc case", "chassis"],
    "Soğutucu": ["cpu cooler", "cooler", "cooling fan", "heatsink"],
    "Monitör": ["monitor", "display panel", "lcd", "oled panel"],
}

# Headlines containing these terms are dropped immediately
NOISE_TITLE_TERMS = [
    "celebrity", "fashion", "k-pop", "actor", "actress", "murder", "stabbing", "football",
    "baseball", "basketball", "tennis", "recipe", "horoscope", "movie", "album",
]

COMMODITY_TITLE_TERMS = ["crude", "oil price", "diesel", "petroleum", "wheat", "fertilizer", "cocoa", "textile", "lng"]

JUNK_PHRASES = [
    "subscribe", "sign up", "cookie", "copyright", "all rights reserved", "read more", "click here",
    "related news", "privacy policy", "follow us", "download the app", "google play", "app store",
    "most read", "latest news", "see all", "opens new tab", "our standards", "trust principles",
    "purchase licensing rights", "suggested topics", "stay informed", "reporting by", "editing by",
    "unrivalled portfolio", "world-check", "data catalogue", "see here for a list",
    "reuters provides", "bernama provides", "more news", "©", "abone ol", "giriş yap",
    "bu site deneyimlerinizi", "dolar euro altın", "bist 100", "btc/usdt",
]

BAD_URL_PATTERNS = [
    "sitemap", "/tag/", "/tags/", "/category/", "/topic/", "/search", "archive", "digest",
    "roundup", "morning-briefing", "/culture/", "learningenglish", "/entertainment/",
    "/sport/", "/sports/", "/travel/", "/lifestyle/", "/video/", "/gallery/", "/galeri/",
]
BAD_TITLE_PATTERNS = ["port news", "morning briefing", "roundup", "daily wrap", "home -", "| home", "anasayfa"]

# SEARCH SETTINGS

SEARCH_DEPTH = "advanced"
MAX_RESULTS_PER_PASS = 5
MIN_TAVILY_SCORE = 0.30         
MAX_TEXT_CHARS = 20000          
MAX_SUMMARY_SENTENCES = 5
MAX_SUMMARY_CHARS = 1000
ADD_TURKIYE_QUERY_VARIANT = True 

# STRICT MODE: "If no relevant news is found, do not force it; report 'no news found'"

# Logistics: Port/airport name must be explicitly mentioned in the text
REQUIRE_LOCATION_NAME = True


PAIR_SAME_SENTENCE_ONLY = True

STRICT_MODE = True
STRICT_MIN_TAVILY_SCORE = 0.50

MAX_AGE_HOURS = 48
REJECT_UNDATED = True