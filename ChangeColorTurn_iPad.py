import streamlit as st
import fitz
from PIL import Image, ImageEnhance
import io

try:
    RESAMPLE_FILTER = Image.Resampling.BICUBIC
except AttributeError:
    RESAMPLE_FILTER = Image.BICUBIC

# ページ設定（必ず一番最初！）
st.set_page_config(page_title="PDF Editor Pro", layout="wide")

# ==========================================
# ★パスワード認証システム★
# ==========================================
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        st.markdown("<h2 style='text-align: center; color: #FF9500;'>🔒 パスワードを入力してください</h2>", unsafe_allow_html=True)
        password = st.text_input("Password", type="password", label_visibility="collapsed")
        
        if st.button("ログイン"):
            if password == st.secrets["APP_PASSWORD"]:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("パスワードが間違っています。")
        return False
        
    return True

if check_password():
    # ==========================================
    # ★ここからメインアプリ★
    # ==========================================
    
    # カスタムCSS（デザイン）
    st.markdown("""
        <style>
        .stApp { background-color: #1A1A1A !important; color: #E2E2E2 !important; }
        [data-testid="stVerticalBlock"] > div > div { background-color: #2B2B2B; border-radius: 12px; padding: 15px; }
        h2, h3, p, span, label { color: #E2E2E2 !important; }
        button[kind="primary"] { background: linear-gradient(180deg, #FFB347 0%, #FF9500 100%) !important; color: #1A1A1A !important; min-height: 70px; font-weight: bold; border-radius: 25px; }
        .stButton > button { background-color: #444 !important; color: white !important; }
        [data-testid="stImage"] { border: 2px solid #FF9500; border-radius: 15px; padding: 10px; }
        </style>
    """, unsafe_allow_html=True)

    # タイトル
    st.markdown("""
        <div style="text-align: center; margin-top: 30px; margin-bottom: 10px;">
            <span style="font-family: 'Arial Black', sans-serif; font-size: 40px; color: #FF9500; font-weight: bold;">
                PDF ページ並び替えツール
            </span>
        </div>
    """, unsafe_allow_html=True)

    # セッションの初期化
    if 'b_sl' not in st.session_state: st.session_state.b_sl = 50.0
    if 'b_nm' not in st.session_state: st.session_state.b_nm = 50.0
    if 'c_sl' not in st.session_state: st.session_state.c_sl = 50.0
    if 'c_nm' not in st.session_state: st.session_state.c_nm = 50.0
    if 's_sl' not in st.session_state: st.session_state.s_sl = 50.0
    if 's_nm' not in st.session_state: st.session_state.s_nm = 50.0
    if 'rotations' not in st.session_state: st.session_state.rotations = {}
    if 'translations' not in st.session_state: st.session_state.translations = {}

    def sync_b_sl(): st.session_state.b_nm = st.session_state.b_sl
    def sync_b_nm(): st.session_state.b_sl = st.session_state.b_nm
    def sync_c_sl(): st.session_state.c_nm = st.session_state.c_sl
    def sync_c_nm(): st.session_state.c_sl = st.session_state.c_nm
    def sync_s_sl(): st.session_state.s_nm = st.session_state.s_sl
    def sync_s_nm(): st.session_state.s_sl = st.session_state.s_nm

    def sync_rot_sl(): 
        st.session_state.rot_nm = round(st.session_state.rot_sl, 1)
        st.session_state.rotations[st.session_state.last_page] = st.session_state.rot_nm

    def sync_rot_nm(): 
        val = st.session_state.rot_nm
        if val < 0.0: val = 359.9
        elif val > 359.9: val = 0.0
        val = round(val, 1)
        st.session_state.rot_sl = val
        st.session_state.rot_nm = val
        st.session_state.rotations[st.session_state.last_page] = val

    # ★ショートカットボタンを押したときの処理
    def set_fixed_angle(deg):
        st.session_state.rot_sl = float(deg)
        st.session_state.rot_nm = float(deg)
        st.session_state.rotations[st.session_state.last_page] = float(deg)

    def sync_pos_x(): st.session_state.translations[st.session_state.last_page]["x"] = st.session_state.pos_x
    def sync_pos_y(): st.session_state.translations[st.session_state.last_page]["y"] = st.session_state.pos_y

    def move_pos(axis, amount):
        if axis == 'x':
            st.session_state.pos_x += amount
            sync_pos_x()
        else:
            st.session_state.pos_y += amount
            sync_pos_y()

    uploaded_file = st.file_uploader("PDFファイルをドラッグ＆ドロップしてください", type=["pdf"])

    if uploaded_file is not None:
        doc = fitz.open(stream=uploaded_file.getvalue(), filetype="pdf")
        total_pages = len(doc)

        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("【1】画像処理(基準50)")
            
            st.write("明度")
            bc1, bc2 = st.columns([3, 1])
            bc1.slider("明度", 0.0, 100.0, key="b_sl", step=1.0, on_change=sync_b_sl, label_visibility="collapsed")
            bc2.number_input("明度数", 0.0, 100.0, key="b_nm", on_change=sync_b_nm, label_visibility="collapsed", step=1.0)

            st.write("コントラスト")
            cc1, cc2 = st.columns([3, 1])
            cc1.slider("コントラスト", 0.0, 100.0, key="c_sl", step=1.0, on_change=sync_c_sl, label_visibility="collapsed")
            cc2.number_input("コン数", 0.0, 100.0, key="c_nm", on_change=sync_c_nm, label_visibility="collapsed", step=1.0)

            st.write("彩度")
            sc1, sc2 = st.columns([3, 1])
            sc1.slider("彩度", 0.0, 100.0, key="s_sl", step=1.0, on_change=sync_s_sl, label_visibility="collapsed")
            sc2.number_input("彩度数", 0.0, 100.0, key="s_nm", on_change=sync_s_nm, label_visibility="collapsed", step=1.0)

            apply_mode = st.radio("適用範囲を選択", ["すべて一括", "指定ページのみ"])
            target_pages_str = ""
            if apply_mode == "指定ページのみ":
                target_pages_str = st.text_input("ページ指定 (例: 1, 3, 5-7)", value="1")

            st.divider()

            st.subheader("【2】回転調整・位置調整")
            preview_page = st.number_input(f"編集ページ (1〜{total_pages})", min_value=1, max_value=total_pages, value=1)
            current_idx = preview_page - 1
            
            if current_idx not in st.session_state.translations:
                st.session_state.translations[current_idx] = {"x": 0, "y": 0}

            if 'last_page' not in st.session_state or st.session_state.last_page != current_idx:
                st.session_state.last_page = current_idx
                st.session_state.rot_sl = float(st.session_state.rotations.get(current_idx, 0.0))
                st.session_state.rot_nm = float(st.session_state.rotations.get(current_idx, 0.0))
                saved_pos = st.session_state.translations[current_idx]
                st.session_state.pos_x = saved_pos["x"]
                st.session_state.pos_y = saved_pos["y"]
                
            st.write("回転角度")
            
            # ★4つのショートカットボタン
            btn_cols = st.columns(4)
            for i, deg in enumerate([0, 90, 180, 270]):
                if btn_cols[i].button(f"{deg}°", key=f"btn_deg_{deg}"):
                    set_fixed_angle(deg)
                    st.rerun()

            rc1, rc2 = st.columns([3, 1])
            rc1.slider("回転", 0.0, 359.9, key="rot_sl", step=0.1, on_change=sync_rot_sl, label_visibility="collapsed")
            rc2.number_input("回転数", -1.0, 360.0, key="rot_nm", on_change=sync_rot_nm, label_visibility="collapsed", step=0.1)

            st.write("左右移動 (X)")
            px1, px2, px3 = st.columns([1, 2, 1])
            px1.button("◀ 左", on_click=move_pos, args=('x', -1), key="btn_l")
            px2.number_input("X", -2000, 2000, key="pos_x", on_change=sync_pos_x, label_visibility="collapsed")
            px3.button("右 ▶", on_click=move_pos, args=('x', 1), key="btn_r")

            st.write("上下移動 (Y)")
            py1, py2, py3 = st.columns([1, 2, 1])
            py1.button("▲ 上", on_click=move_pos, args=('y', -1), key="btn_u")
            py2.number_input("Y", -2000, 2000, key="pos_y", on_change=sync_pos_y, label_visibility="collapsed")
            py3.button("下 ▼", on_click=move_pos, args=('y', 1), key="btn_d")

        def parse_pages(page_str, total):
            pages = set()
            if not page_str: return pages
            try:
                for part in page_str.split(','):
                    part = part.strip()
                    if '-' in part:
                        start, end = part.split('-')
                        for p in range(int(start), int(end) + 1): pages.add(p - 1)
                    else: pages.add(int(part) - 1)
            except: pass
            return pages

        target_pages_set = set(range(total_pages)) if apply_mode == "すべて一括" else parse_pages(target_pages_str, total_pages)

        b_val = st.session_state.b_sl / 50.0
        c_val = st.session_state.c_sl / 50.0
        s_val = st.session_state.s_sl / 50.0
        current_angle_to_apply = st.session_state.rot_sl
        pos_to_apply = st.session_state.translations[current_idx]

        with col2:
            page = doc.load_page(current_idx)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            if current_angle_to_apply != 0.0:
                img = img.rotate(-current_angle_to_apply, expand=True, resample=RESAMPLE_FILTER, fillcolor=(255, 255, 255))
                
            if pos_to_apply["x"] != 0 or pos_to_apply["y"] != 0:
                img = img.transform(img.size, Image.AFFINE, (1, 0, -pos_to_apply["x"], 0, 1, -pos_to_apply["y"]), fillcolor=(255, 255, 255))
            
            if current_idx in target_pages_set:
                img = ImageEnhance.Brightness(img).enhance(b_val)
                img = ImageEnhance.Contrast(img).enhance(c_val)
                img = ImageEnhance.Color(img).enhance(s_val)
                
            st.image(img, caption=f"ページ {preview_page} のプレビュー", use_container_width=True)

        st.divider()
        
        if st.button("【3】変更を適用して保存", type="primary"):
            with st.spinner("PDFを生成中..."):
                processed_images = []
                for i in range(total_pages):
                    p = doc.load_page(i)
                    px = p.get_pixmap(matrix=fitz.Matrix(3.0, 3.0))
                    im = Image.frombytes("RGB", [px.width, px.height], px.samples)
                    
                    ang = st.session_state.rotations.get(i, 0.0)
                    pos = st.session_state.translations.get(i, {"x":0, "y":0})
                    
                    if ang != 0.0:
                        im = im.rotate(-ang, expand=True, resample=RESAMPLE_FILTER, fillcolor=(255, 255, 255))
                        
                    if pos["x"] != 0 or pos["y"] != 0:
                        save_x = pos["x"] * 2
                        save_y = pos["y"] * 2
                        im = im.transform(im.size, Image.AFFINE, (1, 0, -save_x, 0, 1, -save_y), fillcolor=(255, 255, 255))
                        
                    if i in target_pages_set:
                        im = ImageEnhance.Brightness(im).enhance(b_val)
                        im = ImageEnhance.Contrast(im).enhance(c_val)
                        im = ImageEnhance.Color(im).enhance(s_val)
                    
                    processed_images.append(im)
                
                pdf_buffer = io.BytesIO()
                processed_images[0].save(pdf_buffer, format="PDF", resolution=100.0, save_all=True, append_images=processed_images[1:])
                
                default_filename = f"《調整変更》{uploaded_file.name}"
                st.success("✅ 完了しました！以下のボタンからダウンロードできます。")
                st.download_button(
                    label="📥 PDFをダウンロード",
                    data=pdf_buffer.getvalue(),
                    file_name=default_filename,
                    mime="application/pdf"
                )