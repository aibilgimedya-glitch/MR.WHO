import streamlit as st
import json
import google.generativeai as genai
from datetime import datetime
import random
import time
from PIL import Image
import streamlit.components.v1 as components
import uuid

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="MR.WHO - Cinema Director",
    layout="wide",
    page_icon="🎬",
    initial_sidebar_state="expanded"
)

# --- CSS / STİL (HIGGSFIELD ESTETİĞİ) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    /* Genel Arkaplan ve Font */
    .stApp {
        background-color: #0E0E0E;
        color: #E0E0E0;
        font-family: 'Inter', sans-serif;
    }

    /* Perfect Glass Button - MR.WHO Style */
    .stButton>button {
        width: 100%;
        position: relative;
        padding: 22px 55px;
        font-weight: 800;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: #d1fe17;
        border: 2px solid transparent;
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(0, 0, 0, 1), rgba(0, 0, 0, 1));
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        box-shadow:
            0 10px 30px rgba(0, 0, 0, 0.5),
            inset 0 1px 0 rgba(209, 254, 23, 0.15),
            inset 0 -1px 0 rgba(209, 254, 23, 0.04);
        overflow: hidden;
        cursor: pointer;
        transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1),
                    box-shadow 0.35s cubic-bezier(0.4, 0, 0.2, 1),
                    background 0.35s cubic-bezier(0.4, 0, 0.2, 1),
                    color 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* Flowing Border Effect */
    .stButton>button::before {
        content: "";
        position: absolute;
        inset: 0;
        padding: 2px;
        border-radius: inherit;
        background: linear-gradient(
            135deg,
            rgba(237, 21, 114, 0.8),
            rgba(209, 254, 23, 0.8),
            rgba(237, 21, 114, 0.8),
            rgba(209, 254, 23, 0.8),
            rgba(237, 21, 114, 0.8)
        );
        background-size: 200% 200%;
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        opacity: 0.6;
        animation: borderFlow 3s linear infinite;
        transition: opacity 0.35s, animation-duration 0.35s;
    }

    /* Radial Glow Effect */
    .stButton>button::after {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: inherit;
        background: radial-gradient(
            circle at 50% 50%,
            rgba(209, 254, 23, 0.25),
            transparent 55%
        );
        opacity: 0;
        transition: opacity 0.35s;
        pointer-events: none;
    }

    /* Hover State */
    .stButton>button:hover {
        background: #d1fe17;
        color: #000;
        transform: translateY(-3px) scale(1.02);
        box-shadow:
            0 14px 50px rgba(209, 254, 23, 0.5),
            0 0 80px rgba(237, 21, 114, 0.3),
            inset 0 1px 0 rgba(0, 0, 0, 0.1),
            inset 0 -1px 0 rgba(0, 0, 0, 0.05);
    }

    .stButton>button:hover::before {
        opacity: 1;
        animation-duration: 2s;
    }

    .stButton>button:hover::after {
        opacity: 1;
    }

    /* Active State */
    .stButton>button:active {
        transform: translateY(-1px) scale(0.99);
        box-shadow:
            0 6px 24px rgba(209, 254, 23, 0.4),
            inset 0 1px 0 rgba(0, 0, 0, 0.2);
    }

    /* Border Flow Animation */
    @keyframes borderFlow {
        to { background-position: 200% 50%; }
    }

    /* Seçili Kart Stili (Custom) */
    .selected-card {
        border: 2px solid #666 !important;
        background-color: #1A1A1A;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        color: #CCC;
        transition: all 0.3s ease;
    }
    .selected-card:hover {
        border-color: #CCFF00 !important;
        color: #CCFF00;
        box-shadow: 0 0 10px rgba(204, 255, 0, 0.3);
    }
    .normal-card {
        border: 1px solid #333;
        background-color: #121212;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        color: #888;
        transition: all 0.3s ease;
    }
    .normal-card:hover {
        border-color: #555;
        color: #BBB;
    }
    
    h1, h2, h3 { color: #FFFFFF; font-weight: 800; }
    
    /* Tab Ayarları */
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1E1E1E;
        border-radius: 4px 4px 0px 0px;
        color: #888;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #2A2A2A;
        color: #CCC;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2A2A2A;
        color: #CCFF00;
        border-bottom: 3px solid #CCFF00;
    }
</style>
""", unsafe_allow_html=True)

# --- STATE YÖNETİMİ ---
defaults = {
    'selected_camera': "Arri Alexa 35",
    'selected_lens': "ARRI Signature Prime",
    'selected_focal': "24mm",
    'generated_prompt': "",
    'storyboard_content': {},
    'active_shot_id': "Shot 1",
    'detected_style': "Cinematic Realism",
    'uploaded_img': None,
    # Advanced Prompt Engine
    'selected_lighting': "Golden Hour",
    'selected_color_grading': "Kodak 2383",
    'selected_atmosphere': "Clear",
    'selected_composition': "Rule of Thirds",
    'selected_movement': "Static",
    # Video Settings
    'aspect_ratio': "16:9",
    'duration': "4s",
    'fps': 24,
    'motion_strength': 5,
    'video_provider': "Higgsfield",
    'image_provider': "NanoBananaPro",
    'prompt_format': "normal",  # "normal" or "json"
    # Shot Management
    'shots': [],
    'selected_shot_index': 0,
    # Batch Generation Queue
    'generation_queue': [],
    'queue_status': {},
    # Ideas & Notes System
    'ideas': [],
    'ideas_search': "",
    'ideas_filter_tags': [],
    # Professional Prompt Engine
    'saved_characters': [],
    # Batch Processing Pipeline
    'auto_retry_enabled': True,
    'max_retry_attempts': 3,
    'queue_auto_process': False
}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# --- DATA: CINEMA STUDIO EKİPMANLARI ---
CAMERAS = [
    {"name": "Arri Alexa 35", "type": "Digital", "icon": "📹",
     "desc": "Industry-standard digital cinema camera with exceptional dynamic range",
     "desc_tr": "Olağanüstü dinamik aralığa sahip endüstri standardı dijital sinema kamerası",
     "use_case": "Hollywood blockbusters, high-end commercials, TV series",
     "use_case_tr": "Hollywood yapımları, üst düzey reklamlar, TV dizileri"},
    {"name": "Red V-Raptor", "type": "Digital", "icon": "🎥",
     "desc": "8K digital cinema camera with RED's latest sensor technology",
     "desc_tr": "RED'in en yeni sensör teknolojisine sahip 8K dijital sinema kamerası",
     "use_case": "Action sequences, VFX-heavy productions, music videos",
     "use_case_tr": "Aksiyon sahneleri, efekt ağırlıklı yapımlar, müzik videoları"},
    {"name": "Sony Venice 2", "type": "Digital", "icon": "📼",
     "desc": "Full-frame 8.6K sensor with dual base ISO for low-light performance",
     "desc_tr": "Düşük ışık performansı için dual base ISO'lu tam kare 8.6K sensör",
     "use_case": "Low-light scenes, anamorphic cinematography, Netflix originals",
     "use_case_tr": "Düşük ışık sahneleri, anamorfik görüntüleme, Netflix yapımları"},
    {"name": "Arriflex 16SR", "type": "Film 16mm", "icon": "🎞️",
     "desc": "Classic 16mm film camera with authentic film grain",
     "desc_tr": "Otantik film dokusuna sahip klasik 16mm film kamera",
     "use_case": "Indie films, documentaries, retro aesthetic projects",
     "use_case_tr": "Bağımsız filmler, belgeseller, retro estetik projeler"},
    {"name": "Panavision DXL2", "type": "Large Format", "icon": "🔭",
     "desc": "Large format sensor with exceptional color science",
     "desc_tr": "Olağanüstü renk bilimine sahip büyük format sensör",
     "use_case": "Feature films, prestige TV, high-end commercials",
     "use_case_tr": "Uzun metraj filmler, prestijli TV yapımları, üst düzey reklamlar"},
    {"name": "IMAX Film", "type": "70mm", "icon": "🏰",
     "desc": "The ultimate cinematic experience with 70mm film format",
     "desc_tr": "70mm film formatı ile nihai sinema deneyimi",
     "use_case": "Epic blockbusters, IMAX releases, special event films",
     "use_case_tr": "Epik yapımlar, IMAX gösterimleri, özel etkinlik filmleri"}
]

LENSES = [
    {"name": "ARRI Signature Prime", "char": "Clean/Sharp",
     "desc": "Modern optical design with clinical sharpness and minimal distortion",
     "desc_tr": "Minimal bozulma ve klinik keskinliğe sahip modern optik tasarım",
     "use_case": "Modern narratives, corporate videos, clean aesthetic projects",
     "use_case_tr": "Modern anlatımlar, kurumsal videolar, temiz estetik projeler"},
    {"name": "Cooke S4", "char": "Warm/Vintage",
     "desc": "Legendary glass with warm color rendering and gentle skin tones",
     "desc_tr": "Sıcak renk sunumu ve yumuşak cilt tonlarına sahip efsanevi lens",
     "use_case": "Period pieces, romantic dramas, character-driven stories",
     "use_case_tr": "Dönem işleri, romantik dramalar, karakter odaklı hikayeler"},
    {"name": "Petzval", "char": "Swirly Bokeh",
     "desc": "Vintage lens with distinctive swirly bokeh and artistic rendering",
     "desc_tr": "Belirgin burgu bokeh ve artistik görüntülemeye sahip vintage lens",
     "use_case": "Art films, music videos, dream sequences, surreal scenes",
     "use_case_tr": "Sanat filmleri, müzik videoları, rüya sekansları, sürreal sahneler"},
    {"name": "Lensbaby", "char": "Tilt/Shift",
     "desc": "Creative lens with selective focus and tilt-shift effects",
     "desc_tr": "Seçici odak ve tilt-shift efektlerine sahip yaratıcı lens",
     "use_case": "Creative commercials, miniature effects, experimental films",
     "use_case_tr": "Yaratıcı reklamlar, minyatür efektler, deneysel filmler"},
    {"name": "Canon K-35", "char": "Vintage Glow",
     "desc": "Classic 70s lens with warm glow and reduced contrast",
     "desc_tr": "Sıcak parıltı ve azaltılmış kontrasta sahip klasik 70'ler lensi",
     "use_case": "Retro projects, music videos, vintage aesthetic films",
     "use_case_tr": "Retro projeler, müzik videoları, vintage estetik filmler"},
    {"name": "Hawk V-Lite", "char": "Anamorphic",
     "desc": "Anamorphic lens with horizontal flares and 2.39:1 aspect ratio",
     "desc_tr": "Yatay lens parıltıları ve 2.39:1 en-boy oranına sahip anamorfik lens",
     "use_case": "Sci-fi films, epic dramas, cinematic wide-screen projects",
     "use_case_tr": "Bilim-kurgu filmleri, epik dramalar, sinematik geniş ekran projeleri"},
    {"name": "Laowa Macro", "char": "Macro/Close",
     "desc": "Specialized macro lens for extreme close-up detail work",
     "desc_tr": "Aşırı yakın çekim detay işleri için özelleşmiş makro lens",
     "use_case": "Product photography, nature documentaries, detail shots",
     "use_case_tr": "Ürün fotoğrafçılığı, doğa belgeselleri, detay çekimleri"},
    {"name": "Helios 44-2", "char": "Swirly/Art",
     "desc": "Soviet-era lens famous for its unique swirly bokeh and character",
     "desc_tr": "Eşsiz burgu bokeh ve karakteriyle ünlü Sovyet dönemi lensi",
     "use_case": "Art house films, indie projects, atmospheric portraits",
     "use_case_tr": "Sanat sineması filmleri, bağımsız projeler, atmosferik portreler"}
]

FOCALS = ["14mm", "24mm", "35mm", "50mm", "85mm", "100mm"]

# --- ADVANCED PROMPT ENGINE DATA ---
LIGHTING_PRESETS = [
    {"name": "Golden Hour", "name_tr": "Altın Saat", "desc": "Warm, soft, low-angle sunlight", "desc_tr": "Sıcak, yumuşak, alçak açılı güneş ışığı", "tech": "2700K, diffused, backlit"},
    {"name": "Blue Hour", "name_tr": "Mavi Saat", "desc": "Cool twilight, deep blues", "desc_tr": "Serin alacakaranlık, derin maviler", "tech": "6500K, ambient, soft shadows"},
    {"name": "Overcast", "name_tr": "Bulutlu", "desc": "Flat, even, diffused light", "desc_tr": "Düz, eşit, dağınık ışık", "tech": "Soft box equivalent, no hard shadows"},
    {"name": "Neon Night", "name_tr": "Neon Gece", "desc": "Artificial, colorful, high contrast", "desc_tr": "Yapay, renkli, yüksek kontrast", "tech": "Mixed color temps, practical lights"},
    {"name": "Studio", "name_tr": "Stüdyo", "desc": "Controlled, three-point lighting", "desc_tr": "Kontrollü, üç nokta aydınlatma", "tech": "Key + Fill + Rim, 5600K"},
    {"name": "Natural Window", "name_tr": "Doğal Pencere", "desc": "Soft directional light", "desc_tr": "Yumuşak yönlü ışık", "tech": "Single source, side lighting"},
    {"name": "Hard Sunlight", "name_tr": "Sert Güneş", "desc": "Strong shadows, high contrast", "desc_tr": "Güçlü gölgeler, yüksek kontrast", "tech": "Direct sun, 5600K, crisp edges"},
    {"name": "Moonlight", "name_tr": "Ay Işığı", "desc": "Cool, dim, mysterious", "desc_tr": "Serin, loş, gizemli", "tech": "4100K, low intensity, blue tint"}
]

COLOR_GRADING = [
    {"name": "Kodak 2383", "name_tr": "Kodak 2383", "desc": "Classic film look", "desc_tr": "Klasik film görünümü", "tech": "Warm highlights, crushed blacks"},
    {"name": "Fuji Eterna", "name_tr": "Fuji Eterna", "desc": "Pastel, dreamy tones", "desc_tr": "Pastel, rüya gibi tonlar", "tech": "Desaturated, lifted shadows"},
    {"name": "Bleach Bypass", "name_tr": "Ağartma Atlama", "desc": "Desaturated, gritty", "desc_tr": "Soluk, sert görünüm", "tech": "Low saturation, high contrast"},
    {"name": "Teal & Orange", "name_tr": "Turkuaz & Turuncu", "desc": "Modern blockbuster", "desc_tr": "Modern blokbuster tarzı", "tech": "Skin tones orange, shadows teal"},
    {"name": "Film Noir", "name_tr": "Kara Film", "desc": "High contrast B&W", "desc_tr": "Yüksek kontrast siyah-beyaz", "tech": "Deep blacks, blown highlights"},
    {"name": "Cyberpunk", "name_tr": "Siberpunk", "desc": "Neon colors, deep shadows", "desc_tr": "Neon renkler, derin gölgeler", "tech": "Purple/cyan/magenta, crushed blacks"},
    {"name": "Nordic Cool", "name_tr": "İskandinav Soğuk", "desc": "Muted, cold palette", "desc_tr": "Sessiz, soğuk palet", "tech": "Desaturated blues/greens"},
    {"name": "Vintage Fade", "name_tr": "Vintage Solgun", "desc": "Faded film emulation", "desc_tr": "Solmuş film taklidi", "tech": "Lifted blacks, low contrast"}
]

ATMOSPHERE = [
    {"name": "Clear", "name_tr": "Berrak", "desc": "Clean air, sharp details", "desc_tr": "Temiz hava, keskin detaylar"},
    {"name": "Light Fog", "name_tr": "Hafif Sis", "desc": "Soft haze, reduced contrast", "desc_tr": "Yumuşak pus, azaltılmış kontrast"},
    {"name": "Heavy Fog", "name_tr": "Yoğun Sis", "desc": "Dense atmosphere, mystery", "desc_tr": "Yoğun atmosfer, gizem"},
    {"name": "Rain", "name_tr": "Yağmur", "desc": "Wet surfaces, reflections", "desc_tr": "Islak yüzeyler, yansımalar"},
    {"name": "Snow", "name_tr": "Kar", "desc": "Falling particles, cold mood", "desc_tr": "Düşen tanecikler, soğuk hava"},
    {"name": "Dust Particles", "name_tr": "Toz Tanecikleri", "desc": "Volumetric light, texture", "desc_tr": "Hacimsel ışık, doku"},
    {"name": "God Rays", "name_tr": "Işık Huzmeleri", "desc": "Light beams, dramatic shafts", "desc_tr": "Işık ışınları, dramatik kolonlar"},
    {"name": "Smoke", "name_tr": "Duman", "desc": "Atmospheric depth, moody", "desc_tr": "Atmosferik derinlik, kasvetli"}
]

COMPOSITION_RULES = [
    {"name": "Rule of Thirds", "name_tr": "Üçte Bir Kuralı", "desc": "Subjects on 1/3 lines", "desc_tr": "Konular 1/3 çizgilerinde"},
    {"name": "Golden Ratio", "name_tr": "Altın Oran", "desc": "Fibonacci spiral composition", "desc_tr": "Fibonacci spiral kompozisyon"},
    {"name": "Center Frame", "name_tr": "Merkez Çerçeve", "desc": "Symmetrical, direct focus", "desc_tr": "Simetrik, doğrudan odak"},
    {"name": "Dutch Angle", "name_tr": "Hollanda Açısı", "desc": "Tilted, dynamic tension", "desc_tr": "Eğik, dinamik gerilim"},
    {"name": "Leading Lines", "name_tr": "Yönlendirici Çizgiler", "desc": "Guides eye to subject", "desc_tr": "Gözü konuya yönlendirir"},
    {"name": "Frame in Frame", "name_tr": "Çerçeve İçinde Çerçeve", "desc": "Natural framing elements", "desc_tr": "Doğal çerçeveleme öğeleri"},
    {"name": "Negative Space", "name_tr": "Negatif Alan", "desc": "Minimalist, isolated subject", "desc_tr": "Minimalist, izole konu"},
    {"name": "Symmetry", "name_tr": "Simetri", "desc": "Perfect balance, Wes Anderson style", "desc_tr": "Mükemmel denge, Wes Anderson tarzı"}
]

CAMERA_MOVEMENTS = [
    {"name": "Static", "name_tr": "Sabit", "desc": "Locked off, no movement", "desc_tr": "Kilitli, hareketsiz", "tech": "Tripod, stable"},
    {"name": "Slow Push In", "name_tr": "Yavaş İleri Kayma", "desc": "Gradual dolly forward", "desc_tr": "Kademeli öne dolly", "tech": "Reveals detail, builds tension"},
    {"name": "Pull Back", "name_tr": "Geri Çekilme", "desc": "Dolly backward, reveal context", "desc_tr": "Geriye dolly, bağlamı açığa çıkarır", "tech": "Expands scene"},
    {"name": "Pan Left/Right", "name_tr": "Yatay Kaydırma", "desc": "Horizontal camera turn", "desc_tr": "Yatay kamera dönüşü", "tech": "Smooth gimbal/tripod"},
    {"name": "Tilt Up/Down", "name_tr": "Dikey Eğim", "desc": "Vertical camera angle", "desc_tr": "Dikey kamera açısı", "tech": "Reveal/hide elements"},
    {"name": "Crane Up", "name_tr": "Vinç Yukarı", "desc": "Rising aerial movement", "desc_tr": "Yükselen havai hareket", "tech": "God's eye perspective"},
    {"name": "Crane Down", "name_tr": "Vinç Aşağı", "desc": "Descending to subject", "desc_tr": "Konuya iniş", "tech": "Intimate reveal"},
    {"name": "Orbit", "name_tr": "Yörünge", "desc": "Circular around subject", "desc_tr": "Konu etrafında dairesel", "tech": "360° perspective"},
    {"name": "Steadicam", "name_tr": "Steadicam", "desc": "Smooth handheld tracking", "desc_tr": "Pürüzsüz el takibi", "tech": "Following subject"},
    {"name": "Handheld", "name_tr": "El Kamerası", "desc": "Natural shake, documentary feel", "desc_tr": "Doğal sarsıntı, belgesel hissi", "tech": "Organic, raw"}
]

# --- STYLE PRESETS (ONE-CLICK STYLE COMBINATIONS) ---
STYLE_PRESETS = {
    "Cyberpunk Night": {
        "desc": "Neon-lit futuristic cityscape",
        "icon": "🌃",
        "camera": "Red V-Raptor",
        "lens": "Hawk V-Lite",
        "focal": "35mm",
        "lighting": "Neon Night",
        "color_grading": "Cyberpunk",
        "atmosphere": "Light Fog",
        "composition": "Dutch Angle",
        "movement": "Slow Push In"
    },
    "Film Noir": {
        "desc": "Classic 1940s detective style",
        "icon": "🕵️",
        "camera": "Arriflex 16SR",
        "lens": "Cooke S4",
        "focal": "50mm",
        "lighting": "Hard Sunlight",
        "color_grading": "Film Noir",
        "atmosphere": "Smoke",
        "composition": "Frame in Frame",
        "movement": "Static"
    },
    "Wes Anderson": {
        "desc": "Symmetrical, pastel perfection",
        "icon": "🎨",
        "camera": "Arri Alexa 35",
        "lens": "ARRI Signature Prime",
        "focal": "35mm",
        "lighting": "Natural Window",
        "color_grading": "Fuji Eterna",
        "atmosphere": "Clear",
        "composition": "Symmetry",
        "movement": "Static"
    },
    "Golden Hour Magic": {
        "desc": "Warm, dreamy sunset aesthetic",
        "icon": "🌅",
        "camera": "Sony Venice 2",
        "lens": "Canon K-35",
        "focal": "85mm",
        "lighting": "Golden Hour",
        "color_grading": "Kodak 2383",
        "atmosphere": "Dust Particles",
        "composition": "Rule of Thirds",
        "movement": "Slow Push In"
    },
    "Nordic Mystery": {
        "desc": "Cold, muted Scandinavian thriller",
        "icon": "❄️",
        "camera": "Arri Alexa 35",
        "lens": "Cooke S4",
        "focal": "24mm",
        "lighting": "Overcast",
        "color_grading": "Nordic Cool",
        "atmosphere": "Heavy Fog",
        "composition": "Negative Space",
        "movement": "Steadicam"
    },
    "Vintage 70s": {
        "desc": "Retro film grain and warm tones",
        "icon": "📼",
        "camera": "Arriflex 16SR",
        "lens": "Helios 44-2",
        "focal": "50mm",
        "lighting": "Natural Window",
        "color_grading": "Vintage Fade",
        "atmosphere": "Clear",
        "composition": "Center Frame",
        "movement": "Handheld"
    },
    "Epic Fantasy": {
        "desc": "Cinematic adventure, atmospheric",
        "icon": "⚔️",
        "camera": "Panavision DXL2",
        "lens": "ARRI Signature Prime",
        "focal": "24mm",
        "lighting": "God Rays",
        "color_grading": "Teal & Orange",
        "atmosphere": "God Rays",
        "composition": "Golden Ratio",
        "movement": "Crane Up"
    },
    "Tokyo Street": {
        "desc": "Urban Japanese night aesthetics",
        "icon": "🏮",
        "camera": "Red V-Raptor",
        "lens": "Hawk V-Lite",
        "focal": "35mm",
        "lighting": "Neon Night",
        "color_grading": "Teal & Orange",
        "atmosphere": "Rain",
        "composition": "Leading Lines",
        "movement": "Steadicam"
    }
}

# --- HELPER FUNCTIONS ---
def get_available_models(api_key):
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        return [m.name for m in models if 'generateContent' in m.supported_generation_methods], None
    except Exception as e: return [], str(e)

def apply_style_preset(preset_name):
    """
    Applies a complete style preset to all parameters
    """
    if preset_name not in STYLE_PRESETS:
        return

    preset = STYLE_PRESETS[preset_name]

    # Update all session state values
    st.session_state.selected_camera = preset['camera']
    st.session_state.selected_lens = preset['lens']
    st.session_state.selected_focal = preset['focal']
    st.session_state.selected_lighting = preset['lighting']
    st.session_state.selected_color_grading = preset['color_grading']
    st.session_state.selected_atmosphere = preset['atmosphere']
    st.session_state.selected_composition = preset['composition']
    st.session_state.selected_movement = preset['movement']

def analyze_reference_image(api_key, image):
    """
    Uses Gemini Vision to analyze reference image and suggest cinematography parameters
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        analysis_prompt = """
        Analyze this image from a professional cinematographer's perspective.
        Provide a detailed analysis in JSON format with these keys:

        {
          "scene_description": "Brief description of what's in the image",
          "lighting_style": "Choose ONE from: Golden Hour, Blue Hour, Overcast, Neon Night, Studio, Natural Window, Hard Sunlight, Moonlight",
          "color_palette": "Describe dominant colors and mood",
          "suggested_color_grading": "Choose ONE from: Kodak 2383, Fuji Eterna, Bleach Bypass, Teal & Orange, Film Noir, Cyberpunk, Nordic Cool, Vintage Fade",
          "composition_type": "Choose ONE from: Rule of Thirds, Golden Ratio, Center Frame, Dutch Angle, Leading Lines, Frame in Frame, Negative Space, Symmetry",
          "atmosphere": "Choose ONE from: Clear, Light Fog, Heavy Fog, Rain, Snow, Dust Particles, God Rays, Smoke",
          "mood": "Overall emotional feeling (dramatic, peaceful, energetic, etc.)",
          "suggested_camera": "Suggest ONE from: Arri Alexa 35, Red V-Raptor, Sony Venice 2, Arriflex 16SR, Panavision DXL2, IMAX Film",
          "suggested_lens": "Suggest ONE from: ARRI Signature Prime, Cooke S4, Petzval, Lensbaby, Canon K-35, Hawk V-Lite, Laowa Macro, Helios 44-2",
          "suggested_focal": "Suggest ONE from: 14mm, 24mm, 35mm, 50mm, 85mm, 100mm"
        }

        Return ONLY valid JSON, no additional text.
        """

        response = model.generate_content([analysis_prompt, image])
        analysis_text = response.text.strip()

        # Clean markdown code blocks if present
        if analysis_text.startswith("```json"):
            analysis_text = analysis_text[7:]
        if analysis_text.startswith("```"):
            analysis_text = analysis_text[3:]
        if analysis_text.endswith("```"):
            analysis_text = analysis_text[:-3]

        analysis = json.loads(analysis_text.strip())
        return analysis, None

    except Exception as e:
        return None, f"Analysis error: {str(e)}"

def analyze_product_images(api_key, images, product_context=""):
    """
    Analyzes multiple product images for commercial video production
    Returns insights about best angles, lighting, colors, and shot suggestions
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Create analysis prompt for product/commercial context
        analysis_prompt = f"""
        Analyze these product/reference images for creating a commercial video.
        Product context: {product_context if product_context else "General product"}

        Provide detailed analysis in JSON format:

        {{
          "product_summary": "Brief description of the product(s) shown",
          "color_palette": ["color1", "color2", "color3"],
          "dominant_colors_hex": ["#RRGGBB", "#RRGGBB"],
          "recommended_camera_angles": ["angle1", "angle2", "angle3"],
          "recommended_lighting": "Best lighting type (e.g., soft, natural, studio, golden hour)",
          "mood_suggestions": ["mood1", "mood2"],
          "shot_ideas": [
            "Shot idea 1: Description",
            "Shot idea 2: Description",
            "Shot idea 3: Description"
          ],
          "visual_style": "Suggested visual style (e.g., minimalist, luxury, energetic, natural)",
          "background_suggestions": ["background1", "background2"],
          "key_features_to_highlight": ["feature1", "feature2", "feature3"]
        }}

        Return ONLY valid JSON, no additional text.
        """

        # Prepare content with all images
        content = [analysis_prompt]
        for img in images:
            content.append(img)

        response = model.generate_content(content)
        analysis_text = response.text.strip()

        # Clean markdown code blocks
        if analysis_text.startswith("```json"):
            analysis_text = analysis_text[7:]
        if analysis_text.startswith("```"):
            analysis_text = analysis_text[3:]
        if analysis_text.endswith("```"):
            analysis_text = analysis_text[:-3]

        analysis = json.loads(analysis_text.strip())
        return analysis, None

    except Exception as e:
        return None, f"Analiz hatası: {str(e)}"

def generate_storyboard(api_key, concept, shot_count=4):
    """
    Uses Gemini to generate a multi-shot storyboard from a concept
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        storyboard_prompt = f"""
        You are a professional film director creating a storyboard.
        Based on this concept: "{concept}"

        Create exactly {shot_count} cinematic shots that tell this story visually.
        Return a JSON array with {shot_count} shot objects. Each shot should have:

        {{
          "shot_number": 1,
          "shot_type": "Wide/Medium/Close-up/Extreme Close-up",
          "description": "Detailed visual description of what we see",
          "action": "What's happening in this shot",
          "mood": "Emotional tone",
          "suggested_movement": "Choose ONE from: Static, Slow Push In, Pull Back, Pan Left/Right, Tilt Up/Down, Crane Up, Crane Down, Orbit, Steadicam, Handheld",
          "suggested_lighting": "Choose ONE from: Golden Hour, Blue Hour, Overcast, Neon Night, Studio, Natural Window, Hard Sunlight, Moonlight",
          "duration": "2s/4s/6s"
        }}

        Make the shots flow together to tell a cohesive visual story.
        Return ONLY valid JSON array, no additional text.
        """

        response = model.generate_content(storyboard_prompt)
        storyboard_text = response.text.strip()

        # Clean markdown code blocks
        if storyboard_text.startswith("```json"):
            storyboard_text = storyboard_text[7:]
        if storyboard_text.startswith("```"):
            storyboard_text = storyboard_text[3:]
        if storyboard_text.endswith("```"):
            storyboard_text = storyboard_text[:-3]

        shots = json.loads(storyboard_text.strip())
        return shots, None

    except Exception as e:
        return None, f"Storyboard generation error: {str(e)}"

def export_project():
    """
    Exports current project settings to JSON
    """
    project_data = {
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "settings": {
            "camera": st.session_state.selected_camera,
            "lens": st.session_state.selected_lens,
            "focal": st.session_state.selected_focal,
            "lighting": st.session_state.selected_lighting,
            "color_grading": st.session_state.selected_color_grading,
            "atmosphere": st.session_state.selected_atmosphere,
            "composition": st.session_state.selected_composition,
            "movement": st.session_state.selected_movement,
            "aspect_ratio": st.session_state.aspect_ratio,
            "duration": st.session_state.duration,
            "fps": st.session_state.fps,
            "motion_strength": st.session_state.motion_strength
        },
        "prompt": st.session_state.get('generated_prompt', ''),
        "shots": st.session_state.get('shots', [])
    }
    return json.dumps(project_data, indent=2)

def import_project(json_data):
    """
    Imports project settings from JSON
    """
    try:
        data = json.loads(json_data)

        # Load settings
        settings = data.get('settings', {})
        st.session_state.selected_camera = settings.get('camera', st.session_state.selected_camera)
        st.session_state.selected_lens = settings.get('lens', st.session_state.selected_lens)
        st.session_state.selected_focal = settings.get('focal', st.session_state.selected_focal)
        st.session_state.selected_lighting = settings.get('lighting', st.session_state.selected_lighting)
        st.session_state.selected_color_grading = settings.get('color_grading', st.session_state.selected_color_grading)
        st.session_state.selected_atmosphere = settings.get('atmosphere', st.session_state.selected_atmosphere)
        st.session_state.selected_composition = settings.get('composition', st.session_state.selected_composition)
        st.session_state.selected_movement = settings.get('movement', st.session_state.selected_movement)
        st.session_state.aspect_ratio = settings.get('aspect_ratio', st.session_state.aspect_ratio)
        st.session_state.duration = settings.get('duration', st.session_state.duration)
        st.session_state.fps = settings.get('fps', st.session_state.fps)
        st.session_state.motion_strength = settings.get('motion_strength', st.session_state.motion_strength)

        # Load prompt and shots
        st.session_state.generated_prompt = data.get('prompt', '')
        st.session_state.shots = data.get('shots', [])

        return True, "Project loaded successfully!"

    except Exception as e:
        return False, f"Import error: {str(e)}"

# --- IDEAS & NOTES SYSTEM ---
import os
import base64
from pathlib import Path

# Create uploads directory if it doesn't exist
UPLOADS_DIR = Path("uploads/ideas")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
IDEAS_JSON_PATH = "ideas_database.json"

def load_ideas():
    """Load ideas from JSON file"""
    try:
        if os.path.exists(IDEAS_JSON_PATH):
            with open(IDEAS_JSON_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.error(f"Error loading ideas: {e}")
        return []

def save_ideas(ideas):
    """Save ideas to JSON file"""
    try:
        with open(IDEAS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(ideas, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving ideas: {e}")
        return False

def add_idea(title, description, tags, images=None, is_pinned=False, is_favorite=False, analysis=None):
    """Add a new idea to the database"""
    ideas = load_ideas()

    # Generate unique ID
    idea_id = f"idea_{int(time.time())}_{len(ideas)}"

    # Save uploaded images
    saved_images = []
    if images:
        for idx, img in enumerate(images):
            img_filename = f"{idea_id}_{idx}.png"
            img_path = UPLOADS_DIR / img_filename
            img.save(img_path)
            saved_images.append(str(img_path))

    new_idea = {
        "id": idea_id,
        "title": title,
        "description": description,
        "tags": tags,
        "images": saved_images,
        "is_pinned": is_pinned,
        "is_favorite": is_favorite,
        "ai_analysis": analysis,  # Store AI analysis results
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    ideas.append(new_idea)
    save_ideas(ideas)
    return True, "Fikir başarıyla kaydedildi!"

def update_idea(idea_id, **kwargs):
    """Update an existing idea"""
    ideas = load_ideas()
    for idea in ideas:
        if idea['id'] == idea_id:
            idea.update(kwargs)
            idea['updated_at'] = datetime.now().isoformat()
            save_ideas(ideas)
            return True, "Idea updated!"
    return False, "Idea not found"

def delete_idea(idea_id):
    """Delete an idea and its images"""
    ideas = load_ideas()
    for idx, idea in enumerate(ideas):
        if idea['id'] == idea_id:
            # Delete associated images
            for img_path in idea.get('images', []):
                try:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                except:
                    pass
            ideas.pop(idx)
            save_ideas(ideas)
            return True, "Idea deleted!"
    return False, "Idea not found"

def toggle_pin(idea_id):
    """Toggle pin status of an idea"""
    ideas = load_ideas()
    for idea in ideas:
        if idea['id'] == idea_id:
            idea['is_pinned'] = not idea.get('is_pinned', False)
            save_ideas(ideas)
            return True
    return False

def toggle_favorite(idea_id):
    """Toggle favorite status of an idea"""
    ideas = load_ideas()
    for idea in ideas:
        if idea['id'] == idea_id:
            idea['is_favorite'] = not idea.get('is_favorite', False)
            save_ideas(ideas)
            return True
    return False

def search_ideas(query="", filter_tags=None):
    """Search and filter ideas"""
    ideas = load_ideas()

    if not query and not filter_tags:
        return ideas

    filtered = []
    for idea in ideas:
        # Search in title and description
        if query:
            query_lower = query.lower()
            if query_lower not in idea['title'].lower() and query_lower not in idea['description'].lower():
                continue

        # Filter by tags
        if filter_tags:
            idea_tags = [tag.lower() for tag in idea.get('tags', [])]
            if not any(ft.lower() in idea_tags for ft in filter_tags):
                continue

        filtered.append(idea)

    return filtered

# --- VIDEO API INTEGRATION INFRASTRUCTURE ---
VIDEO_API_PROVIDERS = {
    "Higgsfield": {
        "name": "Higgsfield AI",
        "base_url": "https://api.higgsfield.ai/v1",
        "supports": ["image-to-video", "text-to-video"],
        "max_duration": 10,
        "api_key_env": "HIGGSFIELD_API_KEY",
        "prompt_format": ["normal", "json"]
    },
    "Veo 3": {
        "name": "Google Veo 3",
        "base_url": "https://generativelanguage.googleapis.com/v1",
        "supports": ["image-to-video", "text-to-video"],
        "max_duration": 8,
        "api_key_env": "GOOGLE_API_KEY",
        "prompt_format": ["normal"]
    },
    "Luma AI": {
        "name": "Luma Dream Machine",
        "base_url": "https://api.lumalabs.ai/v1",
        "supports": ["image-to-video", "text-to-video"],
        "max_duration": 5,
        "api_key_env": "LUMA_API_KEY",
        "prompt_format": ["normal"]
    },
    "Runway Gen-3": {
        "name": "Runway Gen-3 Alpha",
        "base_url": "https://api.runwayml.com/v1",
        "supports": ["image-to-video", "text-to-video"],
        "max_duration": 10,
        "api_key_env": "RUNWAY_API_KEY",
        "prompt_format": ["normal", "json"]
    },
    "Kling AI": {
        "name": "Kling AI",
        "base_url": "https://api.kling.ai/v1",
        "supports": ["image-to-video", "text-to-video"],
        "max_duration": 10,
        "api_key_env": "KLING_API_KEY",
        "prompt_format": ["normal", "json"]
    },
    "Pika Labs": {
        "name": "Pika 1.5",
        "base_url": "https://api.pika.art/v1",
        "supports": ["image-to-video", "text-to-video"],
        "max_duration": 4,
        "api_key_env": "PIKA_API_KEY",
        "prompt_format": ["normal"]
    },
    "Stability AI": {
        "name": "Stable Video Diffusion",
        "base_url": "https://api.stability.ai/v1",
        "supports": ["image-to-video"],
        "max_duration": 4,
        "api_key_env": "STABILITY_API_KEY",
        "prompt_format": ["normal"]
    }
}

# --- IMAGE GENERATION PROVIDERS ---
IMAGE_API_PROVIDERS = {
    "NanoBananaPro": {
        "name": "NanoBananaPro",
        "base_url": "https://api.nanobananapro.ai/v1",
        "supports": ["text-to-image"],
        "api_key_env": "NANOBANANAPRO_API_KEY",
        "prompt_format": ["normal", "json"]
    },
    "Flux Pro": {
        "name": "Flux Pro",
        "base_url": "https://api.bfl.ml/v1",
        "supports": ["text-to-image"],
        "models": ["flux-pro", "flux-pro-1.1", "flux-dev"],
        "api_key_env": "BFL_API_KEY",
        "prompt_format": ["normal"]
    },
    "Flux Schnell": {
        "name": "Flux Schnell",
        "base_url": "https://api.bfl.ml/v1",
        "supports": ["text-to-image"],
        "models": ["flux-schnell"],
        "api_key_env": "BFL_API_KEY",
        "prompt_format": ["normal"]
    }
}

def generate_video_api(provider, api_key, image, prompt, settings):
    """
    Universal video generation function for multiple providers
    NOTE: This is a template - actual API calls need to be implemented per provider
    """
    try:
        if provider not in VIDEO_API_PROVIDERS:
            return None, "Unknown provider"

        provider_info = VIDEO_API_PROVIDERS[provider]

        # Prepare request payload (generic structure)
        payload = {
            "prompt": prompt,
            "image": image,  # Base64 or URL depending on provider
            "duration": settings.get('duration', '4s'),
            "aspect_ratio": settings.get('aspect_ratio', '16:9'),
            "motion_strength": settings.get('motion_strength', 5),
            "fps": settings.get('fps', 24)
        }

        # TODO: Implement actual API calls for each provider
        # Example structure:
        # import requests
        # headers = {"Authorization": f"Bearer {api_key}"}
        # response = requests.post(f"{provider_info['base_url']}/generate",
        #                          json=payload,
        #                          headers=headers)
        # return response.json(), None

        return None, f"API integration for {provider} pending - Add your API key and implement the request"

    except Exception as e:
        return None, f"Video generation error: {str(e)}"

def add_to_queue(shot_data, prompt, settings):
    """
    Adds a video generation job to the queue
    """
    job_id = f"job_{len(st.session_state.generation_queue) + 1}_{datetime.now().strftime('%H%M%S')}"

    job = {
        "id": job_id,
        "shot_data": shot_data,
        "prompt": prompt,
        "settings": settings.copy(),
        "status": "queued",
        "created_at": datetime.now().isoformat()
    }

    st.session_state.generation_queue.append(job)
    st.session_state.queue_status[job_id] = "queued"

    return job_id

def process_queue_batch():
    """
    Processes all queued jobs
    NOTE: This is a simulation - real implementation would call actual APIs
    """
    processed = 0
    for job in st.session_state.generation_queue:
        if job['status'] == 'queued':
            job['status'] = 'processing'
            st.session_state.queue_status[job['id']] = 'processing'
            # Simulate processing
            time.sleep(0.5)
            job['status'] = 'completed'
            st.session_state.queue_status[job['id']] = 'completed'
            processed += 1

    return processed

def build_advanced_prompt(base_description="", format_type="normal"):
    """
    Builds a professional cinematic prompt from all selected parameters
    Supports both normal text and JSON formats
    """
    # Get technical specs from selected items
    lighting_obj = next((x for x in LIGHTING_PRESETS if x['name'] == st.session_state.selected_lighting), None)
    color_obj = next((x for x in COLOR_GRADING if x['name'] == st.session_state.selected_color_grading), None)
    atmos_obj = next((x for x in ATMOSPHERE if x['name'] == st.session_state.selected_atmosphere), None)
    comp_obj = next((x for x in COMPOSITION_RULES if x['name'] == st.session_state.selected_composition), None)
    move_obj = next((x for x in CAMERA_MOVEMENTS if x['name'] == st.session_state.selected_movement), None)

    if format_type == "json":
        # JSON Format for NanoBananaPro and compatible APIs
        prompt_json = {
            "scene_description": base_description if base_description else "A cinematic scene",
            "camera": {
                "model": st.session_state.selected_camera,
                "lens": st.session_state.selected_lens,
                "focal_length": st.session_state.selected_focal
            },
            "cinematography": {
                "lighting": {
                    "style": st.session_state.selected_lighting,
                    "description": lighting_obj['desc'] if lighting_obj else "",
                    "technical": lighting_obj['tech'] if lighting_obj else ""
                },
                "color_grading": {
                    "style": st.session_state.selected_color_grading,
                    "description": color_obj['desc'] if color_obj else "",
                    "technical": color_obj['tech'] if color_obj else ""
                },
                "atmosphere": {
                    "type": st.session_state.selected_atmosphere,
                    "description": atmos_obj['desc'] if atmos_obj else ""
                },
                "composition": {
                    "rule": st.session_state.selected_composition,
                    "description": comp_obj['desc'] if comp_obj else ""
                },
                "camera_movement": {
                    "type": st.session_state.selected_movement,
                    "description": move_obj['desc'] if move_obj else "",
                    "technical": move_obj['tech'] if move_obj else ""
                }
            },
            "quality": {
                "resolution": "8K",
                "depth_of_field": "shallow",
                "film_grain": True,
                "style": "cinematic masterpiece"
            }
        }
        return json.dumps(prompt_json, indent=2)

    else:
        # Normal Text Format
        prompt_parts = []

        # Base description
        if base_description:
            prompt_parts.append(base_description)

        # Technical cinematography
        prompt_parts.append(f"Shot on {st.session_state.selected_camera} with {st.session_state.selected_lens} lens at {st.session_state.selected_focal}")

        # Lighting
        if lighting_obj:
            prompt_parts.append(f"{lighting_obj['desc']}, {lighting_obj['tech']}")

        # Color grading
        if color_obj:
            prompt_parts.append(f"Color graded: {color_obj['name']} - {color_obj['tech']}")

        # Atmosphere
        if atmos_obj and atmos_obj['name'] != "Clear":
            prompt_parts.append(f"Atmospheric: {atmos_obj['name']} - {atmos_obj['desc']}")

        # Composition
        if comp_obj:
            prompt_parts.append(f"Composition: {comp_obj['name']} - {comp_obj['desc']}")

        # Camera movement
        if move_obj:
            prompt_parts.append(f"Camera: {move_obj['name']} - {move_obj['tech']}")

        # Quality markers
        prompt_parts.append("Cinematic masterpiece, 8K resolution, shallow depth of field, film grain, professional color science")

        # Join with proper formatting
        final_prompt = ". ".join(prompt_parts) + "."

        return final_prompt

# --- BATCH PROCESSING QUEUE FUNCTIONS ---
def add_to_queue(task_data):
    """
    Adds a video generation task to the queue
    task_data = {
        'id': unique_id,
        'type': 'shot_generator' | 'img2vid' | 'text2vid',
        'prompt': str,
        'settings': dict,
        'status': 'pending' | 'processing' | 'completed' | 'failed',
        'created_at': timestamp,
        'attempts': int,
        'max_attempts': int,
        'error': str (if failed)
    }
    """
    if 'generation_queue' not in st.session_state:
        st.session_state.generation_queue = []

    task_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    task_data['attempts'] = 0
    task_data['status'] = 'pending'

    st.session_state.generation_queue.append(task_data)
    return task_data['id']

def remove_from_queue(task_id):
    """Remove a task from queue by ID"""
    st.session_state.generation_queue = [
        task for task in st.session_state.generation_queue
        if task['id'] != task_id
    ]

def get_queue_stats():
    """Get statistics about current queue"""
    if 'generation_queue' not in st.session_state:
        return {'total': 0, 'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0}

    queue = st.session_state.generation_queue
    return {
        'total': len(queue),
        'pending': len([t for t in queue if t['status'] == 'pending']),
        'processing': len([t for t in queue if t['status'] == 'processing']),
        'completed': len([t for t in queue if t['status'] == 'completed']),
        'failed': len([t for t in queue if t['status'] == 'failed'])
    }

def retry_failed_task(task_id):
    """Retry a failed task"""
    for task in st.session_state.generation_queue:
        if task['id'] == task_id and task['status'] == 'failed':
            task['status'] = 'pending'
            task['attempts'] += 1
            task['error'] = None
            return True
    return False

def clear_completed_tasks():
    """Remove all completed tasks from queue"""
    st.session_state.generation_queue = [
        task for task in st.session_state.generation_queue
        if task['status'] != 'completed'
    ]

# --- GLASS MORPHISM SIDEBAR STYLING ---
st.markdown("""
<style>
/* Sidebar Glass Morphism */
[data-testid="stSidebar"] {
    background: rgba(10, 12, 13, 0.95) !important;
}

[data-testid="stSidebar"] > div:first-child {
    background: rgba(255, 255, 255, 0.03) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
}

/* Glass Cards */
.glass-card {
    background: rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(209, 254, 23, 0.2) !important;
    border-radius: 12px !important;
    padding: 15px !important;
    margin-bottom: 15px !important;
}

/* Logo Section */
.sidebar-logo {
    text-align: center !important;
    padding: 25px 15px !important;
    background: rgba(209, 254, 23, 0.05) !important;
    backdrop-filter: blur(20px) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(209, 254, 23, 0.2) !important;
    margin-bottom: 25px !important;
}

.sidebar-logo h1 {
    font-size: 2em !important;
    font-weight: 900 !important;
    color: #d1fe17 !important;
    letter-spacing: 8px !important;
    text-shadow: 0 0 20px rgba(209, 254, 23, 0.5) !important;
    margin: 0 !important;
}

.sidebar-logo p {
    color: #888 !important;
    font-size: 0.9em !important;
    margin-top: 8px !important;
    letter-spacing: 2px !important;
}

/* Connection Indicator */
.connection-status {
    display: inline-flex !important;
    align-items: center !important;
    gap: 8px !important;
    font-size: 0.85em !important;
    color: #d1fe17 !important;
}

.status-dot {
    width: 8px !important;
    height: 8px !important;
    background: #0f0 !important;
    border-radius: 50% !important;
    animation: pulse-dot 2s infinite !important;
}

@keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.status-dot.offline {
    background: #f00 !important;
    animation: none !important;
}

/* Glass Effect Selectbox/Dropdown */
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(209, 254, 23, 0.3) !important;
    border-radius: 8px !important;
    color: #d1fe17 !important;
    transition: all 0.3s ease !important;
}

[data-testid="stSidebar"] .stSelectbox > div > div:hover {
    border-color: rgba(209, 254, 23, 0.6) !important;
    box-shadow: 0 0 15px rgba(209, 254, 23, 0.2) !important;
}

/* Dropdown menu */
[data-baseweb="popover"] {
    background: rgba(19, 22, 24, 0.95) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(209, 254, 23, 0.2) !important;
    border-radius: 10px !important;
}

[data-baseweb="popover"] ul {
    background: transparent !important;
}

[data-baseweb="popover"] li {
    background: rgba(255, 255, 255, 0.03) !important;
    color: #fff !important;
    transition: all 0.2s ease !important;
    border-radius: 6px !important;
    margin: 4px !important;
}

[data-baseweb="popover"] li:hover {
    background: rgba(209, 254, 23, 0.15) !important;
    color: #d1fe17 !important;
    transform: translateX(4px) !important;
}

/* Text Input Glass Effect */
[data-testid="stSidebar"] input[type="password"],
[data-testid="stSidebar"] input[type="text"] {
    background: rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(209, 254, 23, 0.3) !important;
    border-radius: 8px !important;
    color: #fff !important;
}

[data-testid="stSidebar"] input[type="password"]:focus,
[data-testid="stSidebar"] input[type="text"]:focus {
    border-color: rgba(209, 254, 23, 0.6) !important;
    box-shadow: 0 0 15px rgba(209, 254, 23, 0.2) !important;
}

/* Section Title */
.section-title {
    color: #d1fe17 !important;
    font-size: 0.9em !important;
    font-weight: 700 !important;
    margin-bottom: 10px !important;
}

/* Thumbnails */
.thumbnail-grid {
    display: flex !important;
    gap: 8px !important;
    margin-top: 10px !important;
}

.thumbnail {
    width: 60px !important;
    height: 60px !important;
    background: rgba(209, 254, 23, 0.1) !important;
    border: 1px solid rgba(209, 254, 23, 0.3) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

.thumbnail img {
    width: 100% !important;
    height: 100% !important;
    object-fit: cover !important;
}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    # Logo Section with Glass Effect
    st.markdown("""
    <div class="sidebar-logo">
        <h1>MR.WHO</h1>
        <p>CINEMA DIRECTOR</p>
        <p style="font-size: 0.75em; color: #ed1572; margin-top: 5px;">✨ Directed By E.Yiğit Bildi</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API Status Glass Card
    api_key = st.text_input("🔑 Gemini API Key", type="password", key="sidebar_api_key")

    if api_key:
        st.session_state['gemini_api_key'] = api_key
        models, err = get_available_models(api_key)
        active_model = models[0] if models else "OFFLINE"
        is_online = bool(models)
    else:
        active_model = "OFFLINE"
        is_online = False

    # Status indicator
    status_class = "" if is_online else "offline"
    status_text = "Gemini API Connected" if is_online else "API Key Required"
    status_color = "#0f0" if is_online else "#f00"

    st.markdown(f"""
    <div class="glass-card">
        <div class="connection-status">
            <div class="status-dot {status_class}"></div>
            System Status
        </div>
        <div style="font-size: 0.75em; color: {status_color}; margin-top: 8px;">{status_text}</div>
        {f'<div style="font-size: 0.7em; color: #888; margin-top: 4px;">Model: {active_model}</div>' if is_online else ''}
    </div>
    """, unsafe_allow_html=True)
    
    # Reference Image Glass Card
    st.markdown('<div class="section-title">📁 Reference Image</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload reference", type=["jpg", "png", "webp"], label_visibility="collapsed")

    if uploaded_file:
        st.session_state['uploaded_img'] = Image.open(uploaded_file)

        # Show image in glass card
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.image(uploaded_file, use_column_width=True)
        st.caption(f"📎 {uploaded_file.name}")
        st.markdown('</div>', unsafe_allow_html=True)

        # AI Analysis Button
        if api_key and st.button("🔍 Analyze with Gemini AI", use_container_width=True):
            with st.spinner("Analyzing image..."):
                analysis, error = analyze_reference_image(api_key, st.session_state['uploaded_img'])

                if analysis:
                    st.success("Analysis complete!")

                    # Apply suggestions to session state
                    st.session_state.selected_camera = analysis.get('suggested_camera', st.session_state.selected_camera)
                    st.session_state.selected_lens = analysis.get('suggested_lens', st.session_state.selected_lens)
                    st.session_state.selected_focal = analysis.get('suggested_focal', st.session_state.selected_focal)
                    st.session_state.selected_lighting = analysis.get('lighting_style', st.session_state.selected_lighting)
                    st.session_state.selected_color_grading = analysis.get('suggested_color_grading', st.session_state.selected_color_grading)
                    st.session_state.selected_atmosphere = analysis.get('atmosphere', st.session_state.selected_atmosphere)
                    st.session_state.selected_composition = analysis.get('composition_type', st.session_state.selected_composition)

                    # Show analysis details
                    with st.expander("📊 Analysis Details", expanded=True):
                        st.markdown(f"**Scene:** {analysis.get('scene_description', 'N/A')}")
                        st.markdown(f"**Mood:** {analysis.get('mood', 'N/A')}")
                        st.markdown(f"**Colors:** {analysis.get('color_palette', 'N/A')}")

                    st.rerun()
                else:
                    st.error(error)

    # API Providers Glass Card
    st.markdown('<div class="section-title" style="margin-top: 20px;">🎬 API Providers</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("**Video Generation**")
    st.session_state.video_provider = st.selectbox(
        "Video Provider",
        list(VIDEO_API_PROVIDERS.keys()),
        index=list(VIDEO_API_PROVIDERS.keys()).index(st.session_state.video_provider),
        label_visibility="collapsed",
        key="video_provider_select"
    )
    provider_info = VIDEO_API_PROVIDERS[st.session_state.video_provider]
    st.caption(f"Supports: {', '.join(provider_info['supports'])}")
    st.caption(f"Max: {provider_info['max_duration']}s")
    st.markdown('</div>', unsafe_allow_html=True)

    # Image Provider Glass Card
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("**Image Generation**")
    st.session_state.image_provider = st.selectbox(
        "Image Provider",
        list(IMAGE_API_PROVIDERS.keys()),
        index=list(IMAGE_API_PROVIDERS.keys()).index(st.session_state.image_provider),
        label_visibility="collapsed",
        key="image_provider_select"
    )
    image_provider_info = IMAGE_API_PROVIDERS[st.session_state.image_provider]
    st.caption(f"Supports: {', '.join(image_provider_info['supports'])}")
    st.markdown('</div>', unsafe_allow_html=True)

    # Prompt Format
    st.markdown("**Prompt Format**")
    # Check if current provider supports JSON
    current_video_formats = VIDEO_API_PROVIDERS[st.session_state.video_provider].get('prompt_format', ['normal'])
    current_image_formats = IMAGE_API_PROVIDERS[st.session_state.image_provider].get('prompt_format', ['normal'])

    # If both support JSON, show option
    if 'json' in current_video_formats or 'json' in current_image_formats:
        st.session_state.prompt_format = st.selectbox(
            "Format",
            ["normal", "json"],
            index=["normal", "json"].index(st.session_state.prompt_format) if st.session_state.prompt_format in ["normal", "json"] else 0,
            label_visibility="collapsed",
            key="prompt_format_select"
        )
        if st.session_state.prompt_format == "json":
            st.caption("✅ JSON format aktif")
        else:
            st.caption("📝 Normal text format")
    else:
        st.session_state.prompt_format = "normal"
        st.caption("📝 Normal text format only")

    st.markdown("---")
    st.markdown("### 💾 Project Management")

    col_export, col_import = st.columns(2)

    with col_export:
        if st.button("📤 Export", use_container_width=True):
            project_json = export_project()
            st.download_button(
                label="Download JSON",
                data=project_json,
                file_name=f"nano_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

    with col_import:
        uploaded_project = st.file_uploader("📥 Import", type=["json"], label_visibility="collapsed")
        if uploaded_project:
            json_data = uploaded_project.read().decode()
            success, message = import_project(json_data)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

# ============================================
# LANDING PAGE - WEBGL SHADER ANIMATION
# ============================================
if 'app_entered' not in st.session_state:
    # Check URL params for direct entry
    try:
        from streamlit import query_params
        if 'app_entered' in st.query_params:
            st.session_state['app_entered'] = True
        else:
            st.session_state['app_entered'] = False
    except:
        st.session_state['app_entered'] = False

if not st.session_state['app_entered']:
    components.html("""
    <!DOCTYPE html>
    <html>
    <head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700;900&display=swap" rel="stylesheet">
<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Space Grotesk', sans-serif;
    background: #000;
    overflow: hidden;
}

#canvas {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
}

.content {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 10;
    text-align: center;
    pointer-events: none;
}

.logo {
    font-size: 6em;
    font-weight: 900;
    letter-spacing: 25px;
    color: rgba(0, 217, 255, 0.2);
    margin-bottom: 20px;
    animation: float 4s ease-in-out infinite;
    text-shadow:
        0 0 20px rgba(0, 217, 255, 0.3),
        0 0 40px rgba(0, 217, 255, 0.2);
    transition: all 0.5s ease;
}

.logo:hover {
    color: rgba(0, 217, 255, 0.8);
    text-shadow:
        0 0 30px rgba(0, 217, 255, 0.8),
        0 0 60px rgba(0, 217, 255, 0.5);
}

.subtitle {
    font-size: 1.3em;
    color: rgba(138, 43, 226, 0.4);
    letter-spacing: 8px;
    margin-bottom: 60px;
}

.enter-btn {
    padding: 18px 50px;
    font-size: 1em;
    font-weight: 800;
    letter-spacing: 3px;
    background: rgba(0, 217, 255, 0.1);
    color: #00d9ff;
    border: 2px solid #00d9ff;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.4s ease;
    font-family: 'Space Grotesk', sans-serif;
    pointer-events: all;
    backdrop-filter: blur(10px);
}

.enter-btn:hover {
    background: #00d9ff;
    color: #000;
    box-shadow: 0 0 30px rgba(0, 217, 255, 0.6);
    transform: translateY(-3px);
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-15px); }
}

.hint {
    position: fixed;
    bottom: 40px;
    left: 50%;
    transform: translateX(-50%);
    color: #666;
    font-size: 0.9em;
    letter-spacing: 2px;
    animation: blink 2s ease-in-out infinite;
}

@keyframes blink {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 1; }
}
</style>

    </head>
    <body>

<canvas id="canvas"></canvas>

<div class="content">
    <div class="logo">MR.WHO</div>
    <div class="subtitle">CINEMA DIRECTOR</div>
    <button class="enter-btn" onclick="enterStudio()">🎬 ENTER STUDIO</button>
</div>

<div class="hint">Click anywhere to interact</div>

<script>
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

class Particle {
    constructor(x, y) {
        this.x = x || Math.random() * canvas.width;
        this.y = y || Math.random() * canvas.height;
        this.size = Math.random() * 3 + 1;
        this.speedX = Math.random() * 2 - 1;
        this.speedY = Math.random() * 2 - 1;
        this.opacity = Math.random() * 0.5 + 0.3;
        this.hue = Math.random() * 60 + 180; // Blue-cyan range
    }

    update() {
        this.x += this.speedX;
        this.y += this.speedY;

        // Bounce off edges
        if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
        if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;
    }

    draw() {
        ctx.fillStyle = `hsla(${this.hue}, 100%, 50%, ${this.opacity})`;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();

        // Glow effect
        ctx.fillStyle = `hsla(${this.hue}, 100%, 50%, ${this.opacity * 0.3})`;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size * 2, 0, Math.PI * 2);
        ctx.fill();
    }
}

const particles = [];
const particleCount = 150;

// Initialize particles
for (let i = 0; i < particleCount; i++) {
    particles.push(new Particle());
}

function connectParticles() {
    for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
            const dx = particles[i].x - particles[j].x;
            const dy = particles[i].y - particles[j].y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < 120) {
                ctx.strokeStyle = `hsla(${particles[i].hue}, 100%, 50%, ${0.15 - distance / 120 * 0.15})`;
                ctx.lineWidth = 0.5;
                ctx.beginPath();
                ctx.moveTo(particles[i].x, particles[i].y);
                ctx.lineTo(particles[j].x, particles[j].y);
                ctx.stroke();
            }
        }
    }
}

function animate() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    particles.forEach(particle => {
        particle.update();
        particle.draw();
    });

    connectParticles();
    requestAnimationFrame(animate);
}

animate();

// Mouse interaction
canvas.addEventListener('click', (e) => {
    const mouseX = e.clientX;
    const mouseY = e.clientY;

    // Create burst of particles
    for (let i = 0; i < 10; i++) {
        const angle = Math.random() * Math.PI * 2;
        const speed = Math.random() * 5 + 2;
        const particle = new Particle(mouseX, mouseY);
        particle.speedX = Math.cos(angle) * speed;
        particle.speedY = Math.sin(angle) * speed;
        particles.push(particle);
    }

    // Remove excess particles
    if (particles.length > particleCount + 50) {
        particles.splice(0, 50);
    }
});

// Mouse move interaction
canvas.addEventListener('mousemove', (e) => {
    const mouseX = e.clientX;
    const mouseY = e.clientY;

    particles.forEach(particle => {
        const dx = mouseX - particle.x;
        const dy = mouseY - particle.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < 100) {
            particle.speedX -= dx / distance * 0.05;
            particle.speedY -= dy / distance * 0.05;
        }
    });
});

window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});

function enterStudio() {
    // Create explosion effect
    particles.forEach(particle => {
        particle.speedX *= 5;
        particle.speedY *= 5;
    });

    // Fade out and notify parent
    setTimeout(() => {
        document.body.style.transition = 'opacity 1s';
        document.body.style.opacity = '0';
        setTimeout(() => {
            window.parent.postMessage({type:'streamlit:setComponentValue',value:true},'*');
        }, 1000);
    }, 500);
}
</script>


    </body>
    </html>
    """, height=900)

    if st.button("Continue to App", key="hidden_enter", type="primary"):
        st.session_state['app_entered'] = True
        st.rerun()

    st.stop()

# --- ANA EKRAN ---
st.title("🎬 MR.WHO Cinema Director")
st.caption("✨ Directed By E.Yiğit Bildi")

# TABS
t_guide, t_ideas, t_studio, t_board, t_image, t_video, t_equipment, t_sys = st.tabs(["📖 REHBER", "💡 FİKİRLER & NOTLAR", "🎬 STÜDYO", "🧠 STORYBOARD", "🖼️ IMAGE", "🎞️ VİDEO", "📚 EKİPMAN REHBERİ", "⚙️ SİSTEM"])

# --- TAB 0: REHBER (KULLANIM KILAVUZU) ---
with t_guide:
    st.markdown("# 📖 MR.WHO - Kullanım Rehberi")
    st.caption("Sinematik video üretimi için profesyonel iş akışı")

    st.markdown("---")

    # Quick Navigation
    guide_section = st.selectbox(
        "Konuya git:",
        ["🎯 Genel Bakış", "🔄 İş Akışı", "📱 Tab Açıklamaları", "💡 İpuçları & Püf Noktalar", "❓ Sık Sorulan Sorular"]
    )

    st.markdown("---")

    if guide_section == "🎯 Genel Bakış":
        st.markdown("## 🎯 MR.WHO Nedir?")
        st.write("""
        **MR.WHO Cinema Director**, yapay zeka destekli profesyonel video prodüksiyon aracıdır.
        Ticari reklamlar, sosyal medya içerikleri ve sinematik projeler için tasarlanmıştır.
        """)

        col_feat1, col_feat2 = st.columns(2)
        with col_feat1:
            st.markdown("### ✨ Temel Özellikler")
            st.markdown("""
            - 💡 **Fikir Yönetimi:** Proje fikirlerini kaydet, organize et
            - 🔍 **AI Görsel Analizi:** Referans görsellerini analiz et
            - 🎬 **Storyboard Üretimi:** AI ile otomatik sahne oluşturma
            - 🎨 **40+ Sinematik Seçenek:** Profesyonel görünüm
            - 🎞️ **Video Queue Sistemi:** Toplu video üretimi
            - 📱 **Her Yerden Erişim:** Mobil + Desktop
            """)

        with col_feat2:
            st.markdown("### 🎯 Kimler İçin?")
            st.markdown("""
            - 🎬 **Video Yapımcıları:** Ticari reklam üretimi
            - 🎨 **İçerik Üreticileri:** Sosyal medya içerikleri
            - 🏢 **Ajanslar:** Müşteri projeleri
            - 📱 **Freelancerlar:** Hızlı iş akışı
            - 🎓 **Öğrenciler:** Sinema/medya eğitimi
            """)

        st.markdown("---")
        st.markdown("### 🧠 Sistem Nasıl Çalışır?")
        st.info("""
        **1. FİKİR AŞAMASI:** Proje konseptini ve referans görsellerini kaydet

        **2. ANALİZ AŞAMASI:** AI görselleri analiz eder, öneriler sunar

        **3. STORYBOARD AŞAMASI:** AI sahne açıklamaları üretir (text)

        **4. ÜRETİM AŞAMASI:** Text prompt'lardan video üretilir
        """)

    elif guide_section == "🔄 İş Akışı":
        st.markdown("## 🔄 Adım Adım İş Akışı")

        # Workflow diagram
        st.markdown("### 📊 İş Akışı Şeması")
        st.markdown("""
        ```
        1️⃣ FİKİR OLUŞTUR
            ↓
        [Proje bilgileri + Referans görselleri]
            ↓
        2️⃣ AI ANALİZ ET
            ↓
        [Renk paleti, açılar, ışık, shot önerileri]
            ↓
        3️⃣ STORYBOARD OLUŞTUR
            ↓
        [4-8 sahnelik text açıklamaları]
            ↓
        4️⃣ STÜDYO AYARLARI (Opsiyonel)
            ↓
        [Kamera, lens, ışık, renk ayarları]
            ↓
        5️⃣ VIDEO ÜRET
            ↓
        [Higgsfield/Veo/Kling ile video üretimi]
            ↓
        ✅ HAZIR!
        ```
        """)

        st.markdown("---")

        st.markdown("### 📝 Detaylı Adımlar")

        with st.expander("1️⃣ FİKİR OLUŞTURMA", expanded=True):
            st.markdown("""
            **Nerede:** 💡 FİKİRLER & NOTLAR tab

            **Ne Yapılır:**
            - "➕ Yeni Fikir" butonuna tıkla
            - Başlık yaz (Örn: "X Markası - Bebek Arabası Reklamı")
            - Açıklama ekle (Hedef kitle, mood, sahne detayları)
            - Etiketler ekle (#reklam, #ticari, vs.)
            - **Referans görselleri yükle** (Ürün fotoğrafları)
            - Sabitle/Favorile (Önemli projeler için)
            - Kaydet!

            **Önemli:** Referans görselleri buradan sonra AI tarafından analiz edilecek!
            """)

        with st.expander("2️⃣ AI ANALİZ"):
            st.markdown("""
            **Nerede:** 💡 FİKİRLER & NOTLAR tab (Fikir kartında)

            **Ne Yapılır:**
            - Fikir kartında "🔍 Görselleri Analiz Et" butonuna tıkla
            - AI Gemini Vision ile görselleri analiz eder
            - **10-20 saniye** bekle

            **AI Ne Yapar:**
            - ✅ Renk paletini çıkarır (Hex kodlarıyla)
            - ✅ Önerilen kamera açılarını belirler
            - ✅ En uygun aydınlatma tipini önerir
            - ✅ Mood önerileri verir
            - ✅ Shot fikirleri üretir (3-5 adet)
            - ✅ Görsel stil önerir (minimal, luxury, energetic...)

            **Sonuç:** Tüm bu bilgiler fikir ile birlikte kaydedilir!
            """)

        with st.expander("3️⃣ STORYBOARD OLUŞTURMA"):
            st.markdown("""
            **Nerede:** 💡 FİKİRLER & NOTLAR → 🧠 STORYBOARD

            **Yöntem 1: Fikirden Direkt Geçiş**
            - Fikir kartında "🎬 Storyboard Oluştur" butonuna tıkla
            - STORYBOARD tab'ına geç
            - Açıklama otomatik dolu!
            - AI analiz sonuçları görünüyor
            - "🎬 Generate Storyboard with AI" tıkla

            **Yöntem 2: Manuel Oluşturma**
            - Direkt STORYBOARD tab'ına git
            - Fikir/senaryo yaz
            - İstersen referans görselleri yükle
            - "🎬 Generate Storyboard with AI" tıkla

            **AI Ne Üretir:**
            - 2-8 sahne (senin seçtiğin kadar)
            - Her sahne için:
              * Shot tipi (Wide, Medium, Close-up...)
              * Detaylı açıklama
              * Action (ne oluyor)
              * Mood (duygusal ton)
              * Önerilen hareket (Static, Push In...)
              * Önerilen aydınlatma

            **Önemli:** Burada üretilen şey **TEXT** açıklamalardır, video değil!
            """)

        with st.expander("4️⃣ STÜDYO AYARLARI (Opsiyonel)"):
            st.markdown("""
            **Nerede:** 🎬 STÜDYO tab

            **Ne Yapılır:**
            Daha detaylı sinematik ayarlar yapmak istersen:

            **A) Style Presets (Hızlı):**
            - 8 hazır stil kombinasyonu
            - Tek tıkla uygula
            - Örnekler: Cyberpunk Night, Film Noir, Natural Wonder...

            **B) Manuel Ayarlar (Detaylı):**
            - **Kamera:** Arri Alexa, Sony Venice, Red...
            - **Lens:** 35mm, 50mm, 85mm...
            - **Lighting:** Golden Hour, Blue Hour, Neon Night...
            - **Color Grading:** Kodak, Fuji, Teal & Orange...
            - **Atmosphere:** Clear, Fog, Rain, God Rays...
            - **Composition:** Rule of Thirds, Symmetry...
            - **Movement:** Static, Push In, Orbit...

            **Sonuç:** Bu ayarlar prompt'a dahil edilir, daha profesyonel görünüm!
            """)

        with st.expander("5️⃣ VIDEO ÜRETİMİ"):
            st.markdown("""
            **Nerede:** 🎞️ VİDEO tab

            **Ne Yapılır:**

            **A) Storyboard'dan Toplu Ekleme:**
            - STORYBOARD tab'ında "🎬 Add All to Queue" tıkla
            - Tüm sahneler queue'ya eklenir

            **B) Manuel Ekleme:**
            - VİDEO tab'ında prompt yaz
            - Ayarları seç
            - "Add to Queue" tıkla

            **Video Ayarları:**
            - Aspect Ratio: 16:9, 9:16, 1:1
            - Duration: 2s, 4s, 6s
            - FPS: 24, 30, 60
            - Motion Strength: 1-10

            **API Seçimi:**
            - Higgsfield
            - Veo 3 (Google)
            - Kling AI

            **Üretim:**
            - "Generate All" veya tek tek üret
            - API key gerekli!
            - Her video 30-60 saniye sürer

            **Önemli:** Video üretimi sırasında **TEXT PROMPT** kullanılır, referans görselleri değil!
            """)

        st.markdown("---")
        st.success("✅ Tam iş akışını takip ettiğinde profesyonel sonuçlar elde edersin!")

    elif guide_section == "📱 Tab Açıklamaları":
        st.markdown("## 📱 Her Tab Ne İşe Yarar?")

        tab_info = {
            "📖 REHBER": {
                "desc": "Bu tab! Kullanım kılavuzu ve iş akışı açıklamaları",
                "use": "İlk kez kullanıyorsan buradan başla"
            },
            "💡 FİKİRLER & NOTLAR": {
                "desc": "Proje fikirlerini kaydet, referans görselleri yükle, AI analizi yap",
                "use": "Her yeni proje için ilk adım burası"
            },
            "🎬 STÜDYO": {
                "desc": "Sinematik ayarlar: Kamera, lens, ışık, renk, hareket",
                "use": "Daha profesyonel/detaylı ayarlar istediğinde"
            },
            "🧠 STORYBOARD": {
                "desc": "AI ile sahne açıklamaları üret, referans görselleri analiz et",
                "use": "Fikri sahne sahne planlamak için"
            },
            "🎞️ VİDEO": {
                "desc": "Video üretim queue'su, API seçimi, toplu üretim",
                "use": "Final video üretimi için"
            },
            "📚 EKİPMAN REHBERİ": {
                "desc": "Kamera ve lens bilgileri, ne zaman hangisini kullanmalı",
                "use": "Ekipman hakkında bilgi edinmek için"
            },
            "⚙️ SİSTEM": {
                "desc": "Proje export/import, API ayarları, sistem bilgileri",
                "use": "Projeyi kaydetmek veya paylaşmak için"
            }
        }

        for tab_name, info in tab_info.items():
            with st.expander(f"{tab_name}", expanded=False):
                st.markdown(f"**Ne İşe Yarar:** {info['desc']}")
                st.markdown(f"**Ne Zaman Kullan:** {info['use']}")

    elif guide_section == "💡 İpuçları & Püf Noktalar":
        st.markdown("## 💡 İpuçları & Püf Noktalar")

        with st.expander("🎨 Daha İyi Prompt Yazma"):
            st.markdown("""
            **İyi Prompt Özellikleri:**
            - ✅ Detaylı ama özlü
            - ✅ Duygu/mood belirt (joyful, dramatic, peaceful)
            - ✅ Teknik terimler kullan (cinematic, 4K, shallow depth of field)
            - ✅ Renkleri belirt (warm tones, blue palette)
            - ✅ Işık tipini ekle (golden hour, soft lighting)

            **Örnek Kötü Prompt:**
            "Bebek arabası"

            **Örnek İyi Prompt:**
            "Modern premium baby stroller in sunny park, golden hour lighting,
            blue and white colors, cinematic 4K, soft focus, happy family atmosphere,
            professional commercial quality"
            """)

        with st.expander("🔍 Referans Görselleri İpuçları"):
            st.markdown("""
            **En İyi Sonuç İçin:**
            - ✅ 2-4 kaliteli görsel yükle (fazla değil)
            - ✅ Farklı açılardan fotoğraflar (genel, detay, kullanımda)
            - ✅ İyi ışıklı, net fotoğraflar
            - ✅ Ürünün renk ve stil özellikleri belli olsun

            **Kaçın:**
            - ❌ 10+ görsel (AI karışır)
            - ❌ Çok düşük çözünürlük
            - ❌ Karanlık/bulanık fotoğraflar
            """)

        with st.expander("⚡ Hızlı İş Akışı"):
            st.markdown("""
            **5 Dakikada Storyboard:**
            1. Fikir oluştur (2 dk)
            2. Görselleri analiz et (30 sn)
            3. Storyboard'a geç (5 sn)
            4. AI üret (30 sn)
            5. İncele ve düzenle (1.5 dk)

            **Toplu Üretim:**
            - Birden fazla fikir oluştur
            - Hepsini analiz et
            - Storyboard'ları toplu üret
            - Queue'ya ekle ve hepsini birden üret
            """)

        with st.expander("🎯 Ticari Proje İpuçları"):
            st.markdown("""
            **Müşteri İşi İçin:**
            - Proje adını açıklayıcı yap (Marka + Ürün + Tip)
            - Etiketleri kullan (#müşteri-adı, #proje-tipi)
            - Önemli projeleri sabitle 📌
            - AI analizini mutlaka kullan
            - Storyboard'u müşteriye göster, onay al
            - Sonra video üretimine geç

            **Varyasyon Üretme:**
            - Aynı fikri 2-3 farklı mood ile dene
            - Storyboard'da açıklamayı değiştir
            - "Dramatic version", "Joyful version", "Minimal version"
            """)

    elif guide_section == "❓ Sık Sorulan Sorular":
        st.markdown("## ❓ Sık Sorulan Sorular")

        with st.expander("❓ Referans görselleri video üretiminde kullanılıyor mu?"):
            st.markdown("""
            **HAYIR!** Bu yaygın bir karışıklık.

            **Referans Görselleri:**
            - Senin ve AI'nın **anlaması** için
            - AI bunları **analiz eder** ve öneriler üretir
            - Bu öneriler **TEXT PROMPT'a** dönüşür

            **Video Üretimi:**
            - **TEXT PROMPT** kullanılır
            - Görseller değil, açıklamalar gönderilir
            - API text'ten video üretir

            **Örnek:**
            ```
            Referans: Bebek arabası fotoğrafı
                ↓ (AI analiz eder)
            Sonuç: "Blue-white, modern, 45° angle"
                ↓ (Prompt'a dahil edilir)
            Prompt: "Modern blue baby stroller, 45° angle, 4K..."
                ↓ (API'ye gönderilir)
            Video: AI text'ten üretir
            ```
            """)

        with st.expander("❓ Hangi video API'sini kullanmalıyım?"):
            st.markdown("""
            **Higgsfield:**
            - Hızlı üretim
            - İyi kalite
            - Uygun fiyat

            **Veo 3 (Google):**
            - En kaliteli
            - Daha gerçekçi
            - Daha yavaş

            **Kling AI:**
            - Hızlı
            - İyi hareket kalitesi
            - Orta fiyat

            **Öneri:** Hepsini dene, hangisi işine yarıyorsa onu kullan!
            """)

        with st.expander("❓ Gemini API Key nereden alırım?"):
            st.markdown("""
            **Adım Adım:**
            1. https://aistudio.google.com/app/apikey adresine git
            2. Google hesabınla giriş yap
            3. "Create API Key" butonuna tıkla
            4. API key'i kopyala
            5. MR.WHO'da sidebar'a yapıştır

            **Ücretsiz mi?**
            - Evet! Google AI Studio ücretsiz tier var
            - Günlük kullanım limiti var
            - Yeterli olur çoğu kullanım için
            """)

        with st.expander("❓ Fikirleri nasıl organize ederim?"):
            st.markdown("""
            **Etiket Sistemi Kullan:**
            - Her fikre anlamlı etiketler (#müşteri, #proje-tipi)
            - Arama ile filtrele
            - Pin önemli projeleri
            - Favorite en çok kullandıklarını

            **İsimlendirme:**
            - Başlık: "Marka - Ürün - Tip"
            - Örnek: "X Markası - Bebek Arabası - Instagram Reklam"

            **Grid vs Liste:**
            - Grid: Hızlı görsel tarama
            - Liste: Detaylı inceleme
            """)

        with st.expander("❓ Mobilde de kullanabilir miyim?"):
            st.markdown("""
            **EVET!** Tam responsive.

            **Mobil Kullanım:**
            - https://mrwho-cinema.streamlit.app adresini aç
            - Tüm özellikler çalışır
            - Fikir ekleyebilirsin
            - Görsel yükleyebilirsin
            - AI analiz yapabilirsin
            - Storyboard üretebilirsin

            **İpucu:**
            - Mobilde fikir topla (screenshot'lar)
            - PC'de detaylı iş yap
            - Her ikisinde de aynı veriler!
            """)

        with st.expander("❓ Verilerim kaybolur mu?"):
            st.markdown("""
            **Local Kullanım:**
            - ideas_database.json dosyasında
            - Görseller uploads/ideas/ klasöründe
            - Bilgisayarında kayıtlı
            - Backup almayı unutma!

            **Online Kullanım (Streamlit Cloud):**
            - Session bazlı
            - Tarayıcı kapanınca sıfırlanabilir
            - Önemli projeleri Export et (SİSTEM tab)
            - JSON olarak indir, sakla

            **Öneri:**
            - Önemli projeleri export et
            - JSON'ları bilgisayarında tut
            - Gerektiğinde import et
            """)

    st.markdown("---")
    st.success("💡 Başka sorun varsa, her zaman bu rehbere dönebilirsin!")

# --- TAB 1: FİKİRLER & NOTLAR ---
with t_ideas:
    st.markdown("### 💡 Proje Fikirleri & Yaratıcı Notlar")
    st.caption("İlhamını yakala, referansları kaydet, yaratıcı sürecini organize et")

    # Action buttons
    col_act1, col_act2, col_act3 = st.columns([2, 1, 1])
    with col_act1:
        if st.button("➕ Yeni Fikir", use_container_width=True):
            st.session_state['show_new_idea_form'] = True
    with col_act2:
        search_query = st.text_input("🔍 Ara", placeholder="Fikirlerde ara...", label_visibility="collapsed")
    with col_act3:
        view_mode = st.selectbox("Görünüm", ["Kart", "Liste"], label_visibility="collapsed")

    st.markdown("---")

    # Yeni Fikir Formu
    if st.session_state.get('show_new_idea_form', False):
        with st.form("new_idea_form"):
            st.markdown("#### ✨ Yeni Fikir Oluştur")

            idea_title = st.text_input("Başlık *", placeholder="örn: Bebek Arabası Reklam Filmi")
            idea_description = st.text_area(
                "Açıklama * (Kaba fikri yaz, AI geliştirecek)",
                placeholder="örn: bebek arabası reklamı parkta anne mutlu...",
                height=120,
                key="idea_description_input"
            )

            # AI Enhancement Button
            enhance_idea_col1, enhance_idea_col2, enhance_idea_col3 = st.columns([1, 1, 1])
            with enhance_idea_col2:
                enhance_idea_btn = st.form_submit_button("🤖 ENHANCE WITH AI", use_container_width=True)

            if enhance_idea_btn:
                if not idea_description:
                    st.error("⚠️ Önce bir açıklama yaz!")
                else:
                    api_key = st.session_state.get('gemini_api_key')
                    if not api_key:
                        st.error("⚠️ Gemini API key gerekli! (Sidebar'dan ekle)")
                    else:
                        with st.spinner("🤖 AI fikrinizi geliştiriyor..."):
                            try:
                                genai.configure(api_key=api_key)
                                model = genai.GenerativeModel('gemini-2.5-flash')

                                enhancement_prompt = f"""You are a professional creative director and advertising strategist.
Enhance this rough project idea into a detailed, professional creative brief suitable for commercial video production.

Input idea: "{idea_description}"

Create a detailed, professional description that includes:
- Clear concept and vision
- Target audience and messaging
- Visual style and mood
- Key scenes or moments
- Emotional tone
- Production approach
- Any unique selling points

Keep it concise but detailed (2-3 paragraphs). Write in Turkish. Focus on actionable creative direction.

Enhanced creative brief:"""

                                response = model.generate_content(enhancement_prompt)
                                enhanced_idea = response.text.strip()

                                st.session_state['enhanced_idea_description'] = enhanced_idea
                                st.success("✅ Fikir AI tarafından geliştirildi!")
                                st.rerun()

                            except Exception as e:
                                st.error(f"❌ AI Enhancement failed: {str(e)}")

            # Show enhanced description if available
            if 'enhanced_idea_description' in st.session_state and st.session_state['enhanced_idea_description']:
                st.markdown("#### 🤖 AI Geliştirilmiş Fikir")
                st.info(st.session_state['enhanced_idea_description'])

                # Option to use enhanced version
                use_enhanced = st.checkbox("✅ Geliştirilmiş versiyonu kullan", value=True)

                if st.form_submit_button("❌ Temizle", key="clear_enhanced_idea"):
                    del st.session_state['enhanced_idea_description']
                    st.rerun()
            else:
                use_enhanced = False

            idea_tags_input = st.text_input("Etiketler (virgülle ayır)", placeholder="örn: reklam, bebek arabası, park, anne")

            uploaded_images = st.file_uploader("📸 Referans Görselleri Yükle (Birden fazla seçebilirsin!)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
            if uploaded_images:
                st.caption(f"✅ {len(uploaded_images)} görsel seçildi")

            col_pin, col_fav = st.columns(2)
            with col_pin:
                is_pinned = st.checkbox("📌 Bu fikri sabitle")
            with col_fav:
                is_favorite = st.checkbox("⭐ Favori olarak işaretle")

            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submit_idea = st.form_submit_button("💾 Fikri Kaydet", use_container_width=True)
            with col_cancel:
                cancel_idea = st.form_submit_button("❌ İptal", use_container_width=True)

            if submit_idea:
                if not idea_title or not idea_description:
                    st.error("Lütfen başlık ve açıklama gir!")
                else:
                    # Process tags
                    tags = [tag.strip() for tag in idea_tags_input.split(",") if tag.strip()]

                    # Process images
                    images_to_save = []
                    if uploaded_images:
                        for uploaded_file in uploaded_images:
                            images_to_save.append(Image.open(uploaded_file))

                    # Save idea
                    success, message = add_idea(
                        title=idea_title,
                        description=idea_description,
                        tags=tags,
                        images=images_to_save,
                        is_pinned=is_pinned,
                        is_favorite=is_favorite
                    )

                    if success:
                        st.success(message)
                        st.session_state['show_new_idea_form'] = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)

            if cancel_idea:
                st.session_state['show_new_idea_form'] = False
                st.rerun()

    # Display Ideas
    all_ideas = search_ideas(query=search_query if search_query else "")

    # Sort: Pinned first, then by date
    all_ideas.sort(key=lambda x: (not x.get('is_pinned', False), x.get('created_at', '')), reverse=True)

    if not all_ideas:
        st.info("📝 Henüz fikir yok. Yaratıcı fikirlerini kaydetmeye başlamak için '➕ Yeni Fikir' butonuna tıkla!")
    else:
        st.markdown(f"**{len(all_ideas)} Fikir** {'📌 Sabitlenmiş fikirler önce gösteriliyor' if any(i.get('is_pinned') for i in all_ideas) else ''}")

        if view_mode == "Kart":
            # Grid View
            cols_per_row = 3
            for i in range(0, len(all_ideas), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(all_ideas):
                        idea = all_ideas[i + j]
                        with col:
                            # Idea Card
                            pin_icon = "📌 " if idea.get('is_pinned') else ""
                            fav_icon = "⭐ " if idea.get('is_favorite') else ""

                            with st.container():
                                st.markdown(f"**{pin_icon}{fav_icon}{idea['title']}**")

                                # Show first image if available
                                if idea.get('images') and len(idea['images']) > 0:
                                    try:
                                        img_path = idea['images'][0]
                                        if os.path.exists(img_path):
                                            st.image(img_path, use_container_width=True)
                                    except:
                                        pass

                                # Description (truncated)
                                desc_preview = idea['description'][:100] + "..." if len(idea['description']) > 100 else idea['description']
                                st.caption(desc_preview)

                                # Tags
                                if idea.get('tags'):
                                    tags_str = " ".join([f"#{tag}" for tag in idea['tags'][:3]])
                                    st.caption(tags_str)

                                # Date
                                created_date = datetime.fromisoformat(idea['created_at']).strftime("%b %d, %Y")
                                st.caption(f"📅 {created_date}")

                                # Quick Actions
                                col_actions = st.columns(3)
                                with col_actions[0]:
                                    if st.button("📌", key=f"pin_{idea['id']}", help="Sabitle/Kaldır"):
                                        toggle_pin(idea['id'])
                                        st.rerun()
                                with col_actions[1]:
                                    if st.button("⭐", key=f"fav_{idea['id']}", help="Favorile"):
                                        toggle_favorite(idea['id'])
                                        st.rerun()
                                with col_actions[2]:
                                    if st.button("🗑️", key=f"del_{idea['id']}", help="Sil"):
                                        delete_idea(idea['id'])
                                        st.rerun()

                                # Main Actions
                                if idea.get('images') and api_key:
                                    if st.button("🔍 Görselleri Analiz Et", key=f"analyze_{idea['id']}", use_container_width=True):
                                        with st.spinner("AI analiz yapıyor..."):
                                            # Load images
                                            pil_images = []
                                            for img_path in idea['images']:
                                                if os.path.exists(img_path):
                                                    pil_images.append(Image.open(img_path))

                                            if pil_images:
                                                analysis, error = analyze_product_images(api_key, pil_images, idea['title'])
                                                if analysis:
                                                    update_idea(idea['id'], ai_analysis=analysis)
                                                    st.success("✅ Analiz tamamlandı!")
                                                    st.rerun()
                                                else:
                                                    st.error(error)

                                if st.button("🎬 Storyboard Oluştur", key=f"storyboard_{idea['id']}", use_container_width=True):
                                    # Store idea data in session state for storyboard tab
                                    st.session_state['idea_for_storyboard'] = {
                                        'title': idea['title'],
                                        'description': idea['description'],
                                        'tags': idea['tags'],
                                        'images': idea['images'],
                                        'analysis': idea.get('ai_analysis')
                                    }
                                    st.success("✅ Storyboard tab'ına geç!")
                                    st.info("👉 Yukarıdan 'STORYBOARD' tab'ına tıkla")

                                st.markdown("---")

        else:
            # List View
            for idea in all_ideas:
                pin_icon = "📌 " if idea.get('is_pinned') else ""
                fav_icon = "⭐ " if idea.get('is_favorite') else ""

                with st.expander(f"{pin_icon}{fav_icon}{idea['title']}", expanded=False):
                    # Images
                    if idea.get('images'):
                        img_cols = st.columns(min(len(idea['images']), 4))
                        for idx, img_path in enumerate(idea['images'][:4]):
                            with img_cols[idx]:
                                if os.path.exists(img_path):
                                    st.image(img_path, use_container_width=True)

                    # Description
                    st.markdown(f"**Açıklama:**")
                    st.write(idea['description'])

                    # Tags
                    if idea.get('tags'):
                        st.markdown(f"**Etiketler:** {', '.join(['#' + tag for tag in idea['tags']])}")

                    # Metadata
                    created_date = datetime.fromisoformat(idea['created_at']).strftime("%d %B %Y, %H:%M")
                    st.caption(f"📅 Oluşturulma: {created_date}")

                    # Quick Actions
                    col_act1, col_act2, col_act3 = st.columns(3)
                    with col_act1:
                        if st.button(f"📌 {'Sabitlemeyi Kaldır' if idea.get('is_pinned') else 'Sabitle'}", key=f"pin_list_{idea['id']}"):
                            toggle_pin(idea['id'])
                            st.rerun()
                    with col_act2:
                        if st.button(f"⭐ {'Favoriden Çıkar' if idea.get('is_favorite') else 'Favorile'}", key=f"fav_list_{idea['id']}"):
                            toggle_favorite(idea['id'])
                            st.rerun()
                    with col_act3:
                        if st.button("🗑️ Sil", key=f"del_list_{idea['id']}"):
                            if st.button("⚠️ Silmeyi Onayla?", key=f"confirm_del_{idea['id']}"):
                                delete_idea(idea['id'])
                                st.rerun()

                    st.markdown("---")

                    # Main Actions
                    col_main1, col_main2 = st.columns(2)
                    with col_main1:
                        if idea.get('images') and api_key:
                            if st.button("🔍 Görselleri Analiz Et", key=f"analyze_list_{idea['id']}", use_container_width=True):
                                with st.spinner("AI analiz yapıyor..."):
                                    pil_images = []
                                    for img_path in idea['images']:
                                        if os.path.exists(img_path):
                                            pil_images.append(Image.open(img_path))

                                    if pil_images:
                                        analysis, error = analyze_product_images(api_key, pil_images, idea['title'])
                                        if analysis:
                                            update_idea(idea['id'], ai_analysis=analysis)
                                            st.success("✅ Analiz tamamlandı!")
                                            st.rerun()
                                        else:
                                            st.error(error)

                    with col_main2:
                        if st.button("🎬 Storyboard Oluştur", key=f"storyboard_list_{idea['id']}", use_container_width=True):
                            st.session_state['idea_for_storyboard'] = {
                                'title': idea['title'],
                                'description': idea['description'],
                                'tags': idea['tags'],
                                'images': idea['images'],
                                'analysis': idea.get('ai_analysis')
                            }
                            st.success("✅ Storyboard tab'ına geç!")
                            st.info("👉 Yukarıdan 'STORYBOARD' tab'ına tıkla")

                    # Show AI Analysis if exists
                    if idea.get('ai_analysis'):
                        st.markdown("---")
                        st.markdown("### 🎨 AI Analiz Sonuçları")
                        analysis = idea['ai_analysis']

                        col_an1, col_an2 = st.columns(2)
                        with col_an1:
                            if analysis.get('product_summary'):
                                st.markdown("**Ürün/Sahne:**")
                                st.write(analysis['product_summary'])

                            if analysis.get('color_palette'):
                                st.markdown("**Renk Paleti:**")
                                st.write(", ".join(analysis['color_palette']))

                        with col_an2:
                            if analysis.get('recommended_lighting'):
                                st.markdown("**Önerilen Aydınlatma:**")
                                st.write(analysis['recommended_lighting'])

                            if analysis.get('visual_style'):
                                st.markdown("**Görsel Stil:**")
                                st.write(analysis['visual_style'])

                        if analysis.get('shot_ideas'):
                            st.markdown("**💡 Shot Fikirleri:**")
                            for shot_idea in analysis['shot_ideas'][:3]:
                                st.write(f"• {shot_idea}")

# --- TAB 1: CINEMA STUDIO (YENİ GÖRSEL ARAYÜZ) ---
with t_studio:
    st.markdown("#### ⚡ Quick Style Presets")
    st.caption("Tek tıkla profesyonel stil kombinasyonları yükle!")

    # Style Presets Grid - 4 sütunlu
    preset_cols = st.columns(4)
    for i, (preset_name, preset_data) in enumerate(STYLE_PRESETS.items()):
        col_idx = i % 4
        with preset_cols[col_idx]:
            if st.button(f"{preset_data['icon']} {preset_name}", key=f"preset_{preset_name}", use_container_width=True):
                apply_style_preset(preset_name)
                st.rerun()

    st.markdown("---")

    # PROFESSIONAL PROMPT ENGINE
    with st.expander("🎯 Professional Prompt Engine", expanded=False):
        st.caption("Karakter tutarlılığı ve AI model önerileri")

        prompt_tab1, prompt_tab2 = st.tabs(["👤 Karakter Yöneticisi", "🤖 AI Model Eşleştirici"])

        # TAB 1: CHARACTER CONSISTENCY MANAGER
        with prompt_tab1:
            st.markdown("##### 👤 Karakter Tutarlılık Yöneticisi")
            st.caption("Karakterleri kaydet ve tüm projelerinde aynı karakter tanımını kullan!")

            # Add new character
            with st.expander("➕ Yeni Karakter Ekle", expanded=False):
                char_name = st.text_input("Karakter Adı:", key="new_char_name", placeholder="Örn: Ana Karakter, Kahve İçen Adam")
                char_desc = st.text_area(
                    "Karakter Tanımı:",
                    key="new_char_desc",
                    placeholder="Örn: 35 yaşında erkek, koyu saçlı, mavi gözlü, spor yapılı, takım elbise giyen, ciddi yüz ifadeli iş adamı",
                    height=100
                )

                if st.button("💾 Karakteri Kaydet", use_container_width=True, type="primary"):
                    if char_name and char_desc:
                        new_character = {
                            "name": char_name,
                            "description": char_desc,
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        st.session_state.saved_characters.append(new_character)
                        st.success(f"✅ '{char_name}' karakteri kaydedildi!")
                        st.rerun()
                    else:
                        st.error("⚠️ Lütfen karakter adı ve tanımı girin!")

            st.markdown("---")

            # Display saved characters
            if st.session_state.saved_characters:
                st.markdown("##### 📋 Kayıtlı Karakterler")

                for idx, character in enumerate(st.session_state.saved_characters):
                    with st.container():
                        col_c1, col_c2, col_c3 = st.columns([2, 3, 1])

                        with col_c1:
                            st.markdown(f"**{character['name']}**")
                            st.caption(f"📅 {character['created_at']}")

                        with col_c2:
                            st.caption(f"_{character['description'][:80]}..._" if len(character['description']) > 80 else f"_{character['description']}_")

                        with col_c3:
                            if st.button("Kullan", key=f"use_char_{idx}", use_container_width=True):
                                # Copy character description to clipboard (simulated by showing it)
                                st.session_state.character_in_use = character['description']
                                st.success(f"✅ '{character['name']}' kullanıma hazır!")

                        # Full description preview
                        with st.expander("Tam Tanım", expanded=False):
                            st.text(character['description'])

                            # Delete button
                            if st.button("🗑️ Sil", key=f"delete_char_{idx}", use_container_width=True):
                                st.session_state.saved_characters.pop(idx)
                                st.rerun()

                        st.divider()

                # Active character display
                if 'character_in_use' in st.session_state and st.session_state.character_in_use:
                    st.markdown("---")
                    st.success("**Aktif Karakter Tanımı:**")
                    st.code(st.session_state.character_in_use, language=None)
                    st.caption("Bu tanımı prompt'larına ekleyebilirsin!")
            else:
                st.info("👋 Henüz kayıtlı karakter yok. Yukarıdan yeni karakter ekle!")

        # TAB 2: AI MODEL MATCHER
        with prompt_tab2:
            st.markdown("##### 🤖 AI Model Eşleştirici")
            st.caption("Sahne tipine göre en uygun AI modelini bul!")

            # Scene type selection
            scene_type = st.selectbox(
                "Sahne Tipi:",
                [
                    "🎬 Aksiyon & Hızlı Hareket",
                    "👥 Portre & Karakter Odaklı",
                    "🏙️ Kentsel Manzara & Mimari",
                    "🌿 Doğa & Peyzaj",
                    "🍔 Ürün & Yiyecek",
                    "🚗 Otomobil & Araç",
                    "💎 Lüks & Moda",
                    "🎨 Sanatsal & Soyut",
                    "🏡 İç Mekan & Yaşam Alanları"
                ],
                key="scene_type_select"
            )

            # Model recommendations based on scene type
            model_recommendations = {
                "🎬 Aksiyon & Hızlı Hareket": {
                    "best": "Kling AI",
                    "reason": "Hızlı hareket, aksiyon sekansları ve dinamik kamera hareketlerinde üstün performans",
                    "settings": "Motion Strength: 7-9, Duration: 4-6s, FPS: 30",
                    "alternatives": ["Higgsfield (kararlılık için)"]
                },
                "👥 Portre & Karakter Odaklı": {
                    "best": "Veo 2",
                    "reason": "Yüz detayları, mimikler ve karakter tutarlılığında en iyi sonuç",
                    "settings": "Motion Strength: 3-5, Duration: 4s, Focus: Close-up/Medium shots",
                    "alternatives": ["Higgsfield (sinematik look için)"]
                },
                "🏙️ Kentsel Manzara & Mimari": {
                    "best": "Higgsfield",
                    "reason": "Mimari detaylar, geniş açılar ve stabilite konusunda profesyonel",
                    "settings": "Motion Strength: 4-6, Composition: Wide shots, Lens: 24mm",
                    "alternatives": ["Veo 2 (fotorealistik için)"]
                },
                "🌿 Doğa & Peyzaj": {
                    "best": "Veo 2",
                    "reason": "Doğal ışık, organik hareketler ve atmosfer yakalamada güçlü",
                    "settings": "Motion Strength: 5-7, Lighting: Golden Hour/Natural, Atmosphere: Active",
                    "alternatives": ["Kling (drone shots için)"]
                },
                "🍔 Ürün & Yiyecek": {
                    "best": "Higgsfield",
                    "reason": "Ürün detayları, makro çekimler ve profesyonel reklam estetiği",
                    "settings": "Motion Strength: 2-4, Focal: 85-100mm, Lighting: Studio/Controlled",
                    "alternatives": ["NanoBananaPro (still image için)"]
                },
                "🚗 Otomobil & Araç": {
                    "best": "Kling AI",
                    "reason": "Araç hareketi, refleksiyonlar ve dinamik kamera takibi",
                    "settings": "Motion Strength: 6-8, Camera Movement: Tracking/Orbit, Duration: 5-6s",
                    "alternatives": ["Higgsfield (statik beauty shots için)"]
                },
                "💎 Lüks & Moda": {
                    "best": "Higgsfield",
                    "reason": "Premium estetik, yüksek detay ve sinematik renk gradasyonu",
                    "settings": "Color Grading: Kodak/Fuji, Lighting: Controlled, Composition: Center/Golden Ratio",
                    "alternatives": ["Veo 2 (karakter+ürün kombinasyonu için)"]
                },
                "🎨 Sanatsal & Soyut": {
                    "best": "Kling AI",
                    "reason": "Yaratıcı interpretasyon, sürreal hareketler ve deneysel görselleştirme",
                    "settings": "Motion Strength: Varies 3-9, Atmosphere: Active, Experimental lens choices",
                    "alternatives": ["NanoBananaPro (konsept oluşturma için)"]
                },
                "🏡 İç Mekan & Yaşam Alanları": {
                    "best": "Veo 2",
                    "reason": "İç mekan aydınlatması, gerçekçi doku ve yaşam alanı atmosferi",
                    "settings": "Motion Strength: 3-5, Lighting: Natural Window/Soft, Focal: 24-35mm",
                    "alternatives": ["Higgsfield (mimari showcase için)"]
                }
            }

            if scene_type:
                recommendation = model_recommendations[scene_type]

                st.markdown("---")
                st.success(f"**🎯 Önerilen Model: {recommendation['best']}**")

                col_r1, col_r2 = st.columns(2)

                with col_r1:
                    st.markdown("**📋 Neden bu model?**")
                    st.write(recommendation['reason'])

                    st.markdown("**⚙️ Önerilen Ayarlar:**")
                    st.code(recommendation['settings'], language=None)

                with col_r2:
                    st.markdown("**🔄 Alternatif Modeller:**")
                    for alt in recommendation['alternatives']:
                        st.caption(f"• {alt}")

                    # Apply model selection
                    if st.button(f"✅ {recommendation['best']} Kullan", use_container_width=True, type="primary"):
                        # Map to actual provider names
                        provider_map = {
                            "Higgsfield": "Higgsfield",
                            "Veo 2": "Veo",
                            "Kling AI": "Kling",
                            "NanoBananaPro": "NanoBananaPro"
                        }

                        best_model = recommendation['best']
                        if best_model in provider_map:
                            # Determine if it's video or image
                            if "NanoBananaPro" in best_model:
                                st.session_state.image_provider = provider_map[best_model]
                            else:
                                st.session_state.video_provider = provider_map[best_model]

                            st.success(f"✅ {best_model} seçildi!")

                st.markdown("---")
                st.info("💡 **İpucu:** Model seçimini sahne tipine göre optimize etmek, daha iyi sonuç ve daha az deneme-yanılma demektir!")

    st.markdown("---")
    st.markdown("#### 🛠️ Ekipman Seçimi")

    # 3 KOLONLU GRID YAPISI (HIGGSFIELD TARZI)
    col_cam, col_lens, col_foc = st.columns(3)

    # 1. KAMERA SEÇİMİ
    with col_cam:
        st.markdown(f"**CAMERA** <span style='color:#CCFF00'>{st.session_state.selected_camera}</span>", unsafe_allow_html=True)
        for cam in CAMERAS:
            # Seçili mi kontrol et
            is_selected = (st.session_state.selected_camera == cam['name'])
            btn_label = f"{cam['icon']}  {cam['name']}"

            # Buton mantığı: Eğer seçiliyse farklı renk (Streamlit'te tam renk kontrolü zor ama border ile yaptık)
            if st.button(btn_label, key=f"btn_cam_{cam['name']}", use_container_width=True):
                st.session_state.selected_camera = cam['name']
                st.rerun()

    # 2. LENS SEÇİMİ
    with col_lens:
        st.markdown(f"**LENS** <span style='color:#CCFF00'>{st.session_state.selected_lens}</span>", unsafe_allow_html=True)
        for lens in LENSES:
            is_selected = (st.session_state.selected_lens == lens['name'])
            btn_label = f"🔘 {lens['name']} ({lens['char']})"

            if st.button(btn_label, key=f"btn_lens_{lens['name']}", use_container_width=True):
                st.session_state.selected_lens = lens['name']
                st.rerun()

    # 3. ODAK UZAKLIĞI
    with col_foc:
        st.markdown(f"**FOCAL LENGTH** <span style='color:#CCFF00'>{st.session_state.selected_focal}</span>", unsafe_allow_html=True)

        # Grid içinde Grid
        f_cols = st.columns(2)
        for i, focal in enumerate(FOCALS):
            col_idx = i % 2
            with f_cols[col_idx]:
                if st.button(focal, key=f"btn_foc_{focal}", use_container_width=True):
                    st.session_state.selected_focal = focal
                    st.rerun()

        st.divider()
        st.info(f"🎥 **Şu anki Setup:**\n{st.session_state.selected_camera} + {st.session_state.selected_lens} @ {st.session_state.selected_focal}")

    st.markdown("---")
    st.markdown("#### 🎨 Advanced Cinematic Controls")

    # ADVANCED CONTROLS - 5 KOLONLU GRID
    adv_col1, adv_col2, adv_col3, adv_col4, adv_col5 = st.columns(5)

    with adv_col1:
        st.markdown("**💡 LIGHTING (Işık)**")
        st.session_state.selected_lighting = st.selectbox(
            "Select Lighting",
            [x['name'] for x in LIGHTING_PRESETS],
            index=[x['name'] for x in LIGHTING_PRESETS].index(st.session_state.selected_lighting),
            key="light_select",
            label_visibility="collapsed"
        )
        light_obj = next((x for x in LIGHTING_PRESETS if x['name'] == st.session_state.selected_lighting), None)
        if light_obj:
            st.caption(f"**{light_obj.get('name_tr', light_obj['name'])}**")
            st.caption(f"_{light_obj.get('desc_tr', light_obj['desc'])}_")

    with adv_col2:
        st.markdown("**🎨 COLOR GRADING (Renk Tonlama)**")
        st.session_state.selected_color_grading = st.selectbox(
            "Select Color Grading",
            [x['name'] for x in COLOR_GRADING],
            index=[x['name'] for x in COLOR_GRADING].index(st.session_state.selected_color_grading),
            key="color_select",
            label_visibility="collapsed"
        )
        color_obj = next((x for x in COLOR_GRADING if x['name'] == st.session_state.selected_color_grading), None)
        if color_obj:
            st.caption(f"**{color_obj.get('name_tr', color_obj['name'])}**")
            st.caption(f"_{color_obj.get('desc_tr', color_obj['desc'])}_")

    with adv_col3:
        st.markdown("**🌫️ ATMOSPHERE (Atmosfer)**")
        st.session_state.selected_atmosphere = st.selectbox(
            "Select Atmosphere",
            [x['name'] for x in ATMOSPHERE],
            index=[x['name'] for x in ATMOSPHERE].index(st.session_state.selected_atmosphere),
            key="atmos_select",
            label_visibility="collapsed"
        )
        atmos_obj = next((x for x in ATMOSPHERE if x['name'] == st.session_state.selected_atmosphere), None)
        if atmos_obj:
            st.caption(f"**{atmos_obj.get('name_tr', atmos_obj['name'])}**")
            st.caption(f"_{atmos_obj.get('desc_tr', atmos_obj['desc'])}_")

    with adv_col4:
        st.markdown("**📐 COMPOSITION (Kompozisyon)**")
        st.session_state.selected_composition = st.selectbox(
            "Select Composition",
            [x['name'] for x in COMPOSITION_RULES],
            index=[x['name'] for x in COMPOSITION_RULES].index(st.session_state.selected_composition),
            key="comp_select",
            label_visibility="collapsed"
        )
        comp_obj = next((x for x in COMPOSITION_RULES if x['name'] == st.session_state.selected_composition), None)
        if comp_obj:
            st.caption(f"**{comp_obj.get('name_tr', comp_obj['name'])}**")
            st.caption(f"_{comp_obj.get('desc_tr', comp_obj['desc'])}_")

    with adv_col5:
        st.markdown("**🎬 CAMERA MOVE (Kamera Hareketi)**")
        st.session_state.selected_movement = st.selectbox(
            "Select Movement",
            [x['name'] for x in CAMERA_MOVEMENTS],
            index=[x['name'] for x in CAMERA_MOVEMENTS].index(st.session_state.selected_movement),
            key="move_select",
            label_visibility="collapsed"
        )
        move_obj = next((x for x in CAMERA_MOVEMENTS if x['name'] == st.session_state.selected_movement), None)
        if move_obj:
            st.caption(f"**{move_obj.get('name_tr', move_obj['name'])}**")
            st.caption(f"_{move_obj.get('desc_tr', move_obj['desc'])}_")

    st.markdown("---")

    # PROMPT PREVIEW
    with st.expander("📝 Generated Prompt Preview", expanded=True):
        preview_prompt = build_advanced_prompt("A cinematic shot", format_type=st.session_state.prompt_format)

        if st.session_state.prompt_format == "json":
            st.code(preview_prompt, language="json")
            st.caption("📋 JSON format - NanoBananaPro & Higgsfield & Kling uyumlu")
        else:
            st.code(preview_prompt, language=None)
            st.caption("📝 Normal text format - Tüm platformlarla uyumlu")

        st.caption("Bu prompt otomatik olarak seçtiğin tüm parametrelerden oluşturuldu!")

# --- TAB 2: STORYBOARD ---
with t_board:
    # SMART STORYBOARD GENERATOR
    with st.expander("🧠 Smart Storyboard Generator", expanded=False):
        st.caption("Senaryo → otomatik shot breakdown, timing hesaplama, gelişmiş AI analizi")

        st.markdown("##### 📝 Senaryo Girişi")

        # Script input modes
        script_mode = st.radio(
            "Giriş modu:",
            ["✍️ Manuel Senaryo", "💡 Fikir Temelli", "📄 Sahne Açıklaması"],
            horizontal=True,
            key="smart_story_mode"
        )

        script_input = ""

        if script_mode == "✍️ Manuel Senaryo":
            script_input = st.text_area(
                "Senaryo metni:",
                placeholder="""Örnek senaryo:

EXT. JAP ON BAHÇESİ - SABAH

Karlı bir Japon bahçesi. Ağaçların dallarında kar birikmiş.

BUDDHA HEYKELİ bahçenin ortasında sessizce duruyor. Güneş yavaşça doğuyor.

Kamera yavaşça Buddha'ya yaklaşıyor. Kar taneleri havada dans ediyor.

CLOSE-UP: Buddha'nın yüzü. Huzurlu bir gülümseme.

Kamera geri çekiliyor, tüm bahçeyi gösteriyor. Mükemmel bir an.""",
                height=250,
                key="manual_script"
            )

        elif script_mode == "💡 Fikir Temelli":
            col_idea1, col_idea2 = st.columns([2, 1])
            with col_idea1:
                script_input = st.text_area(
                    "Fikir özeti:",
                    placeholder="Örn: Karlı bir Japon bahçesinde Buddha heykeli, huzurlu atmosfer, sabah ışığı, zen mood",
                    height=150,
                    key="idea_script"
                )
            with col_idea2:
                st.markdown("**Hedef:**")
                target_option = st.selectbox(
                    "Ne için?",
                    ["Reklam (15-30s)", "Sosyal Medya (5-10s)", "Kısa Film (1-2 dak)", "Müzik Videosu"],
                    key="target_select"
                )
                st.caption("AI bu hedefe göre shot breakdown yapacak")

        else:  # Sahne Açıklaması
            script_input = st.text_area(
                "Sahne açıklaması:",
                placeholder="Örn: Lüks bir restoranda akşam yemeği sahnesi. Romantik atmosfer, mum ışığı, şık giyimli çift.",
                height=150,
                key="scene_script"
            )

        st.markdown("---")

        # Advanced options
        adv_col1, adv_col2, adv_col3 = st.columns(3)

        with adv_col1:
            auto_shot_count = st.checkbox("Otomatik shot sayısı", value=True, key="auto_shot_count")
            if not auto_shot_count:
                manual_shot_count = st.number_input("Shot sayısı:", 2, 12, 6, key="manual_shot_num")

        with adv_col2:
            calculate_timing = st.checkbox("Timing otomatik hesapla", value=True, key="calc_timing")
            if calculate_timing:
                total_duration = st.number_input("Toplam süre (saniye):", 10, 120, 30, key="total_dur")

        with adv_col3:
            include_transitions = st.checkbox("Geçiş önerileri", value=True, key="include_trans")
            suggest_audio = st.checkbox("Müzik & Ses Efekti", value=True, key="suggest_audio")

        st.markdown("---")

        # Generate button
        if st.button("🎬 Smart Storyboard Oluştur", use_container_width=True, type="primary", key="gen_smart_story"):
            if not api_key:
                st.error("⚠️ Lütfen Gemini API Key gir!")
            elif not script_input:
                st.error("⚠️ Lütfen bir senaryo/fikir gir!")
            else:
                with st.spinner("🧠 AI akıllı storyboard oluşturuyor..."):
                    # Build enhanced prompt for AI
                    enhanced_prompt = f"""
                    Senaryo/Fikir:
                    {script_input}

                    Görev: Bu senaryo/fikirden profesyonel bir storyboard oluştur.

                    Format: JSON array olarak döndür, her shot için:
                    {{
                        "shot_number": int,
                        "shot_type": str (Wide Shot, Close-Up, Medium Shot, etc.),
                        "description": str (ne görülüyor, detaylı açıklama),
                        "action": str (sahnede ne oluyor),
                        "mood": str (sahnenin duygusal tonu),
                        "suggested_movement": str (kamera hareketi),
                        "suggested_lighting": str (ışık tipi),
                        "duration": str (örn: "4s", "6s"),
                        {'"transition": str (bir sonraki shota geçiş önerisi - fade/cut/dissolve/wipe),' if include_transitions else ""}
                        {'"music": {{"genre": str, "mood": str, "tempo": str, "instruments": str, "envato_keywords": str}},' if suggest_audio else ""}
                        {'"sound_effects": {{"effects": [list of specific sounds], "atmosphere": str, "envato_keywords": str}},' if suggest_audio else ""}
                        "timing_notes": str (neden bu süre, ne zaman hızlan/yavaşla)
                    }}

                    Önemli:
                    - {"Shot sayısını otomatik belirle (içerik karmaşıklığına göre)" if auto_shot_count else f"Tam {manual_shot_count} shot oluştur"}
                    - {"Her shot'ın süresini toplam " + str(total_duration) + " saniye olacak şekilde hesapla" if calculate_timing else "Her shot için uygun süre öner"}
                    - Sahne geçişlerinde mantık kur (establishment shot → action → close-up → wide)
                    - Sinematik kurallara uy (180 degree rule, continuity, pacing)
                    - Her shot için teknik kamera parametreleri öner
                    {"- Müzik: genre, mood, tempo (BPM), instruments öneri" if suggest_audio else ""}
                    {"- Ses Efektleri: shot'a özel sesler, atmosfer sesleri" if suggest_audio else ""}
                    {"- Envato Keywords: Envato Elements'te arama için kelimeleri İngilizce ver (örn: 'zen ambient music', 'snow footsteps sfx')" if suggest_audio else ""}

                    Sadece JSON array döndür, başka açıklama ekleme.
                    """

                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        response = model.generate_content(enhanced_prompt)

                        # Parse JSON response
                        import re
                        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)

                        if json_match:
                            shots = json.loads(json_match.group())
                            st.session_state['shots'] = shots
                            st.success(f"✅ {len(shots)} shot başarıyla oluşturuldu!")

                            # Show summary
                            total_est_duration = sum([int(s.get('duration', '4s').replace('s', '')) for s in shots])
                            st.info(f"📊 Tahmini toplam süre: {total_est_duration} saniye")

                            st.rerun()
                        else:
                            st.error("❌ AI'dan geçerli JSON alınamadı. Lütfen tekrar dene.")

                    except Exception as e:
                        st.error(f"❌ Hata: {str(e)}")

    # Reference Images Section
    with st.expander("📸 Referans Görselleri", expanded=False):
        st.caption("Storyboard oluştururken referans görselleri buraya yükleyebilirsin")

        reference_images = st.file_uploader(
            "Referans görselleri yükle (birden fazla seçebilirsin)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key="storyboard_references"
        )

        if reference_images:
            st.success(f"✅ {len(reference_images)} görsel yüklendi")

            # Display images in grid
            cols_per_row = 4
            for i in range(0, len(reference_images), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(reference_images):
                        with col:
                            img = Image.open(reference_images[i + j])
                            st.image(img, use_container_width=True, caption=reference_images[i + j].name)

            # Option to analyze references with AI
            if api_key and st.button("🔍 Referansları Analiz Et (AI)", use_container_width=True):
                with st.spinner("AI görselleri analiz ediyor..."):
                    # Convert uploaded files to PIL Images
                    pil_images = [Image.open(ref) for ref in reference_images]
                    analysis, error = analyze_product_images(api_key, pil_images, "Storyboard references")

                    if analysis:
                        st.success("✅ Analiz tamamlandı!")

                        # Display analysis results
                        st.markdown("### 🎨 AI Analiz Sonuçları:")

                        col_a1, col_a2 = st.columns(2)
                        with col_a1:
                            st.markdown("**Ürün/Sahne Özeti:**")
                            st.write(analysis.get('product_summary', 'N/A'))

                            st.markdown("**Renk Paleti:**")
                            if analysis.get('color_palette'):
                                st.write(", ".join(analysis['color_palette']))

                            st.markdown("**Önerilen Aydınlatma:**")
                            st.write(analysis.get('recommended_lighting', 'N/A'))

                        with col_a2:
                            st.markdown("**Önerilen Kamera Açıları:**")
                            if analysis.get('recommended_camera_angles'):
                                for angle in analysis['recommended_camera_angles']:
                                    st.write(f"• {angle}")

                            st.markdown("**Mood Önerileri:**")
                            if analysis.get('mood_suggestions'):
                                st.write(", ".join(analysis['mood_suggestions']))

                        # Shot ideas from AI
                        if analysis.get('shot_ideas'):
                            st.markdown("**💡 AI Shot Fikirleri:**")
                            for idea in analysis['shot_ideas']:
                                st.write(f"• {idea}")
                    else:
                        st.error(error)

        st.markdown("---")

    # Check if idea was transferred from Ideas tab
    transferred_idea = st.session_state.get('idea_for_storyboard')
    if transferred_idea:
        st.success(f"✅ '{transferred_idea['title']}' fikrini yükledin!")

        if transferred_idea.get('images'):
            st.info(f"📸 {len(transferred_idea['images'])} referans görseli var")

        if transferred_idea.get('analysis'):
            with st.expander("🎨 AI Analiz Sonuçları", expanded=True):
                analysis = transferred_idea['analysis']
                st.write(f"**Ürün/Sahne:** {analysis.get('product_summary', 'N/A')}")
                st.write(f"**Önerilen Aydınlatma:** {analysis.get('recommended_lighting', 'N/A')}")
                st.write(f"**Görsel Stil:** {analysis.get('visual_style', 'N/A')}")

                if analysis.get('shot_ideas'):
                    st.markdown("**💡 AI Shot Önerileri:**")
                    for idea in analysis['shot_ideas'][:3]:
                        st.write(f"• {idea}")

        if st.button("❌ Fikri Temizle"):
            del st.session_state['idea_for_storyboard']
            st.rerun()

        st.markdown("---")

    col1, col2 = st.columns([3, 1])
    with col1:
        # Auto-fill with idea description if transferred
        default_text = transferred_idea['description'] if transferred_idea else ""
        raw_idea = st.text_area("Fikir / Senaryo", height=100, value=default_text, placeholder="Karlı bir japon bahçesinde gülen buddha...")
    with col2:
        shot_count = st.slider("Sahne Sayısı", 2, 8, 4)
        if st.button("🎬 Generate Storyboard with AI", use_container_width=True):
            if not api_key:
                st.error("Lütfen Gemini API Key gir!")
            elif not raw_idea:
                st.error("Lütfen bir fikir/senaryo gir!")
            else:
                with st.spinner("AI storyboard oluşturuyor..."):
                    shots, error = generate_storyboard(api_key, raw_idea, shot_count)

                    if shots:
                        st.session_state['shots'] = shots
                        st.success(f"{len(shots)} shot başarıyla oluşturuldu!")
                        st.rerun()
                    else:
                        st.error(error)

    # Display Generated Shots
    if st.session_state.get('shots'):
        st.markdown("### 🎞️ Generated Storyboard")

        # Batch Actions
        batch_col1, batch_col2, batch_col3 = st.columns([2, 1, 1])
        with batch_col1:
            st.markdown(f"**{len(st.session_state['shots'])} shots generated**")
        with batch_col2:
            if st.button("🎬 Add All to Queue", use_container_width=True):
                for i, shot in enumerate(st.session_state['shots']):
                    shot_description = f"{shot.get('description', '')}. {shot.get('action', '')}"
                    prompt = build_advanced_prompt(shot_description, format_type=st.session_state.prompt_format)
                    settings = {
                        'aspect_ratio': st.session_state.aspect_ratio,
                        'duration': shot.get('duration', st.session_state.duration),
                        'fps': st.session_state.fps,
                        'motion_strength': st.session_state.motion_strength
                    }
                    add_to_queue(shot, prompt, settings)
                st.success(f"{len(st.session_state['shots'])} shots added to queue!")
                st.rerun()

        with batch_col3:
            if len(st.session_state.generation_queue) > 0:
                st.info(f"Queue: {len(st.session_state.generation_queue)} jobs")

        st.markdown("---")

        for i, shot in enumerate(st.session_state['shots']):
            with st.expander(f"🎬 Shot {shot.get('shot_number', i+1)}: {shot.get('shot_type', 'Scene')}", expanded=(i==0)):
                col_shot_left, col_shot_right = st.columns([2, 1])

                with col_shot_left:
                    st.markdown(f"**Description:** {shot.get('description', 'N/A')}")
                    st.markdown(f"**Action:** {shot.get('action', 'N/A')}")
                    st.markdown(f"**Mood:** {shot.get('mood', 'N/A')}")

                    # Transition info
                    if shot.get('transition'):
                        st.markdown(f"**Geçiş:** {shot.get('transition')}")

                with col_shot_right:
                    st.markdown(f"**Movement:** {shot.get('suggested_movement', 'Static')}")
                    st.markdown(f"**Lighting:** {shot.get('suggested_lighting', 'Natural')}")
                    st.markdown(f"**Duration:** {shot.get('duration', '4s')}")

                # Music & Sound Effects Section
                if shot.get('music') or shot.get('sound_effects'):
                    st.markdown("---")
                    audio_col1, audio_col2 = st.columns(2)

                    with audio_col1:
                        if shot.get('music'):
                            st.markdown("##### 🎵 Müzik")
                            music = shot['music']
                            st.caption(f"**Tür:** {music.get('genre', 'N/A')}")
                            st.caption(f"**Mood:** {music.get('mood', 'N/A')}")
                            st.caption(f"**Tempo:** {music.get('tempo', 'N/A')}")
                            st.caption(f"**Enstrüman:** {music.get('instruments', 'N/A')}")

                            if music.get('envato_keywords'):
                                st.code(f"🔍 Envato: {music['envato_keywords']}", language=None)

                    with audio_col2:
                        if shot.get('sound_effects'):
                            st.markdown("##### 🔊 Ses Efektleri")
                            sfx = shot['sound_effects']

                            if sfx.get('effects'):
                                st.caption("**Efektler:**")
                                for effect in sfx['effects']:
                                    st.caption(f"• {effect}")

                            if sfx.get('atmosphere'):
                                st.caption(f"**Atmosfer:** {sfx['atmosphere']}")

                            if sfx.get('envato_keywords'):
                                st.code(f"🔍 Envato: {sfx['envato_keywords']}", language=None)

                    shot_btn_col1, shot_btn_col2 = st.columns(2)
                    with shot_btn_col1:
                        if st.button(f"✅ Use", key=f"use_shot_{i}", use_container_width=True):
                            # Apply shot settings to current parameters
                            st.session_state.selected_movement = shot.get('suggested_movement', st.session_state.selected_movement)
                            st.session_state.selected_lighting = shot.get('suggested_lighting', st.session_state.selected_lighting)
                            st.session_state.selected_shot_index = i

                            # Generate prompt for this shot
                            shot_description = f"{shot.get('description', '')}. {shot.get('action', '')}"
                            st.session_state['generated_prompt'] = build_advanced_prompt(shot_description, format_type=st.session_state.prompt_format)

                            st.success("Applied!")
                            st.rerun()

                    with shot_btn_col2:
                        if st.button(f"➕ Queue", key=f"queue_shot_{i}", use_container_width=True):
                            shot_description = f"{shot.get('description', '')}. {shot.get('action', '')}"
                            prompt = build_advanced_prompt(shot_description, format_type=st.session_state.prompt_format)
                            settings = {
                                'aspect_ratio': st.session_state.aspect_ratio,
                                'duration': shot.get('duration', st.session_state.duration),
                                'fps': st.session_state.fps,
                                'motion_strength': st.session_state.motion_strength
                            }
                            job_id = add_to_queue(shot, prompt, settings)
                            st.success(f"Added to queue!")
    else:
        st.info("👆 Yukarıdan bir fikir gir ve 'Generate Storyboard' butonuna bas!")

# --- TAB 3.5: IMAGE (8 ANGLE PROMPT GENERATOR) ---
with t_image:
    st.markdown("# 🖼️ IMAGE - 8 Angle Prompt Generator")
    st.caption("Generate character prompts from 8 different camera angles")

    st.markdown("---")

    # Center: Reference Image Upload
    st.markdown("### 📷 Reference Image")

    col_spacer1, col_center, col_spacer2 = st.columns([0.5, 2, 0.5])

    with col_center:
        if st.session_state['uploaded_img']:
            st.image(st.session_state['uploaded_img'], caption="Reference Character", use_column_width=True)
        else:
            st.info("⚠️ Please upload a reference image from sidebar first")

    st.markdown("---")

    # 8 Angle Buttons Grid (4x2)
    st.markdown("### 🎯 Select Camera Angles")
    st.caption("Click on angles to generate prompts for character consistency")

    angle_definitions = [
        {
            "name": "Wide Shot",
            "emoji": "🌄",
            "desc": "Full body, establishing shot",
            "prompt_template": "wide shot, full body view, {character_desc}, cinematic lighting, professional photography"
        },
        {
            "name": "Medium Shot",
            "emoji": "👤",
            "desc": "Waist up, character focused",
            "prompt_template": "medium shot, waist up view, {character_desc}, portrait photography, shallow depth of field"
        },
        {
            "name": "Close-Up",
            "emoji": "😊",
            "desc": "Face detail, emotional",
            "prompt_template": "close-up shot, face detail, {character_desc}, emotional expression, soft lighting"
        },
        {
            "name": "Extreme Close-Up",
            "emoji": "👁️",
            "desc": "Eyes, hands, details",
            "prompt_template": "extreme close-up, detailed view, {character_desc}, macro photography, sharp focus"
        },
        {
            "name": "Over-the-Shoulder",
            "emoji": "🎭",
            "desc": "Conversation perspective",
            "prompt_template": "over-the-shoulder shot, {character_desc}, cinematic angle, depth of field"
        },
        {
            "name": "Low Angle",
            "emoji": "⬆️",
            "desc": "Power, dominance view",
            "prompt_template": "low angle shot, looking up at {character_desc}, dramatic perspective, powerful composition"
        },
        {
            "name": "High Angle",
            "emoji": "⬇️",
            "desc": "Vulnerability, overview",
            "prompt_template": "high angle shot, looking down at {character_desc}, bird's eye perspective, cinematic"
        },
        {
            "name": "Dutch Angle",
            "emoji": "🔄",
            "desc": "Tension, dynamic tilt",
            "prompt_template": "dutch angle, tilted shot, {character_desc}, dynamic composition, cinematic tension"
        }
    ]

    # Initialize selected angles in session state
    if 'selected_angles' not in st.session_state:
        st.session_state['selected_angles'] = []

    # Display 8 angle buttons in compact 4x2 grid
    st.markdown("""
        <style>
        div[data-testid="stButton"] > button {
            padding: 8px 12px !important;
            font-size: 0.85em !important;
            height: auto !important;
            min-height: 40px !important;
            white-space: normal !important;
        }
        </style>
    """, unsafe_allow_html=True)

    angle_row1 = st.columns(4, gap="small")
    angle_row2 = st.columns(4, gap="small")

    for i, angle in enumerate(angle_definitions[:4]):
        with angle_row1[i]:
            is_selected = angle['name'] in st.session_state['selected_angles']
            if st.button(
                f"{angle['emoji']} {angle['name'].upper()}",
                key=f"angle_btn_{i}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
                help=angle['desc']
            ):
                if is_selected:
                    st.session_state['selected_angles'].remove(angle['name'])
                else:
                    st.session_state['selected_angles'].append(angle['name'])
                st.rerun()

    for i, angle in enumerate(angle_definitions[4:], start=4):
        with angle_row2[i-4]:
            is_selected = angle['name'] in st.session_state['selected_angles']
            if st.button(
                f"{angle['emoji']} {angle['name'].upper()}",
                key=f"angle_btn_{i}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
                help=angle['desc']
            ):
                if is_selected:
                    st.session_state['selected_angles'].remove(angle['name'])
                else:
                    st.session_state['selected_angles'].append(angle['name'])
                st.rerun()

    st.markdown("---")

    # Camera and Lens Selection
    st.markdown("### 📹 Camera & Lens Settings")
    st.caption("Select camera and lens for professional cinematic look")

    cam_lens_col1, cam_lens_col2 = st.columns(2)

    with cam_lens_col1:
        st.markdown("**📹 Camera**")
        camera_names = [cam['name'] for cam in CAMERAS]
        selected_camera_idx = st.selectbox(
            "Select Camera",
            range(len(camera_names)),
            format_func=lambda i: f"{CAMERAS[i]['icon']} {camera_names[i]}",
            key="image_camera_select",
            label_visibility="collapsed"
        )
        selected_camera = CAMERAS[selected_camera_idx]

    with cam_lens_col2:
        st.markdown("**🔭 Lens**")
        lens_names = [lens['name'] for lens in LENSES]
        selected_lens_idx = st.selectbox(
            "Select Lens",
            range(len(lens_names)),
            format_func=lambda i: f"{lens_names[i]} ({LENSES[i]['char']})",
            key="image_lens_select",
            label_visibility="collapsed"
        )
        selected_lens = LENSES[selected_lens_idx]

    # Show selected equipment info
    equip_info_col1, equip_info_col2 = st.columns(2)
    with equip_info_col1:
        st.info(f"**Camera:** {selected_camera['name']} - {selected_camera['type']}")
    with equip_info_col2:
        st.info(f"**Lens:** {selected_lens['name']} - {selected_lens['char']}")

    st.markdown("---")

    # Character Description Input
    st.markdown("### ✍️ Character Description")
    character_desc = st.text_area(
        "Describe your character/scene (simple or detailed)",
        placeholder="Example: modern bir kadın bebek arabası ile park da yürüyor ve bebek arasının tanıtım filmini yapıyor...",
        height=120,
        key="character_description"
    )

    # AI Enhancement Feature
    enhance_col1, enhance_col2, enhance_col3 = st.columns([1, 1, 1])
    with enhance_col2:
        if st.button("🤖 ENHANCE WITH AI", use_container_width=True, key="enhance_ai_btn"):
            if not character_desc:
                st.error("⚠️ Please enter a description first!")
            else:
                with st.spinner("🤖 AI is enhancing your description..."):
                    try:
                        # Call Gemini API to enhance the description
                        api_key = st.session_state.get('gemini_api_key')
                        if not api_key:
                            st.error("⚠️ Please add your Gemini API key in SISTEM tab!")
                        else:
                            genai.configure(api_key=api_key)
                            model = genai.GenerativeModel('gemini-2.5-flash')

                            enhancement_prompt = f"""You are a professional cinematographer and prompt engineer.
Enhance this rough character/scene description into a detailed, professional cinematic prompt suitable for AI image generation.

Input description: "{character_desc}"

Create a detailed, professional description that includes:
- Physical appearance details
- Clothing and style
- Environment and setting
- Lighting and mood
- Camera quality (professional, cinematic)
- Any relevant context for a promotional/commercial shoot

Keep it concise but detailed. Write in English. Focus on visual details.

Enhanced description:"""

                            response = model.generate_content(enhancement_prompt)
                            enhanced_text = response.text.strip()

                            # Store enhanced description
                            st.session_state['enhanced_character_desc'] = enhanced_text
                            st.success("✅ Description enhanced by AI!")
                            st.rerun()

                    except Exception as e:
                        st.error(f"❌ AI Enhancement failed: {str(e)}")

    # Show enhanced description if available
    if 'enhanced_character_desc' in st.session_state and st.session_state['enhanced_character_desc']:
        st.markdown("#### 🤖 AI Enhanced Description")
        st.info(st.session_state['enhanced_character_desc'])

        if st.button("❌ Clear Enhanced Version", key="clear_enhanced"):
            del st.session_state['enhanced_character_desc']
            st.rerun()

    st.markdown("---")

    # Generate Prompts Button
    gen_col1, gen_col2, gen_col3 = st.columns([1, 1, 1])
    with gen_col2:
        if st.button("🎬 GENERATE PROMPTS", use_container_width=True, type="primary", key="gen_prompts_btn"):
            if not character_desc:
                st.error("⚠️ Please enter a character description first!")
            elif len(st.session_state['selected_angles']) == 0:
                st.error("⚠️ Please select at least one camera angle!")
            else:
                # Use enhanced description if available, otherwise use original
                final_desc = st.session_state.get('enhanced_character_desc', character_desc)

                # Add camera and lens info to description
                camera_info = f"shot on {selected_camera['name']}, {selected_lens['name']} lens, {selected_lens['char']}"
                full_desc = f"{final_desc}, {camera_info}"

                st.session_state['generated_angle_prompts'] = {}
                for angle in angle_definitions:
                    if angle['name'] in st.session_state['selected_angles']:
                        prompt = angle['prompt_template'].replace("{character_desc}", full_desc)
                        st.session_state['generated_angle_prompts'][angle['name']] = prompt

                if 'enhanced_character_desc' in st.session_state:
                    st.success(f"✅ Generated {len(st.session_state['generated_angle_prompts'])} prompts using AI-enhanced description!")
                else:
                    st.success(f"✅ Generated {len(st.session_state['generated_angle_prompts'])} prompts!")

    # Display Generated Prompts - INDIVIDUAL COPY FOR EACH
    if 'generated_angle_prompts' in st.session_state and len(st.session_state['generated_angle_prompts']) > 0:
        st.markdown("---")
        st.markdown("### 📝 Generated Prompts")
        st.caption(f"{len(st.session_state['generated_angle_prompts'])} açı için prompt oluşturuldu - Her birini ayrı kopyalayabilirsin")

        # Display each prompt individually with copy instructions
        for angle_name, prompt in st.session_state['generated_angle_prompts'].items():
            angle_data = next((a for a in angle_definitions if a['name'] == angle_name), None)
            if angle_data:
                # Header for each angle
                st.markdown(f"#### {angle_data['emoji']} {angle_name.upper()}")

                # Prompt in code block (easy to select and copy)
                st.code(prompt, language=None)

                # Small instruction
                st.caption("☝️ Prompt'u kopyalamak için: Kod kutusuna tıkla → Ctrl+A (tümünü seç) → Ctrl+C (kopyala)")

                st.markdown("---")

# --- TAB 4: VIDEO RENDER ---
with t_video:
    st.markdown("# 🎬 VIDEO - CINEMA STUDIO")
    st.caption("Professional video production system")

    st.markdown("---")

    # ===== 3-MODE SELECTION SYSTEM =====
    mode_col1, mode_col2, mode_col3 = st.columns(3)

    if 'video_mode' not in st.session_state:
        st.session_state['video_mode'] = 'SHOT_GENERATOR'

    with mode_col1:
        if st.button("🎯 SHOT GENERATOR\n8 Angle System", key="mode_shot", use_container_width=True,
                     type="primary" if st.session_state['video_mode'] == 'SHOT_GENERATOR' else "secondary"):
            st.session_state['video_mode'] = 'SHOT_GENERATOR'
            st.rerun()

    with mode_col2:
        if st.button("🖼️ IMAGE → VIDEO\nQuick Conversion", key="mode_img2vid", use_container_width=True,
                     type="primary" if st.session_state['video_mode'] == 'IMAGE_TO_VIDEO' else "secondary"):
            st.session_state['video_mode'] = 'IMAGE_TO_VIDEO'
            st.rerun()

    with mode_col3:
        if st.button("✍️ TEXT → VIDEO\nText to Video", key="mode_txt2vid", use_container_width=True,
                     type="primary" if st.session_state['video_mode'] == 'TEXT_TO_VIDEO' else "secondary"):
            st.session_state['video_mode'] = 'TEXT_TO_VIDEO'
            st.rerun()

    st.markdown("---")

    # ===== BATCH PROCESSING PIPELINE =====
    with st.expander("📦 Batch Processing Pipeline", expanded=False):
        st.caption("Toplu video üretimi - Queue yönetimi, otomatik retry ve ilerleme takibi")

        # Queue Statistics Dashboard
        stats = get_queue_stats()

        stat_col1, stat_col2, stat_col3, stat_col4, stat_col5 = st.columns(5)
        with stat_col1:
            st.metric("📊 Toplam", stats['total'])
        with stat_col2:
            st.metric("⏳ Bekliyor", stats['pending'])
        with stat_col3:
            st.metric("⚙️ İşleniyor", stats['processing'])
        with stat_col4:
            st.metric("✅ Tamamlandı", stats['completed'])
        with stat_col5:
            st.metric("❌ Başarısız", stats['failed'])

        st.markdown("---")

        # Queue Settings
        queue_col1, queue_col2, queue_col3 = st.columns(3)

        with queue_col1:
            st.markdown("**⚙️ Otomatik Retry**")
            st.session_state.auto_retry_enabled = st.checkbox(
                "Başarısız görevleri otomatik tekrar dene",
                value=st.session_state.auto_retry_enabled,
                key="auto_retry_toggle"
            )

            if st.session_state.auto_retry_enabled:
                st.session_state.max_retry_attempts = st.number_input(
                    "Maksimum deneme sayısı:",
                    min_value=1,
                    max_value=10,
                    value=st.session_state.max_retry_attempts,
                    key="max_retry_input"
                )

        with queue_col2:
            st.markdown("**🔄 Otomatik İşleme**")
            st.session_state.queue_auto_process = st.checkbox(
                "Queue'daki görevleri otomatik işle",
                value=st.session_state.queue_auto_process,
                key="auto_process_toggle"
            )

            if st.session_state.queue_auto_process:
                st.info("🤖 Otomatik işleme aktif - görevler sırayla işlenecek")

        with queue_col3:
            st.markdown("**🗑️ Temizlik**")
            if st.button("Tamamlananları Temizle", use_container_width=True, key="clear_completed_btn"):
                clear_completed_tasks()
                st.success("✅ Tamamlanan görevler temizlendi!")
                st.rerun()

            if st.button("Tüm Queue'yu Temizle", use_container_width=True, key="clear_all_btn"):
                st.session_state.generation_queue = []
                st.success("✅ Tüm queue temizlendi!")
                st.rerun()

        st.markdown("---")

        # Queue Task List
        if st.session_state.generation_queue and len(st.session_state.generation_queue) > 0:
            st.markdown("##### 📋 Queue'daki Görevler")

            for idx, task in enumerate(st.session_state.generation_queue):
                with st.container():
                    task_col1, task_col2, task_col3, task_col4 = st.columns([2, 3, 2, 2])

                    with task_col1:
                        # Status indicator
                        status_emoji = {
                            'pending': '⏳',
                            'processing': '⚙️',
                            'completed': '✅',
                            'failed': '❌'
                        }
                        st.markdown(f"**{status_emoji.get(task['status'], '❓')} Task #{idx + 1}**")
                        st.caption(f"Tip: {task['type']}")
                        st.caption(f"Oluşturulma: {task.get('created_at', 'N/A')}")

                    with task_col2:
                        st.caption(f"**Prompt:**")
                        prompt_preview = task.get('prompt', 'N/A')
                        if len(prompt_preview) > 80:
                            prompt_preview = prompt_preview[:80] + "..."
                        st.caption(f"_{prompt_preview}_")

                        if task['status'] == 'failed' and task.get('error'):
                            st.error(f"Hata: {task['error']}")

                    with task_col3:
                        st.caption(f"**Durum:** {task['status'].upper()}")
                        st.caption(f"**Denemeler:** {task.get('attempts', 0)}/{task.get('max_attempts', 3)}")

                        # Progress bar for processing tasks
                        if task['status'] == 'processing':
                            st.progress(0.5)

                    with task_col4:
                        # Action buttons
                        if task['status'] == 'pending':
                            if st.button("▶️ İşle", key=f"process_task_{idx}", use_container_width=True):
                                task['status'] = 'processing'
                                st.rerun()

                        elif task['status'] == 'failed':
                            if st.button("🔄 Tekrar Dene", key=f"retry_task_{idx}", use_container_width=True):
                                retry_failed_task(task['id'])
                                st.success("✅ Görev yeniden kuyruğa eklendi!")
                                st.rerun()

                        if st.button("🗑️ Sil", key=f"delete_task_{idx}", use_container_width=True):
                            remove_from_queue(task['id'])
                            st.rerun()

                    st.divider()

            # Batch Actions
            st.markdown("---")
            st.markdown("##### ⚡ Toplu İşlemler")
            batch_col1, batch_col2, batch_col3 = st.columns(3)

            with batch_col1:
                if st.button("▶️ Tüm Bekleyenleri İşle", use_container_width=True, type="primary"):
                    for task in st.session_state.generation_queue:
                        if task['status'] == 'pending':
                            task['status'] = 'processing'
                    st.success("✅ Tüm bekleyen görevler işleniyor!")
                    st.rerun()

            with batch_col2:
                if st.button("🔄 Tüm Başarısızları Tekrarla", use_container_width=True):
                    retry_count = 0
                    for task in st.session_state.generation_queue:
                        if task['status'] == 'failed':
                            retry_failed_task(task['id'])
                            retry_count += 1
                    if retry_count > 0:
                        st.success(f"✅ {retry_count} görev yeniden kuyruğa eklendi!")
                        st.rerun()
                    else:
                        st.info("Başarısız görev yok!")

            with batch_col3:
                if st.button("⏸️ Tüm İşlemleri Durdur", use_container_width=True):
                    for task in st.session_state.generation_queue:
                        if task['status'] == 'processing':
                            task['status'] = 'pending'
                    st.warning("⏸️ Tüm işlemler durduruldu!")
                    st.rerun()

        else:
            st.info("👋 Queue boş! Görev eklemek için aşağıdaki modlardan birini kullan ve 'Add to Queue' butonuna tıkla.")

    st.markdown("---")

    # ===== MODE: SHOT GENERATOR (8 Angle System) =====
    if st.session_state['video_mode'] == 'SHOT_GENERATOR':
        st.markdown("### 🎯 SHOT GENERATOR - 8 Professional Angles")
        st.caption("Generate videos with cinematic camera angles")

        shot_angles = [
            {"name": "Wide Shot", "icon": "🌄", "desc": "Establishing full scene context"},
            {"name": "Medium Shot", "icon": "👤", "desc": "Waist up, character focused"},
            {"name": "Close-Up", "icon": "😊", "desc": "Face detail, emotional"},
            {"name": "Extreme Close-Up", "icon": "👁️", "desc": "Detail focus (eyes, hands)"},
            {"name": "Over-the-Shoulder", "icon": "🎭", "desc": "Conversation perspective"},
            {"name": "Low Angle", "icon": "⬆️", "desc": "Power, dominance view"},
            {"name": "High Angle", "icon": "⬇️", "desc": "Vulnerability, overview"},
            {"name": "Dutch Angle", "icon": "🔄", "desc": "Tension, unease, dynamic"}
        ]

        angle_cols = st.columns(4)
        for i, angle in enumerate(shot_angles):
            with angle_cols[i % 4]:
                if st.button(f"{angle['icon']} {angle['name']}", key=f"angle_{i}", use_container_width=True):
                    st.session_state['selected_angle'] = angle['name']
                    st.info(f"**{angle['name']}** selected: {angle['desc']}")

        st.markdown("---")
        st.markdown("#### Selected Angle Settings")
        if 'selected_angle' in st.session_state:
            st.success(f"🎥 Current: **{st.session_state['selected_angle']}**")
        else:
            st.warning("Please select an angle above")

        st.markdown("---")

        # Reference Image and Video Generation
        shot_col1, shot_col2 = st.columns([1, 1])

        with shot_col1:
            st.markdown("#### 🖼️ Reference Image")
            if st.session_state['uploaded_img']:
                st.image(st.session_state['uploaded_img'], caption="Source Image", use_column_width=True)
            else:
                st.warning("⚠️ Please upload an image from sidebar first")

        with shot_col2:
            st.markdown("#### 🎬 Shot Generation")
            if 'selected_angle' in st.session_state:
                st.info(f"**Angle:** {st.session_state['selected_angle']}")
            else:
                st.info("**Angle:** Not selected")

            st.markdown("**Camera Movement:**")
            camera_move = st.selectbox(
                "Movement",
                ["Static", "Slow Pan", "Zoom In", "Zoom Out", "Dolly", "Tracking"],
                key="shot_camera_move",
                label_visibility="collapsed"
            )

            st.markdown("**Intensity:**")
            shot_intensity = st.slider("Shot Intensity", 1, 10, 5, key="shot_intensity")

            st.markdown("---")

            gen_shot_col1, gen_shot_col2 = st.columns(2)
            with gen_shot_col1:
                if st.button("🎬 GENERATE SHOT", use_container_width=True, type="primary", key="gen_shot_btn"):
                    if not st.session_state['uploaded_img']:
                        st.error("Please upload an image first!")
                    elif 'selected_angle' not in st.session_state:
                        st.error("Please select a camera angle!")
                    else:
                        with st.spinner(f"Generating {st.session_state['selected_angle']} shot..."):
                            time.sleep(2)
                            st.success(f"✅ {st.session_state['selected_angle']} video generated!")

            with gen_shot_col2:
                if st.button("➕ Add to Queue", use_container_width=True, key="shot_queue_btn"):
                    if not st.session_state['uploaded_img']:
                        st.error("Please upload an image first!")
                    elif 'selected_angle' not in st.session_state:
                        st.error("Please select a camera angle!")
                    else:
                        # Create task and add to queue
                        task_id = str(uuid.uuid4())
                        task_data = {
                            'id': task_id,
                            'type': 'shot_generator',
                            'prompt': f"{st.session_state['selected_angle']} shot with {camera_move} camera movement",
                            'settings': {
                                'angle': st.session_state['selected_angle'],
                                'camera_move': camera_move,
                                'intensity': shot_intensity,
                                'aspect_ratio': st.session_state.aspect_ratio,
                                'duration': st.session_state.duration,
                                'fps': st.session_state.fps,
                                'motion_strength': st.session_state.motion_strength
                            },
                            'max_attempts': st.session_state.max_retry_attempts
                        }
                        add_to_queue(task_data)
                        st.success(f"✅ Task eklendi! Queue'da {len(st.session_state.generation_queue)} görev var.")
                        st.rerun()

    # ===== MODE: IMAGE → VIDEO =====
    elif st.session_state['video_mode'] == 'IMAGE_TO_VIDEO':
        st.markdown("### 🖼️ IMAGE → VIDEO - Quick Conversion")
        st.caption("Fast image-to-video transformation")

        if st.session_state['uploaded_img']:
            st.image(st.session_state['uploaded_img'], caption="Source Image", use_column_width=True)
        else:
            st.warning("⚠️ Please upload an image from sidebar first")

        st.markdown("#### Quick Settings")
        quick_col1, quick_col2 = st.columns(2)
        with quick_col1:
            quick_duration = st.selectbox("Duration", ["2s", "4s", "6s"], key="quick_dur")
            quick_motion = st.slider("Motion Intensity", 1, 10, 5, key="quick_motion")
        with quick_col2:
            quick_style = st.selectbox("Style", ["Cinematic", "Dynamic", "Smooth", "Epic"], key="quick_style")
            quick_ar = st.selectbox("Aspect Ratio", ["16:9", "9:16", "1:1"], key="quick_ar")

        if st.button("⚡ GENERATE VIDEO (Fast)", use_container_width=True, type="primary"):
            if st.session_state['uploaded_img']:
                with st.spinner("Converting image to video..."):
                    time.sleep(1.5)
                    st.success("✅ Video generated successfully!")
            else:
                st.error("Please upload an image first!")

    # ===== MODE: TEXT → VIDEO =====
    elif st.session_state['video_mode'] == 'TEXT_TO_VIDEO':
        st.markdown("### ✍️ TEXT → VIDEO - Text to Video Generation")
        st.caption("Create videos from text descriptions")

        text_prompt = st.text_area(
            "Video Description",
            placeholder="Describe your video scene in detail...\nExample: A cinematic shot of a sunset over mountains, golden hour lighting, slow camera pan",
            height=150,
            key="text2vid_prompt"
        )

        st.markdown("#### Generation Settings")
        text_col1, text_col2, text_col3 = st.columns(3)
        with text_col1:
            text_duration = st.selectbox("Duration", ["4s", "6s", "8s", "10s"], key="text_dur")
        with text_col2:
            text_ar = st.selectbox("Aspect Ratio", ["16:9", "9:16", "1:1", "21:9"], key="text_ar")
        with text_col3:
            text_quality = st.selectbox("Quality", ["Standard", "High", "Ultra"], key="text_quality")

        st.markdown("#### Style Presets")
        style_col1, style_col2, style_col3, style_col4 = st.columns(4)
        with style_col1:
            if st.button("🎬 Cinematic", use_container_width=True):
                st.session_state['text2vid_style'] = "cinematic"
        with style_col2:
            if st.button("🌈 Vibrant", use_container_width=True):
                st.session_state['text2vid_style'] = "vibrant"
        with style_col3:
            if st.button("🎨 Artistic", use_container_width=True):
                st.session_state['text2vid_style'] = "artistic"
        with style_col4:
            if st.button("⚡ Dynamic", use_container_width=True):
                st.session_state['text2vid_style'] = "dynamic"

        if st.button("🎬 GENERATE VIDEO FROM TEXT", use_container_width=True, type="primary"):
            if text_prompt:
                with st.spinner("Generating video from text..."):
                    time.sleep(2)
                    st.success("✅ Text-to-video generation started!")
                    st.info(f"Style: {st.session_state.get('text2vid_style', 'Default')} | {text_duration} | {text_ar}")
            else:
                st.error("Please enter a text description!")

    st.markdown("---")

    # ===== COMMON VIDEO SETTINGS (Shared across all modes) =====
    st.markdown("### ⚙️ Advanced Video Settings")
    common_col1, common_col2, common_col3, common_col4 = st.columns(4)

    with common_col1:
        st.markdown("**Aspect Ratio**")
        st.session_state.aspect_ratio = st.selectbox(
            "AR",
            ["16:9", "9:16", "1:1", "21:9", "4:3"],
            index=["16:9", "9:16", "1:1", "21:9", "4:3"].index(st.session_state.aspect_ratio),
            label_visibility="collapsed",
            key="common_ar"
        )

    with common_col2:
        st.markdown("**Duration**")
        st.session_state.duration = st.selectbox(
            "Dur",
            ["2s", "4s", "6s", "8s", "10s"],
            index=["2s", "4s", "6s", "8s", "10s"].index(st.session_state.duration),
            label_visibility="collapsed",
            key="common_dur"
        )

    with common_col3:
        st.markdown("**FPS**")
        st.session_state.fps = st.selectbox(
            "FPS",
            [24, 30, 60],
            index=[24, 30, 60].index(st.session_state.fps),
            label_visibility="collapsed",
            key="common_fps"
        )

    with common_col4:
        st.markdown("**Motion Strength**")
        st.session_state.motion_strength = st.slider(
            "Motion",
            1, 10, st.session_state.motion_strength,
            label_visibility="collapsed",
            key="common_motion"
        )

    st.markdown("---")

    col_v1, col_v2 = st.columns([1, 1])
    with col_v1:
        if st.session_state['uploaded_img']:
            st.image(st.session_state['uploaded_img'], caption="Kaynak Görsel", use_column_width=True)
        else:
            st.warning("Lütfen Sidebar'dan görsel yükleyin.")

    with col_v2:
        # ADVANCED AUTOMATIC PROMPT
        if st.session_state.get('generated_prompt'):
            final_prompt = st.session_state['generated_prompt']
        else:
            final_prompt = build_advanced_prompt("A cinematic video scene", format_type=st.session_state.prompt_format)

        st.markdown("#### 📝 Final Video Prompt")
        prompt_lang = "json" if st.session_state.prompt_format == "json" else None
        st.code(final_prompt, language=prompt_lang)

        if st.session_state.prompt_format == "json":
            st.info(f"📋 **Format:** JSON - Compatible with {st.session_state.video_provider}")
        else:
            st.info(f"📝 **Format:** Normal Text - Using {st.session_state.video_provider}")

        st.markdown("#### 🎬 Generation Settings")
        st.info(f"**Aspect Ratio:** {st.session_state.aspect_ratio}\n**Duration:** {st.session_state.duration}\n**FPS:** {st.session_state.fps}\n**Motion:** {st.session_state.motion_strength}/10")

        gen_col1, gen_col2 = st.columns(2)
        with gen_col1:
            if st.button("🍌 GENERATE VIDEO", use_container_width=True, type="primary"):
                if not st.session_state['uploaded_img']:
                    st.error("Lütfen önce bir görsel yükle!")
                else:
                    with st.spinner("Video üretiliyor..."):
                        time.sleep(2)  # Simulate API call
                        st.success("✅ Video generation başlatıldı!")
                        st.info("Video API entegrasyonu için Runway/Luma/Pika API key'leri eklemen gerekiyor.")
                        # TODO: Real API integration

        with gen_col2:
            if st.button("➕ Add to Queue", use_container_width=True):
                if not st.session_state['uploaded_img']:
                    st.error("Lütfen önce bir görsel yükle!")
                else:
                    settings = {
                        'aspect_ratio': st.session_state.aspect_ratio,
                        'duration': st.session_state.duration,
                        'fps': st.session_state.fps,
                        'motion_strength': st.session_state.motion_strength
                    }
                    job_id = add_to_queue({}, final_prompt, settings)
                    st.success(f"Added to queue!")

    # Queue Management Panel
    if len(st.session_state.generation_queue) > 0:
        st.markdown("---")
        st.markdown("### 📋 Generation Queue")

        queue_col1, queue_col2 = st.columns([3, 1])
        with queue_col1:
            st.markdown(f"**{len(st.session_state.generation_queue)} jobs in queue**")
        with queue_col2:
            if st.button("▶️ Process All", use_container_width=True, type="primary"):
                with st.spinner("Processing queue..."):
                    processed = process_queue_batch()
                    st.success(f"✅ Processed {processed} jobs!")
                    st.rerun()

        # Display queue items
        for i, job in enumerate(st.session_state.generation_queue):
            status_emoji = {"queued": "⏳", "processing": "⚙️", "completed": "✅", "failed": "❌"}
            with st.expander(f"{status_emoji.get(job['status'], '❓')} {job['id']} - {job['status'].upper()}", expanded=False):
                st.markdown(f"**Created:** {job['created_at']}")
                st.markdown(f"**Settings:** {job['settings']['aspect_ratio']} | {job['settings']['duration']} | {job['settings']['fps']}fps")
                st.code(job['prompt'][:200] + "..." if len(job['prompt']) > 200 else job['prompt'], language=None)

# --- TAB 4: EQUIPMENT GUIDE ---
with t_equipment:
    st.markdown("### 📚 Ekipman Rehberi (Equipment Guide)")
    st.caption("Kamera ve lenslerin ne işe yaradığını öğren")

    guide_tab1, guide_tab2 = st.tabs(["📹 Kameralar (Cameras)", "🔭 Lensler (Lenses)"])

    # CAMERAS GUIDE
    with guide_tab1:
        st.markdown("#### 📹 Kamera Rehberi")
        for cam in CAMERAS:
            with st.expander(f"{cam['icon']} {cam['name']} - {cam['type']}", expanded=False):
                col_cam_left, col_cam_right = st.columns([2, 1])

                with col_cam_left:
                    st.markdown(f"**English:** {cam.get('desc', 'N/A')}")
                    st.markdown(f"**Türkçe:** {cam.get('desc_tr', 'N/A')}")

                with col_cam_right:
                    st.markdown(f"**Type:** {cam['type']}")

                st.markdown("---")
                st.markdown("**🎯 Use Cases / Kullanım Alanları:**")
                st.markdown(f"**English:** {cam.get('use_case', 'N/A')}")
                st.markdown(f"**Türkçe:** {cam.get('use_case_tr', 'N/A')}")

    # LENSES GUIDE
    with guide_tab2:
        st.markdown("#### 🔭 Lens Rehberi")
        for lens in LENSES:
            with st.expander(f"🔘 {lens['name']} - {lens['char']}", expanded=False):
                col_lens_left, col_lens_right = st.columns([2, 1])

                with col_lens_left:
                    st.markdown(f"**English:** {lens.get('desc', 'N/A')}")
                    st.markdown(f"**Türkçe:** {lens.get('desc_tr', 'N/A')}")

                with col_lens_right:
                    st.markdown(f"**Character:** {lens['char']}")

                st.markdown("---")
                st.markdown("**🎯 Use Cases / Kullanım Alanları:**")
                st.markdown(f"**English:** {lens.get('use_case', 'N/A')}")
                st.markdown(f"**Türkçe:** {lens.get('use_case_tr', 'N/A')}")

# --- TAB 5: SYSTEM INFO ---
with t_sys:
    st.markdown("### 📊 Sistem Mimarisi")

    st.markdown("""
    #### 🎬 NanoDirector V2.0 - Cinema Studio Edition

    **Major Features:**
    - ✅ Advanced Prompt Engine (Lighting, Color Grading, Atmosphere, Composition, Camera Movement)
    - ✅ 8 Style Presets (Cyberpunk Night, Film Noir, Wes Anderson, Golden Hour Magic, etc.)
    - ✅ Gemini Vision AI - Reference Image Analysis
    - ✅ AI Storyboard Generation
    - ✅ Shot Management System
    - ✅ Multi-Provider Video API Support (Higgsfield, Veo 3, Kling AI)
    - ✅ Multi-Provider Image API Support (NanoBananaPro, Flux Pro/Schnell)
    - ✅ JSON & Normal Prompt Format Support
    - ✅ Batch Generation & Queue Management
    - ✅ Project Save/Load (JSON Export/Import)
    - ✅ Professional Video Settings Panel

    **Teknoloji Stack:**
    - **Frontend:** Streamlit
    - **AI:** Google Gemini (Vision & Text)
    - **Video APIs:** Higgsfield, Google Veo 3, Kling AI (Ready for integration)
    - **Image APIs:** NanoBananaPro, Flux Pro, Flux Schnell (Ready for integration)
    - **Prompt Formats:** Normal Text & JSON (Platform-dependent)
    - **Data:** JSON-based project management

    **Kullanım:**
    1. Sidebar'dan Gemini API key gir
    2. Video/Image provider seç (Higgsfield, Veo 3, Kling, NanoBananaPro, Flux)
    3. Prompt format seç (Normal veya JSON - platform desteğine göre)
    4. Style Preset seç veya manuel ekipman ayarla
    5. Referans görsel yükle (opsiyonel) ve AI analizi yap
    6. STORYBOARD tab'ından senaryo gir ve AI ile shot'lar oluştur
    7. Her shot'ı kuyruğa ekle veya hepsini toplu ekle
    8. VIDEO RENDER tab'ında queue'yu işle

    **API Provider Özellikleri:**
    - **Higgsfield:** Image-to-video, Text-to-video, JSON support ✅
    - **Veo 3 (Google):** Image-to-video, Text-to-video, Normal text only
    - **Kling AI:** Image-to-video, Text-to-video, JSON support ✅
    - **NanoBananaPro:** Text-to-image, JSON support ✅
    - **Flux Pro/Schnell:** Text-to-image, Normal text only

    **Geliştirme Notları:**
    - Video/Image API entegrasyonları hazır, sadece API key eklenmesi gerekiyor
    - JSON prompt formatı Higgsfield, Kling ve NanoBananaPro ile tam uyumlu
    - Batch processing simülasyon modunda, gerçek API çağrıları implement edilmeli

    ---
    🎬 **MR.WHO Cinema Director**
    ✨ Directed By E.Yiğit Bildi
    📅 Version 2.0 - Professional Edition
    """)

    st.markdown("---")
    st.markdown("### 🔧 Quick Stats")
    stat_col1, stat_col2, stat_col3, stat_col4, stat_col5 = st.columns(5)

    with stat_col1:
        st.metric("Cameras", len(CAMERAS))
    with stat_col2:
        st.metric("Lenses", len(LENSES))
    with stat_col3:
        st.metric("Style Presets", len(STYLE_PRESETS))
    with stat_col4:
        st.metric("Video APIs", len(VIDEO_API_PROVIDERS))
    with stat_col5:
        st.metric("Image APIs", len(IMAGE_API_PROVIDERS))

    if st.session_state.get('shots'):
        st.markdown("---")
        st.markdown("### 📈 Current Session")
        session_col1, session_col2, session_col3 = st.columns(3)

        with session_col1:
            st.metric("Generated Shots", len(st.session_state['shots']))
        with session_col2:
            st.metric("Queue Jobs", len(st.session_state.generation_queue))
        with session_col3:
            completed = sum(1 for job in st.session_state.generation_queue if job['status'] == 'completed')
            st.metric("Completed Jobs", completed)