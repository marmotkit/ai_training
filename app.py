from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, flash
import os
import random
from functools import wraps
import time
from werkzeug.utils import secure_filename
import json
import PyPDF2
from datetime import datetime
import io
from pptx import Presentation
from PIL import Image

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 數據文件路徑
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PRESENTATIONS_FILE = os.path.join(CURRENT_DIR, 'static', 'data', 'presentations.json')
UPLOADS_FILE = os.path.join(CURRENT_DIR, 'static', 'data', 'uploads.json')
QUESTIONS_FILE = os.path.join(CURRENT_DIR, 'static', 'data', 'questions.json')
SLIDES_DIR = os.path.join(CURRENT_DIR, 'static', 'slides')
UPLOAD_FOLDER = os.path.join(CURRENT_DIR, 'static', 'uploads')

# 確保目錄存在
os.makedirs(os.path.join(CURRENT_DIR, 'static', 'data'), exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SLIDES_DIR, exist_ok=True)

# 從文件加載數據
def load_data_from_file(file_path, default_data=None):
    if default_data is None:
        default_data = []
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"載入數據時發生錯誤: {str(e)}")
            return default_data
    else:
        return default_data

# 保存數據到文件
def save_data_to_file(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"保存數據時發生錯誤: {str(e)}")
        return False

# 將 PowerPoint 轉換為圖片
def convert_ppt_to_images(ppt_path, presentation_id):
    """
    將 PowerPoint 文件轉換為圖片並保存
    使用 python-pptx 和 PIL 進行轉換，提供更好的渲染效果
    """
    try:
        print(f"開始轉換 PowerPoint 文件: {ppt_path}")
        
        # 創建保存圖片的目錄
        slides_dir = os.path.join(app.static_folder, 'slides', f"presentation-{presentation_id}")
        os.makedirs(slides_dir, exist_ok=True)
        
        print(f"圖片將保存到: {slides_dir}")
        
        # 打開 PowerPoint 文件
        prs = Presentation(ppt_path)
        
        # 獲取頁數
        num_slides = len(prs.slides)
        print(f"PowerPoint 共有 {num_slides} 頁")
        
        # 設置圖片尺寸 (16:9 比例)
        width = 1280
        height = 720
        
        # 轉換每一頁為圖片
        for i, slide in enumerate(prs.slides):
            # 保存路徑
            img_path = os.path.join(slides_dir, f"slide-{i+1}.png")
            
            # 創建一個空白圖片
            img = Image.new('RGB', (width, height), 'white')
            
            # 使用 PIL 繪製文字
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            
            try:
                # 嘗試加載字體，如果失敗則使用默認字體
                try:
                    # 嘗試使用支持中文的字體
                    fonts_to_try = [
                        "simhei.ttf",  # 中文黑體
                        "simsun.ttc",  # 中文宋體
                        "msyh.ttc",    # 微軟雅黑
                        "arial.ttf",   # 英文字體
                    ]
                    
                    title_font = None
                    for font_name in fonts_to_try:
                        try:
                            title_font = ImageFont.truetype(font_name, 36)
                            break
                        except:
                            continue
                    
                    if title_font is None:
                        title_font = ImageFont.load_default()
                        
                    content_font = ImageFont.truetype(font_name, 24) if title_font != ImageFont.load_default() else title_font
                    small_font = ImageFont.truetype(font_name, 18) if title_font != ImageFont.load_default() else title_font
                except:
                    title_font = ImageFont.load_default()
                    content_font = title_font
                    small_font = title_font
                
                # 繪製幻燈片背景
                draw.rectangle([(0, 0), (width, 80)], fill="#4472C4")  # 頂部藍色條
                
                # 提取和繪製幻燈片內容
                y_position = 100
                title_found = False
                
                # 處理每個形狀
                for shape in slide.shapes:
                    if not hasattr(shape, 'text'):
                        continue
                        
                    text = shape.text.strip()
                    if not text:
                        continue
                    
                    # 檢查形狀類型和位置來確定它是標題還是內容
                    if not title_found and (hasattr(shape, 'is_title') and shape.is_title) or y_position < 150:
                        # 這是標題
                        draw.text((40, 20), text, fill="white", font=title_font)
                        title_found = True
                    else:
                        # 這是內容
                        # 處理長文本，自動換行
                        words = text.split()
                        lines = []
                        current_line = ""
                        
                        for word in words:
                            test_line = current_line + " " + word if current_line else word
                            # 檢查行寬度
                            if draw.textlength(test_line, font=content_font) < width - 80:
                                current_line = test_line
                            else:
                                lines.append(current_line)
                                current_line = word
                        
                        if current_line:
                            lines.append(current_line)
                        
                        # 繪製文本行
                        for line in lines:
                            draw.text((40, y_position), line, fill="black", font=content_font)
                            y_position += 30
                        
                        y_position += 20  # 段落間距
                
                # 如果沒有找到標題，添加默認標題
                if not title_found:
                    draw.text((40, 20), f"幻燈片 {i+1}", fill="white", font=title_font)
                
                # 繪製頁碼在右下角
                page_text = f"{i+1}/{num_slides}"
                draw.text((width-100, height-30), page_text, fill="black", font=small_font)
                
                # 嘗試提取和繪製圖片
                for shape in slide.shapes:
                    if hasattr(shape, 'image'):
                        try:
                            # 提取圖片數據
                            image_stream = io.BytesIO(shape.image.blob)
                            shape_img = Image.open(image_stream)
                            
                            # 計算圖片位置和大小
                            img_x = width // 2 - shape_img.width // 2
                            img_y = y_position
                            
                            # 確保圖片不會太大
                            max_img_width = width - 80
                            max_img_height = height - y_position - 50
                            
                            if shape_img.width > max_img_width or shape_img.height > max_img_height:
                                # 等比例縮放
                                ratio = min(max_img_width / shape_img.width, max_img_height / shape_img.height)
                                new_width = int(shape_img.width * ratio)
                                new_height = int(shape_img.height * ratio)
                                shape_img = shape_img.resize((new_width, new_height), Image.LANCZOS)
                                
                                img_x = width // 2 - new_width // 2
                            
                            # 將圖片粘貼到幻燈片上
                            img.paste(shape_img, (img_x, img_y))
                            y_position += shape_img.height + 20
                        except Exception as img_error:
                            print(f"處理幻燈片 {i+1} 中的圖片時發生錯誤: {str(img_error)}")
                
            except Exception as inner_e:
                print(f"繪製幻燈片 {i+1} 時發生錯誤: {str(inner_e)}")
                # 繪製錯誤信息
                draw.text((width//2 - 200, height//2), f"無法渲染幻燈片 {i+1}", fill="red", font=title_font)
                draw.text((width//2 - 200, height//2 + 50), str(inner_e), fill="red", font=small_font)
            
            # 保存圖片
            img.save(img_path, 'PNG')
            print(f"已保存第 {i+1} 頁到 {img_path}")
        
        return num_slides
    except Exception as e:
        print(f"轉換 PowerPoint 時發生錯誤: {str(e)}")
        return 0

# 默認數據
default_presentations = [
    {
        "id": 1,
        "title": "AI導論",
        "filename": "AI_Introduction.pdf",
        "pages": 30,
        "date": "2023/04/10",
        "size": "2.5 MB",
        "type": "presentation"
    },
    {
        "id": 2,
        "title": "機器學習基礎",
        "filename": "ML_Basics.pdf",
        "pages": 25,
        "date": "2023/04/10",
        "size": "1.8 MB",
        "type": "presentation"
    },
    {
        "id": 3,
        "title": "深度學習應用",
        "filename": "DL_Applications.pdf",
        "pages": 28,
        "date": "2023/04/10",
        "size": "2.2 MB",
        "type": "presentation"
    }
]

default_uploads = [
    {
        "id": 1,
        "title": "機器學習算法比較",
        "filename": "ML_Algorithm_Comparison.pdf",
        "type": "document",
        "date": "2023/04/15",
        "size": "1.5 MB"
    },
    {
        "id": 2,
        "title": "神經網絡架構圖解",
        "filename": "Neural_Network_Diagrams.pdf",
        "type": "document",
        "date": "2023/04/10",
        "size": "3.2 MB"
    }
]

default_questions = [
    {
        "id": 1,
        "student_name": "陳小明",
        "question": "請問深度學習和機器學習有什麼區別？",
        "time": "2023/04/08 14:30",
        "status": "已回答",
        "answer": "機器學習是人工智能的一個分支，而深度學習是機器學習的一個子領域。主要區別在於深度學習使用多層神經網絡處理更複雜的模式。"
    },
    {
        "id": 2,
        "student_name": "林小華",
        "question": "卷積神經網絡適合什麼類型的數據？",
        "time": "2023/04/09 10:15",
        "status": "待回答",
        "answer": ""
    },
    {
        "id": 3,
        "student_name": "張小芳",
        "question": "如何避免神經網絡過擬合？",
        "time": "2023/04/10 09:45",
        "status": "待回答",
        "answer": ""
    }
]

# 加載數據
presentations = load_data_from_file(PRESENTATIONS_FILE, default_presentations)
uploads = load_data_from_file(UPLOADS_FILE, default_uploads)
questions = load_data_from_file(QUESTIONS_FILE, default_questions)

# 允許的檔案類型
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 模擬講師帳號
lecturer_accounts = {
    "admin": {
        "password": "admin123",
        "name": "梁坤棠",
        "title": "副總經理"
    }
}

# 登入裝飾器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'lecturer_username' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# 路由
@app.route('/')
def index():
    # 嘗試載入講師資料（無論是否登入）
    config_path = os.path.join(os.path.dirname(__file__), 'static', 'config', 'lecturer_info.json')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # 確保session中有講師資料
                if 'lecturer_name' not in session and 'lecturer_name' in config:
                    session['lecturer_name'] = config.get('lecturer_name')
                if 'lecturer_title' not in session and 'lecturer_title' in config:
                    session['lecturer_title'] = config.get('lecturer_title')
                if 'lecturer_email' not in session and 'lecturer_email' in config:
                    session['lecturer_email'] = config.get('lecturer_email')
        except Exception as e:
            print(f"載入講師資料時發生錯誤: {str(e)}")
    
    return render_template('index.html', presentations=presentations, questions=questions)

@app.route('/presentation')
def presentation():
    presentations = load_data_from_file(PRESENTATIONS_FILE, default_presentations)
    
    # 獲取請求的簡報ID
    presentation_id = request.args.get('id')
    page = request.args.get('page', 1, type=int)
    
    # 如果沒有指定ID，顯示第一個簡報
    current_presentation = None
    if presentation_id:
        # 查找對應ID的簡報
        for p in presentations:
            if str(p['id']) == str(presentation_id):
                current_presentation = p
                break
    elif presentations:
        current_presentation = presentations[0]
        presentation_id = current_presentation['id']
    
    # 如果找不到簡報，顯示空頁面
    if not current_presentation:
        return render_template('presentation.html', 
                               presentations=presentations, 
                               current_presentation=None,
                               current_page=1,
                               total_pages=0)
    
    # 確保頁碼在有效範圍內
    total_pages = current_presentation.get('pages', 1)
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages
    
    # 檢查是否為 PowerPoint 文件，如果是，檢查是否已轉換為圖片
    if current_presentation.get('filename') and (current_presentation['filename'].lower().endswith('.ppt') or current_presentation['filename'].lower().endswith('.pptx')):
        # 檢查轉換後的圖片目錄是否存在
        slides_dir = os.path.join(app.static_folder, 'slides', f"presentation-{current_presentation['id']}")
        if not os.path.exists(slides_dir) or len(os.listdir(slides_dir)) == 0:
            # 如果不存在，執行轉換
            ppt_path = os.path.join(app.static_folder, 'uploads', current_presentation['filename'])
            if os.path.exists(ppt_path):
                num_slides = convert_ppt_to_images(ppt_path, current_presentation['id'])
                # 更新簡報頁數
                if num_slides > 0:
                    current_presentation['pages'] = num_slides
                    # 保存更新後的數據
                    save_data_to_file(PRESENTATIONS_FILE, presentations)
                    total_pages = num_slides
    
    print(f"渲染簡報頁面: ID={presentation_id}, 頁碼={page}, 總頁數={total_pages}")
    return render_template('presentation.html', 
                           presentations=presentations, 
                           current_presentation=current_presentation,
                           current_page=page,
                           total_pages=total_pages)

@app.route('/presentation/<int:presentation_id>', methods=['GET'])
def presentation_with_id(presentation_id):
    # 重定向到查詢參數格式的URL
    page = request.args.get('page', 1, type=int)
    return redirect(url_for('presentation', id=presentation_id, page=page))

@app.route('/ai-demo')
def ai_demo():
    return render_template('ai-demo.html', presentations=presentations)

@app.route('/resources')
def resources():
    return render_template('resources.html', presentations=presentations, uploads=uploads)

@app.route('/qa')
def qa():
    return render_template('qa.html', questions=questions, presentations=presentations)

# 講師登入
@app.route('/lecturer/login', methods=['POST'])
def lecturer_login():
    if request.is_json:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        remember_me = data.get('rememberMe', False)
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = request.form.get('rememberMe') == 'on'
    
    # 驗證帳號密碼
    if username in lecturer_accounts and lecturer_accounts[username]["password"] == password:
        # 登入成功，只設置username，不覆蓋姓名和職稱
        session['lecturer_username'] = username
        
        # 檢查session中是否已有從配置文件載入的資料
        # 如果沒有，才使用默認資料
        if 'lecturer_name' not in session:
            session['lecturer_name'] = lecturer_accounts[username]["name"]
        if 'lecturer_title' not in session:
            session['lecturer_title'] = lecturer_accounts[username]["title"]
        
        # 確保載入配置文件中的資料
        config_path = os.path.join(os.path.dirname(__file__), 'static', 'config', 'lecturer_info.json')
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    # 使用配置文件中的資料
                    if 'lecturer_name' in config:
                        session['lecturer_name'] = config.get('lecturer_name')
                    if 'lecturer_title' in config:
                        session['lecturer_title'] = config.get('lecturer_title')
                    if 'lecturer_email' in config:
                        session['lecturer_email'] = config.get('lecturer_email')
                    print("登入時已從配置文件載入講師資料")
            except Exception as e:
                print(f"登入時載入講師資料錯誤: {str(e)}")
        
        if not remember_me:
            # 如果不記住我，設置session在瀏覽器關閉時過期
            session.permanent = False
        else:
            # 否則設置session持久化
            session.permanent = True
        
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "帳號或密碼錯誤"})

# 講師登出
@app.route('/lecturer/logout')
def lecturer_logout():
    # 清除特定的session變數而不是整個session
    session.pop('lecturer_username', None)
    # 保留講師個人資料，這樣登出後重新登入時仍能保持個人化設定
    # session.pop('lecturer_name', None)
    # session.pop('lecturer_title', None)
    # session.pop('lecturer_email', None)
    return redirect(url_for('index'))

# 講師儀表板
@app.route('/lecturer/dashboard')
@login_required
def lecturer_dashboard():
    return render_template('lecturer/dashboard.html', 
                          presentations=presentations, 
                          questions=questions,
                          lecturer=lecturer_accounts.get(session.get('lecturer_username')))

# 回答問題
@app.route('/lecturer/answer-question', methods=['POST'])
@login_required
def answer_question():
    data = request.get_json()
    question_id = data.get('questionId')
    answer = data.get('answer')
    
    # 尋找要回答的問題
    for question in questions:
        if question['id'] == question_id:
            question['answer'] = answer
            save_data_to_file(QUESTIONS_FILE, questions)
            return jsonify({"success": True})
    
    return jsonify({"success": False, "message": "找不到問題"})

# 講師個人資料更新
@app.route('/lecturer/update-profile', methods=['POST'])
def update_lecturer_profile():
    try:
        data = request.get_json()
        name = data.get('name', '')
        title = data.get('title', '')
        email = data.get('email', '')
        
        # 更新session中的講師資料
        session['lecturer_name'] = name
        session['lecturer_title'] = title
        session['lecturer_email'] = email
        
        # 將更新的資料保存到config.json文件中
        config_path = os.path.join(os.path.dirname(__file__), 'static', 'config', 'lecturer_info.json')
        
        # 確保目錄存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # 讀取現有配置（如果存在）
        config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except:
                pass
        
        # 更新講師資料
        config['lecturer_name'] = name
        config['lecturer_title'] = title
        config['lecturer_email'] = email
        
        # 保存更新後的配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        
        return jsonify({'success': True, 'message': '個人資料已更新'})
    except Exception as e:
        print(f"更新個人資料時發生錯誤: {str(e)}")
        return jsonify({'success': False, 'message': f'更新個人資料時發生錯誤: {str(e)}'}), 500

# 講師照片更新
@app.route('/lecturer/update-photo', methods=['POST'])
def update_lecturer_photo():
    try:
        if 'photo' not in request.files:
            print("未提供照片文件")
            return jsonify({'success': False, 'message': '沒有提供照片'}), 400
        
        photo = request.files['photo']
        if photo.filename == '':
            print("未選擇檔案")
            return jsonify({'success': False, 'message': '未選擇檔案'}), 400
        
        if photo and allowed_file(photo.filename):
            # 使用固定檔案名稱
            filename = 'lecturer-photo.jpg'
            
            # 確保目錄存在
            upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'images')
            os.makedirs(upload_folder, exist_ok=True)
            
            # 保存照片
            filepath = os.path.join(upload_folder, filename)
            print(f"正在保存照片到: {filepath}")
            photo.save(filepath)
            
            # 生成時間戳以防止瀏覽器緩存
            timestamp = int(time.time())
            session['photo_timestamp'] = timestamp
            
            # 返回照片URL (包含時間戳以防止緩存)
            photo_url = f"/static/images/{filename}?t={timestamp}"
            print(f"生成照片URL: {photo_url}")
            
            return jsonify({
                'success': True, 
                'message': '照片已更新',
                'photo_url': photo_url
            })
        else:
            print("不支援的檔案類型")
            return jsonify({'success': False, 'message': '不支援的檔案類型'}), 400
    except Exception as e:
        import traceback
        print(f"更新照片時發生錯誤: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'更新照片時發生錯誤: {str(e)}'}), 500

# 上傳教材
@app.route('/lecturer/upload-material', methods=['POST'])
@login_required
def upload_material():
    if 'title' not in request.form:
        return jsonify({"success": False, "message": "未提供教材標題"})
    
    title = request.form.get('title')
    material_type = request.form.get('type')
    
    # 如果是文件上傳（非影片連結）
    if material_type != 'video':
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "未提供檔案"})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "message": "未選擇檔案"})
        
        # 檢查檔案類型
        if material_type == 'presentation' and not file.filename.lower().endswith(('.pdf', '.ppt', '.pptx')):
            return jsonify({"success": False, "message": "簡報必須是 PDF 或 PowerPoint 檔案 (.pdf, .ppt, .pptx)"})
        
        if material_type == 'document' and not file.filename.lower().endswith(('.pdf', '.doc', '.docx', '.txt')):
            return jsonify({"success": False, "message": "文件必須是 PDF、Word 或文字檔案 (.pdf, .doc, .docx, .txt)"})
        
        # 在真實環境中，這裡會保存文件到磁盤並更新資料庫
        try:
            # 安全的檔案名
            secure_filename = file.filename.replace(' ', '_')
            
            # 創建保存目錄（如果不存在）
            save_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
            os.makedirs(save_dir, exist_ok=True)
            
            # 保存文件
            file_path = os.path.join(save_dir, secure_filename)
            print(f"正在保存檔案到: {file_path}")
            file.save(file_path)
            
            # 獲取文件大小
            file_size = os.path.getsize(file_path)
            size_display = f"{file_size / 1024 / 1024:.1f} MB" if file_size > 1024 * 1024 else f"{file_size / 1024:.1f} KB"
            
            # 獲取當前日期
            from datetime import datetime
            current_date = datetime.now().strftime("%Y/%m/%d")
            
            # 獲取PDF頁數（如果是PDF文件）
            pages = 1
            if file.filename.lower().endswith('.pdf'):
                try:
                    with open(file_path, 'rb') as pdf_file:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        pages = len(pdf_reader.pages)
                except Exception as e:
                    print(f"無法讀取PDF頁數: {str(e)}")
                    pages = 20  # 如果無法讀取，使用默認值
            elif file.filename.lower().endswith(('.ppt', '.pptx')):
                # 對於PPT文件，目前無法直接讀取頁數，使用默認值
                pages = 20
                # 將PPT轉換為圖片
                pages = convert_ppt_to_images(file_path, len(presentations) + 1)
            
            # 將新教材添加到模擬數據
            if material_type == 'presentation':
                new_id = max([p["id"] for p in presentations]) + 1 if presentations else 1
                new_material = {
                    "id": new_id,
                    "title": title,
                    "filename": secure_filename,
                    "pages": pages,
                    "date": current_date,
                    "size": size_display,
                    "type": "presentation"
                }
                presentations.insert(0, new_material)
                save_data_to_file(PRESENTATIONS_FILE, presentations)
            else:
                # 添加到上傳檔案列表
                new_id = max([u["id"] for u in uploads]) + 1 if uploads else 1
                new_upload = {
                    "id": new_id,
                    "title": title,
                    "filename": secure_filename,
                    "type": material_type,
                    "date": current_date,
                    "size": size_display
                }
                uploads.insert(0, new_upload)
                save_data_to_file(UPLOADS_FILE, uploads)
            
            return jsonify({
                "success": True, 
                "message": "教材上傳成功",
                "file_path": f"/static/uploads/{secure_filename}"
            })
        except Exception as e:
            return jsonify({"success": False, "message": f"檔案保存失敗: {str(e)}"})
    else:
        # 處理影片連結
        video_url = request.form.get('videoUrl')
        if not video_url:
            return jsonify({"success": False, "message": "未提供影片連結"})
        
        # 獲取當前日期
        from datetime import datetime
        current_date = datetime.now().strftime("%Y/%m/%d")
        
        # 在真實應用中，這裡會更新資料庫
        new_id = max([p["id"] for p in presentations]) + 1 if presentations else 1
        new_material = {
            "id": new_id,
            "title": title,
            "filename": "video_link",
            "pages": 1,
            "date": current_date,
            "type": "video",
            "video_url": video_url
        }
        presentations.insert(0, new_material)
        save_data_to_file(PRESENTATIONS_FILE, presentations)
        
        return jsonify({
            "success": True, 
            "message": "影片連結新增成功"
        })

# API 路由
@app.route('/api/generate-text', methods=['POST'])
def generate_text():
    prompt = request.json.get('prompt', '')
    
    # 根據提示詞生成回應
    responses = {
        "介紹": "人工智能（AI）是一門讓機器模擬人類智能的科學與技術。它涵蓋機器學習、深度學習、自然語言處理等多個領域。近年來，AI技術快速發展，已經應用於醫療診斷、自動駕駛、智能助手等多個領域，並持續改變著我們的生活和工作方式。",
        "例子": "AI的實際應用例子：\n1. 醫療保健：輔助醫生診斷疾病，分析醫學圖像\n2. 金融服務：欺詐檢測，算法交易，風險評估\n3. 客戶服務：智能聊天機器人，個性化推薦\n4. 教育：自適應學習系統，智能評分\n5. 交通：自動駕駛車輛，交通流量優化",
        "未來": "AI的未來發展趨勢包括：\n- 更強大的通用人工智能（AGI）\n- 人機協作的深入整合\n- 更加透明和可解釋的AI系統\n- 強化隱私和倫理考量的AI設計\n- AI在氣候變化、醫療突破等全球挑戰中的應用"
    }
    
    response = ""
    for key, value in responses.items():
        if key in prompt:
            response = value
            break
    
    if not response:
        response = f"基於您的提示詞「{prompt}」，AI可以生成多種內容。在實際應用中，這裡會連接到GPT等大型語言模型，提供更加精確和相關的回應。這只是一個示例文本，展示AI文字生成功能的界面交互。"
    
    return jsonify({"text": response})

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    prompt = request.json.get('prompt', '')
    
    # 模擬圖像URL
    categories = ["nature", "city", "tech", "abstract", "people"]
    category = random.choice(categories)
    image_url = f"https://picsum.photos/800/600?category={category}&random={random.randint(1,1000)}"
    
    return jsonify({"image_url": image_url})

@app.route('/api/submit-question', methods=['POST'])
def submit_question():
    name = request.json.get('name', '')
    content = request.json.get('content', '')
    
    # 在真實應用中，會將問題存儲到數據庫
    new_question = {
        "id": len(questions) + 1,
        "name": name,
        "date": "2023/04/11 10:00",  # 應該使用實際時間
        "content": content,
        "answer": None
    }
    
    questions.insert(0, new_question)
    save_data_to_file(QUESTIONS_FILE, questions)
    
    return jsonify({"success": True, "question": new_question})

# 下載簡報
@app.route('/download_presentation/<int:presentation_id>')
def download_presentation(presentation_id):
    presentations = load_data_from_file(PRESENTATIONS_FILE, default_presentations)
    
    # 查找對應ID的簡報
    presentation = None
    for p in presentations:
        if p['id'] == presentation_id:
            presentation = p
            break
    
    # 如果找不到簡報，返回404錯誤
    if not presentation or not presentation.get('filename'):
        return render_template('error.html', message="找不到簡報文件"), 404
    
    # 獲取文件路徑
    file_path = os.path.join(app.static_folder, 'uploads', presentation['filename'])
    
    # 如果文件不存在，返回404錯誤
    if not os.path.exists(file_path):
        return render_template('error.html', message="簡報文件不存在"), 404
    
    # 返回文件下載
    return send_from_directory(
        os.path.join(app.static_folder, 'uploads'),
        presentation['filename'],
        as_attachment=True,
        download_name=presentation['filename']
    )

# 刪除教材
@app.route('/lecturer/delete-material', methods=['POST'])
@login_required
def delete_material():
    data = request.get_json()
    material_id = data.get('id')
    material_type = data.get('type', 'presentation')
    
    if not material_id:
        return jsonify({"success": False, "message": "未提供教材ID"})
    
    try:
        material_id = int(material_id)
        
        # 根據類型選擇要操作的列表
        target_list = presentations if material_type == 'presentation' else uploads
        
        # 尋找要刪除的教材
        material_index = None
        material = None
        for i, item in enumerate(target_list):
            if item['id'] == material_id:
                material_index = i
                material = item
                break
        
        if material_index is None:
            return jsonify({"success": False, "message": "找不到指定的教材"})
        
        # 嘗試刪除實際文件
        if 'filename' in material and material['filename'] != 'video_link':
            file_path = os.path.join(os.path.dirname(__file__), 'static', 'uploads', material['filename'])
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # 從列表中移除
        target_list.pop(material_index)
        
        if material_type == 'presentation':
            save_data_to_file(PRESENTATIONS_FILE, presentations)
        else:
            save_data_to_file(UPLOADS_FILE, uploads)
        
        return jsonify({"success": True, "message": "教材已成功刪除"})
    except Exception as e:
        print(f"刪除教材時發生錯誤: {str(e)}")
        return jsonify({"success": False, "message": f"刪除教材時發生錯誤: {str(e)}"})

# 編輯教材
@app.route('/lecturer/edit-material', methods=['POST'])
@login_required
def edit_material():
    data = request.get_json()
    material_id = data.get('id')
    material_type = data.get('type', 'presentation')
    new_title = data.get('title')
    
    if not material_id or not new_title:
        return jsonify({"success": False, "message": "未提供教材ID或新標題"})
    
    try:
        material_id = int(material_id)
        
        # 根據類型選擇要操作的列表
        target_list = presentations if material_type == 'presentation' else uploads
        
        # 尋找要編輯的教材
        material = None
        for item in target_list:
            if item['id'] == material_id:
                material = item
                break
        
        if material is None:
            return jsonify({"success": False, "message": "找不到指定的教材"})
        
        # 更新標題
        material['title'] = new_title
        
        if material_type == 'presentation':
            save_data_to_file(PRESENTATIONS_FILE, presentations)
        else:
            save_data_to_file(UPLOADS_FILE, uploads)
        
        return jsonify({"success": True, "message": "教材標題已更新"})
    except Exception as e:
        print(f"編輯教材時發生錯誤: {str(e)}")
        return jsonify({"success": False, "message": f"編輯教材時發生錯誤: {str(e)}"})

@app.route('/get_slide_image/<presentation_id>/<page_number>')
def get_slide_image(presentation_id, page_number):
    """獲取特定簡報的特定頁面圖片，用於全螢幕模式下的AJAX請求"""
    try:
        # 獲取簡報信息
        presentation = get_presentation_by_id(presentation_id)
        if not presentation:
            return jsonify({'success': False, 'error': '找不到簡報'})
        
        # 檢查頁碼是否有效
        page_number = int(page_number)
        if page_number < 1 or page_number > presentation.pages:
            return jsonify({'success': False, 'error': '頁碼超出範圍'})
        
        # 構建圖片URL
        image_url = f'/static/slides/presentation-{presentation_id}/slide-{page_number}.png'
        
        return jsonify({
            'success': True, 
            'image_url': image_url,
            'current_page': page_number,
            'total_pages': presentation.pages
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.before_request
def load_lecturer_info():
    # 跳過靜態文件請求
    if request.path.startswith('/static/'):
        return
    
    # 只在未設置講師資料但已經登入的情況下載入持久化資料
    if 'lecturer_username' in session and ('lecturer_name' not in session or 'lecturer_title' not in session or 'lecturer_email' not in session):
        # 嘗試從配置文件讀取講師資料
        config_path = os.path.join(os.path.dirname(__file__), 'static', 'config', 'lecturer_info.json')
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    # 如果配置文件中有講師資料，則載入到session
                    if 'lecturer_name' in config:
                        session['lecturer_name'] = config.get('lecturer_name')
                    if 'lecturer_title' in config:
                        session['lecturer_title'] = config.get('lecturer_title')
                    if 'lecturer_email' in config:
                        session['lecturer_email'] = config.get('lecturer_email')
                    print("已從配置文件載入講師資料")
            except Exception as e:
                print(f"載入講師資料時發生錯誤: {str(e)}")

if __name__ == '__main__':
    # 確保資料夾存在
    os.makedirs('static/downloads', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=8080)