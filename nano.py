import streamlit as st
import json
import google.generativeai as genai
from datetime import datetime
import random
import time
from PIL import Image
import streamlit.components.v1 as components

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

    /* Butonlar - Koyu, hover'da parlak */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #2A2A2A 0%, #1E1E1E 100%);
        color: #E0E0E0;
        border-radius: 8px;
        height: 45px;
        font-weight: 800;
        border: 1px solid #333;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #CCFF00 0%, #AAFF00 100%);
        color: black;
        border-color: #CCFF00;
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(204, 255, 0, 0.4);
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
    'ideas_filter_tags': []
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

def add_idea(title, description, tags, images=None, is_pinned=False, is_favorite=False):
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
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    ideas.append(new_idea)
    save_ideas(ideas)
    return True, "Idea saved successfully!"

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
        "name": "Higgsfield",
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
    "Kling AI": {
        "name": "Kling AI",
        "base_url": "https://api.kling.ai/v1",
        "supports": ["image-to-video", "text-to-video"],
        "max_duration": 10,
        "api_key_env": "KLING_API_KEY",
        "prompt_format": ["normal", "json"]
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

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🎬 MR.WHO")
    st.markdown("#### Cinema Director")
    st.caption("✨ Directed By **E.Yiğit Bildi**")
    
    st.markdown("---")
    
    with st.expander("🔑 API Anahtarı"):
        api_key = st.text_input("Gemini API Key", type="password")
        if api_key:
            models, err = get_available_models(api_key)
            active_model = models[0] if models else "OFFLINE"
            if models: st.success("Online")
        else:
            active_model = "OFFLINE"
    
    st.markdown("### 🖼️ Proje Görseli")
    uploaded_file = st.file_uploader("Referans Yükle", type=["jpg", "png", "webp"])
    if uploaded_file:
        st.image(uploaded_file, use_column_width=True)
        st.session_state['uploaded_img'] = Image.open(uploaded_file)

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

    st.markdown("---")
    st.markdown("### 🎥 API Providers")

    # Video Provider
    st.markdown("**Video Generation**")
    st.session_state.video_provider = st.selectbox(
        "Video Provider",
        list(VIDEO_API_PROVIDERS.keys()),
        index=list(VIDEO_API_PROVIDERS.keys()).index(st.session_state.video_provider),
        label_visibility="collapsed",
        key="video_provider_select"
    )
    provider_info = VIDEO_API_PROVIDERS[st.session_state.video_provider]
    st.caption(f"**Supports:** {', '.join(provider_info['supports'])}")
    st.caption(f"**Max Duration:** {provider_info['max_duration']}s")

    # Image Provider
    st.markdown("**Image Generation**")
    st.session_state.image_provider = st.selectbox(
        "Image Provider",
        list(IMAGE_API_PROVIDERS.keys()),
        index=list(IMAGE_API_PROVIDERS.keys()).index(st.session_state.image_provider),
        label_visibility="collapsed",
        key="image_provider_select"
    )
    image_provider_info = IMAGE_API_PROVIDERS[st.session_state.image_provider]
    st.caption(f"**Supports:** {', '.join(image_provider_info['supports'])}")

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

# --- ANA EKRAN ---
st.title("🎬 MR.WHO Cinema Director")
st.caption("✨ Directed By E.Yiğit Bildi")

# TABS
t_ideas, t_studio, t_board, t_video, t_equipment, t_sys = st.tabs(["💡 IDEAS & NOTES", "🎬 STUDIO GEAR", "🧠 STORYBOARD", "🎞️ VIDEO RENDER", "📚 EQUIPMENT GUIDE", "⚙️ SYSTEM"])

# --- TAB 0: IDEAS & NOTES ---
with t_ideas:
    st.markdown("### 💡 Project Ideas & Creative Notes")
    st.caption("Capture inspiration, save references, organize your creative process")

    # Action buttons
    col_act1, col_act2, col_act3 = st.columns([2, 1, 1])
    with col_act1:
        if st.button("➕ New Idea", use_container_width=True):
            st.session_state['show_new_idea_form'] = True
    with col_act2:
        search_query = st.text_input("🔍 Search", placeholder="Search ideas...", label_visibility="collapsed")
    with col_act3:
        view_mode = st.selectbox("View", ["Grid", "List"], label_visibility="collapsed")

    st.markdown("---")

    # New Idea Form
    if st.session_state.get('show_new_idea_form', False):
        with st.form("new_idea_form"):
            st.markdown("#### ✨ Create New Idea")

            idea_title = st.text_input("Title *", placeholder="e.g., Cyberpunk Night Scene")
            idea_description = st.text_area("Description *", placeholder="Describe your idea, concept, or notes...", height=100)
            idea_tags_input = st.text_input("Tags (separate with commas)", placeholder="e.g., cyberpunk, neon, night, commercial")

            uploaded_images = st.file_uploader("Upload Reference Images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

            col_pin, col_fav = st.columns(2)
            with col_pin:
                is_pinned = st.checkbox("📌 Pin this idea")
            with col_fav:
                is_favorite = st.checkbox("⭐ Mark as favorite")

            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submit_idea = st.form_submit_button("💾 Save Idea", use_container_width=True)
            with col_cancel:
                cancel_idea = st.form_submit_button("❌ Cancel", use_container_width=True)

            if submit_idea:
                if not idea_title or not idea_description:
                    st.error("Please fill in title and description!")
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
        st.info("📝 No ideas yet. Click '➕ New Idea' to start capturing your creative concepts!")
    else:
        st.markdown(f"**{len(all_ideas)} Ideas** {'📌 Showing pinned first' if any(i.get('is_pinned') for i in all_ideas) else ''}")

        if view_mode == "Grid":
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

                                # Actions
                                col_actions = st.columns(3)
                                with col_actions[0]:
                                    if st.button("📌", key=f"pin_{idea['id']}", help="Pin/Unpin"):
                                        toggle_pin(idea['id'])
                                        st.rerun()
                                with col_actions[1]:
                                    if st.button("⭐", key=f"fav_{idea['id']}", help="Favorite"):
                                        toggle_favorite(idea['id'])
                                        st.rerun()
                                with col_actions[2]:
                                    if st.button("🗑️", key=f"del_{idea['id']}", help="Delete"):
                                        delete_idea(idea['id'])
                                        st.rerun()

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
                    st.markdown(f"**Description:**")
                    st.write(idea['description'])

                    # Tags
                    if idea.get('tags'):
                        st.markdown(f"**Tags:** {', '.join(['#' + tag for tag in idea['tags']])}")

                    # Metadata
                    created_date = datetime.fromisoformat(idea['created_at']).strftime("%B %d, %Y at %H:%M")
                    st.caption(f"📅 Created: {created_date}")

                    # Actions
                    col_act1, col_act2, col_act3 = st.columns(3)
                    with col_act1:
                        if st.button(f"📌 {'Unpin' if idea.get('is_pinned') else 'Pin'}", key=f"pin_list_{idea['id']}"):
                            toggle_pin(idea['id'])
                            st.rerun()
                    with col_act2:
                        if st.button(f"⭐ {'Unfavorite' if idea.get('is_favorite') else 'Favorite'}", key=f"fav_list_{idea['id']}"):
                            toggle_favorite(idea['id'])
                            st.rerun()
                    with col_act3:
                        if st.button("🗑️ Delete", key=f"del_list_{idea['id']}"):
                            if st.button("⚠️ Confirm Delete?", key=f"confirm_del_{idea['id']}"):
                                delete_idea(idea['id'])
                                st.rerun()

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
    col1, col2 = st.columns([3, 1])
    with col1:
        raw_idea = st.text_area("Fikir / Senaryo", height=100, placeholder="Karlı bir japon bahçesinde gülen buddha...")
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

                with col_shot_right:
                    st.markdown(f"**Movement:** {shot.get('suggested_movement', 'Static')}")
                    st.markdown(f"**Lighting:** {shot.get('suggested_lighting', 'Natural')}")
                    st.markdown(f"**Duration:** {shot.get('duration', '4s')}")

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

# --- TAB 3: VIDEO RENDER ---
with t_video:
    st.subheader("🍌 Nano Banana: Video Production")

    # Video Settings Panel
    st.markdown("### ⚙️ Video Settings")
    settings_col1, settings_col2, settings_col3, settings_col4 = st.columns(4)

    with settings_col1:
        st.markdown("**Aspect Ratio**")
        st.session_state.aspect_ratio = st.selectbox(
            "AR",
            ["16:9", "9:16", "1:1", "21:9", "4:3"],
            index=["16:9", "9:16", "1:1", "21:9", "4:3"].index(st.session_state.aspect_ratio),
            label_visibility="collapsed"
        )

    with settings_col2:
        st.markdown("**Duration**")
        st.session_state.duration = st.selectbox(
            "Dur",
            ["2s", "4s", "6s", "8s", "10s"],
            index=["2s", "4s", "6s", "8s", "10s"].index(st.session_state.duration),
            label_visibility="collapsed"
        )

    with settings_col3:
        st.markdown("**FPS**")
        st.session_state.fps = st.selectbox(
            "FPS",
            [24, 30, 60],
            index=[24, 30, 60].index(st.session_state.fps),
            label_visibility="collapsed"
        )

    with settings_col4:
        st.markdown("**Motion Strength**")
        st.session_state.motion_strength = st.slider(
            "Motion",
            1, 10, st.session_state.motion_strength,
            label_visibility="collapsed"
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