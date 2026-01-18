import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import random
import io

# --- 設定 ---
CARD_WIDTH = 400
CARD_HEIGHT = 560
BORDER_WIDTH = 15

# レアリティごとの設定 (確率, 枠色, 攻撃力範囲)
RARITY_SETTINGS = {
    "LR": {"prob": 0.01, "color": "#FF00FF", "atk_min": 9000, "atk_max": 9999, "bg_effect": "🌈"},
    "SSR": {"prob": 0.06, "color": "#FFD700", "atk_min": 6000, "atk_max": 8999, "bg_effect": "✨"},
    "SR": {"prob": 0.15, "color": "#C0C0C0", "atk_min": 3000, "atk_max": 5999, "bg_effect": "⚡"},
    "R": {"prob": 0.78, "color": "#8B4513", "atk_min": 1000, "atk_max": 2999, "bg_effect": ""},
}

def determine_rarity():
    """確率に基づいてレアリティを決定する"""
    rand = random.random()
    cumulative = 0
    for rarity, data in RARITY_SETTINGS.items():
        cumulative += data["prob"]
        if rand <= cumulative:
            return rarity
    return "R"

def create_card_image(base_image, char_name, element):
    """画像を合成してカードを作成する"""
    
    # 1. レアリティとステータスの決定
    rarity = determine_rarity()
    settings = RARITY_SETTINGS[rarity]
    atk = random.randint(settings["atk_min"], settings["atk_max"])
    defense = random.randint(settings["atk_min"] - 500, settings["atk_max"] - 500)
    
    # 2. ベース画像の準備 (リサイズとトリミング)
    img = base_image.convert("RGB")
    
    # アスペクト比を維持してCenter Crop風にリサイズ
    aspect_ratio = CARD_WIDTH / CARD_HEIGHT
    img_ratio = img.width / img.height
    
    if img_ratio > aspect_ratio:
        new_height = CARD_HEIGHT
        new_width = int(new_height * img_ratio)
    else:
        new_width = CARD_WIDTH
        new_height = int(new_width / img_ratio)
        
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 中央を切り抜く
    left = (new_width - CARD_WIDTH) / 2
    top = (new_height - CARD_HEIGHT) / 2
    img = img.crop((left, top, left + CARD_WIDTH, top + CARD_HEIGHT))

    # 3. 描画オブジェクト作成
    draw = ImageDraw.Draw(img)
    
    # フォント読み込み (同階層のfont.ttfを探す)
    try:
        font_title = ImageFont.truetype("font.ttf", 32)
        font_stats = ImageFont.truetype("font.ttf", 24)
        font_desc = ImageFont.truetype("font.ttf", 16)
    except IOError:
        # フォントがない場合はデフォルト (日本語非対応の可能性あり)
        font_title = ImageFont.load_default()
        font_stats = ImageFont.load_default()
        font_desc = ImageFont.load_default()

    # 4. UIパーツの描画
    
    # 下部のステータスウィンドウ (半透明の黒)
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([(10, 400), (390, 550)], fill=(0, 0, 0, 180), outline=settings["color"], width=2)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # 枠線 (レアリティカラー)
    draw.rectangle([(0,0), (CARD_WIDTH-1, CARD_HEIGHT-1)], outline=settings["color"], width=BORDER_WIDTH)
    
    # テキスト描画
    # 名前
    draw.text((30, 410), f"{char_name}", font=font_title, fill="white")
    # レアリティ
    draw.text((320, 415), f"{rarity}", font=font_title, fill=settings["color"])
    # 属性・ステータス
    draw.text((30, 460), f"属性: {element}", font=font_stats, fill="cyan")
    draw.text((30, 490), f"ATK: {atk}", font=font_stats, fill="#FF5555")
    draw.text((200, 490), f"DEF: {defense}", font=font_stats, fill="#5555FF")
    
    # 演出効果（簡易的）
    if settings["bg_effect"]:
        draw.text((20, 20), settings["bg_effect"], font=font_title, fill="white")

    return img, rarity, atk, defense

# --- Streamlit アプリ本体 ---
st.title("🃏 NanoBanana Card Maker")
st.write("画像をアップロードして、デュエルカードを生成しよう！")

# 1. 入力エリア
col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("キャラクター画像をアップロード", type=["jpg", "png", "webp"])
with col2:
    char_name = st.text_input("キャラクター名", value="名無しの戦士")
    element = st.selectbox("属性 (Attribute)", ["🔥 Fire", "💧 Water", "🌲 Earth", "⚡ Light", "🌑 Dark"])

# 2. 生成ボタン
if uploaded_file is not None:
    st.markdown("---")
    if st.button("カード生成 / GENERATE", type="primary"):
        # 画像を開く
        image = Image.open(uploaded_file)
        
        # カード生成処理
        with st.spinner('Generating Card Data...'):
            card_img, rarity, atk, def_val = create_card_image(image, char_name, element)
        
        # 3. 結果表示
        st.success(f"生成完了！ レアリティ: **{rarity}**")
        
        # 画像表示
        st.image(card_img, caption=f"{char_name} (ATK:{atk})", width=400)
        
        # ダウンロードボタン
        # 画像をバイト列に変換
        buf = io.BytesIO()
        card_img.save(buf, format="PNG")
        byte_im = buf.getvalue()
        
        st.download_button(
            label="カード画像をダウンロード",
            data=byte_im,
            file_name=f"card_{rarity}_{char_name}.png",
            mime="image/png"
        )
        
        # デバッグ用データ表示 (将来のDB用)
        st.json({
            "name": char_name,
            "rarity": rarity,
            "attribute": element,
            "attack": atk,
            "defense": def_val
        })