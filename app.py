import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
from database import mongodb

# โหลด .env (ใน Railway จะใช้ Environment Variables แทนไฟล์ .env ก็ได้)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'signin'  # type: ignore

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# ตั้งค่า Gemini API
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])  # type: ignore
    model = genai.GenerativeModel('gemini-2.0-flash')  # type: ignore
except KeyError:
    model = None
    print("❌ GEMINI_API_KEY not found")
except Exception as e:
    model = None
    print(f"❌ Error configuring Gemini API: {e}")

# ประเมินความเสี่ยงซึมเศร้า
def evaluate_depression_risk(avg_score):
    if avg_score < 20:
        return {
            "level": "สูง",
            "message": "คะแนนอารมณ์ต่ำมาก แสดงว่ามีความเสี่ยงสูงที่จะเป็นภาวะซึมเศร้า ควรรีบพบผู้เชี่ยวชาญหรือนักจิตวิทยา"
        }
    elif avg_score < 40:
        return {
            "level": "ปานกลาง",
            "message": "คะแนนอารมณ์อยู่ในระดับปานกลาง อาจมีความเครียดหรือวิตกกังวล ควรดูแลสุขภาพจิตอย่างใกล้ชิด"
        }
    elif avg_score < 60:
        return {
            "level": "เล็กน้อย",
            "message": "คะแนนอารมณ์อยู่ในระดับพึ่งเริ่ม เข้าค่ายที่จะเป็นภาวะซึมเศร้า อาจมีความเครียดหรือวิตกกังวล"
        }
    else:
        return {
            "level": "ปกติ",
            "message": "คะแนนอารมณ์อยู่ในระดับปกติ ไม่มีความเสี่ยงซึมเศร้าในระดับน่ากังวล"
        }

# หน้าแรก
@app.route("/")
@login_required
def index():
    return render_template("index.html", user=current_user)

# วิเคราะห์อารมณ์
@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    if not model:
        return jsonify({"error": "Gemini API is not configured."}), 500

    data = request.get_json()
    message = data.get("message", "").strip() if data else ""
    emoji = data.get("emoji", "").strip() if data else ""

    if not message:
        return jsonify({"error": "Missing message"}), 400
    if not emoji:
        return jsonify({"error": "Missing emoji"}), 400

    prompt = f"""
    วิเคราะห์ข้อความและอีโมจิต่อไปนี้ แล้วตอบกลับเป็น JSON object เท่านั้น ห้ามมีข้อความอื่นนอกเหนือจาก JSON
    ข้อความ: "{message}"
    อีโมจิ: {emoji}

    หน้าที่ของคุณ:
    1.  `emotion`: ระบุอารมณ์หลักของข้อความเป็นภาษาไทย (เช่น "มีความสุข", "เศร้า", "โกรธ").
    2.  `summary`: สรุปใจความสำคัญของข้อความสั้นๆ เป็นภาษาไทย.
    3.  `emotionScore`: ให้คะแนนอารมณ์จาก 0 ถึง 100 (0 คือแง่ลบสุดๆ, 100 คือแง่บวกสุดๆ).

    ตัวอย่าง JSON output ที่ต้องการ:
    {{
      "emotion": "มีความสุข",
      "summary": "ผู้เขียนรู้สึกดีใจที่ได้ไปเที่ยวทะเลกับเพื่อนๆ",
      "emotionScore": 95
    }}

    วิเคราะห์ข้อมูลต่อไปนี้และสร้าง JSON object ตามรูปแบบที่กำหนด:
    """

    try:
        response = model.generate_content(prompt)
        cleaned = response.text.strip().replace("```json", "").replace("```", "").strip()
        ai_result = json.loads(cleaned)

        entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "message": message,
            "emoji": emoji,
            "emotion": ai_result.get("emotion", "N/A"),
            "summary": ai_result.get("summary", "N/A"),
            "emotionScore": ai_result.get("emotionScore", 50),
        }
        return jsonify(entry)

    except Exception as e:
        return jsonify({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "message": message,
            "emoji": emoji,
            "emotion": "ไม่สามารถวิเคราะห์ได้",
            "summary": f"เกิดข้อผิดพลาดในการสื่อสารกับ AI: {e}",
            "emotionScore": 50,
        }), 500

# บันทึกข้อมูล
@app.route("/save", methods=["POST"])
@login_required
def save_entry():
    entry = request.get_json()
    if not isinstance(entry, dict) or not entry.get("message") or not entry.get("emoji"):
        return jsonify({"error": "Invalid or incomplete entry data"}), 400

    entry['date'] = datetime.now().strftime("%Y-%m-%d")
    
    # สร้าง entry ที่ปลอดภัยสำหรับ JSON response (ไม่มี ObjectId)
    safe_entry = {
        'message': entry.get('message'),
        'emoji': entry.get('emoji'),
        'date': entry['date'],
        'emotionScore': entry.get('emotionScore', 0),
        'emotion': entry.get('emotion', 'N/A'),
        'summary': entry.get('summary', 'N/A'),
        'analysis': entry.get('analysis', ''),
        'user_id': str(current_user.id)
    }
    
    # ลองบันทึกลง MongoDB ก่อน
    if mongodb.client:
        success = mongodb.save_emotion_entry(current_user.id, entry)
        if success:
            return jsonify({"status": "saved", "entry": safe_entry})
    
    # หาก MongoDB ไม่พร้อม ให้ return error
    return jsonify({"error": "Database connection failed. Please try again later."}), 500

@app.route('/generate', methods=["POST"])
@login_required
def generate_text():
    try:
        if not model:
            return jsonify({'error': 'Gemini API is not configured.'}), 500
            
        data = request.get_json()
        prompt = data.get('prompt') if data else None
        if not prompt:
            return jsonify({'error': 'Prompt is missing.'}), 400
        response = model.generate_content(prompt)
        return jsonify({'response': response.text})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'Failed to generate response from the model.'}), 500

# ประวัติย้อนหลัง 90 วัน
@app.route("/history90")
@login_required
def history90():
    # ดึงข้อมูลจาก MongoDB
    if mongodb.client:
        history = mongodb.get_emotion_history(current_user.id, days=90)
    else:
        # หาก MongoDB ไม่พร้อม ให้ return empty data
        return jsonify({"history90": [], "averageScore": 0, "risk": evaluate_depression_risk(0)})
    
    if not history:
        return jsonify({"history90": [], "averageScore": 0, "risk": evaluate_depression_risk(0)})

    # คำนวณคะแนนเฉลี่ย
    total_score = sum(entry.get("emotionScore", 0) for entry in history if isinstance(entry, dict))
    avg_score = total_score / len(history) if history else 0
    risk = evaluate_depression_risk(avg_score)

    return jsonify({
        "history90": history,
        "averageScore": avg_score,
        "risk": risk,
    })

# ประเมินความเสี่ยงด้วย AI
@app.route('/evaluate_depression', methods=['POST'])
@login_required
def evaluate_depression_with_ai():
    if not model:
        return jsonify({"error": "Gemini API is not configured."}), 500

    # 1. ดึงข้อมูลประวัติทั้งหมดของผู้ใช้
    if mongodb.client:
        history = mongodb.get_emotion_history(current_user.id, days=90) # ดึงข้อมูล 90 วัน
    else:
        return jsonify({
            "risk": "ไม่สามารถประเมินได้",
            "reason": "ไม่สามารถเชื่อมต่อฐานข้อมูลได้",
            "advice": "กรุณาลองใหม่อีกครั้งในภายหลัง"
        })

    if not history:
        return jsonify({
            "risk": "ไม่สามารถประเมินได้",
            "reason": "ไม่มีข้อมูลประวัติเพียงพอที่จะนำมาวิเคราะห์",
            "advice": "กรุณาเริ่มบันทึกอารมณ์ของคุณก่อน แล้วลองประเมินอีกครั้ง"
        })

    # 2. อ่าน Prompt จากไฟล์ anaprompt.md
    try:
        with open("anaprompt.md", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        return jsonify({"error": "Prompt file (anaprompt.md) not found."}), 500

    # 3. สร้าง safe history data สำหรับ JSON serialization
    safe_history = []
    
    # Debug: ตรวจสอบประเภทข้อมูลใน history
    print(f"🔍 History type: {type(history)}, Length: {len(history) if history else 'None'}")
    if history and isinstance(history, list):
        for i, entry in enumerate(history[:3]):  # ตรวจสอบแค่ 3 entries แรก
            print(f"🔍 Entry {i}: type={type(entry)}, keys={list(entry.keys()) if isinstance(entry, dict) else 'Not a dict'}")
            if isinstance(entry, dict):
                for key, value in entry.items():
                    if hasattr(value, '__class__') and 'datetime' in str(type(value)):
                        print(f"⚠️  Found datetime in {key}: {type(value)} - {value}")
    
    for entry in history:
        # ตรวจสอบว่า entry เป็น dict หรือไม่
        if not isinstance(entry, dict):
            print(f"⚠️  Skipping invalid entry (not a dict): {type(entry)} - {entry}")
            continue
        
        # Debug: ตรวจสอบทุก field ใน entry
        for key, value in entry.items():
            if hasattr(value, '__class__') and ('datetime' in str(type(value)) or 'ObjectId' in str(type(value))):
                print(f"⚠️  Problematic field {key}: {type(value)} - {value}")
        
        # แปลง date field ให้เป็น string ถ้าเป็น datetime object
        date_value = entry.get('date')
        if isinstance(date_value, datetime):
            date_value = date_value.strftime("%Y-%m-%d")
        elif date_value is None:
            date_value = datetime.now().strftime("%Y-%m-%d")
        
        # สร้าง safe_entry โดยแปลงทุก field เป็น string หรือ primitive types เท่านั้น
        safe_entry = {
            'message': str(entry.get('message', '')),
            'emoji': str(entry.get('emoji', '')),
            'date': str(date_value),
            'emotionScore': int(entry.get('emotionScore', 0)) if isinstance(entry.get('emotionScore'), (int, float)) else 0,
            'emotion': str(entry.get('emotion', 'N/A')),
            'summary': str(entry.get('summary', 'N/A')),
            'analysis': str(entry.get('analysis', '')),
        }
        safe_history.append(safe_entry)
    
    # 4. สร้าง Prompt ที่สมบูรณ์
    try:
        history_json_str = json.dumps(safe_history, ensure_ascii=False, indent=2)
        print(f"✅ Successfully serialized {len(safe_history)} entries to JSON")
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        print(f"🔍 Safe history sample: {safe_history[:2] if safe_history else 'Empty'}")
        return jsonify({
            "risk": "ข้อผิดพลาด",
            "reason": "เกิดข้อผิดพลาดในการประมวลผลข้อมูลประวัติ",
            "advice": f"รายละเอียด: {str(e)}"
        }), 500
        
    full_prompt = f"{prompt_template}\n\nข้อมูลผู้ใช้:\n{history_json_str}"

    # 5. เรียก Gemini API
    try:
        response = model.generate_content(full_prompt)
        cleaned = response.text.strip().replace("```json", "").replace("```", "").strip()
        ai_result = json.loads(cleaned)
        return jsonify(ai_result)

    except Exception as e:
        print(f"❌ AI Evaluation Error: {e}")
        return jsonify({
            "risk": "ข้อผิดพลาด",
            "reason": "เกิดข้อผิดพลาดในการสื่อสารกับ AI หรือการประมวลผลข้อมูล",
            "advice": f"รายละเอียด: {str(e)}"
        }), 500


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # ตรวจสอบว่า username ซ้ำหรือไม่
        existing_user = User.get_by_username(username)
        if existing_user:
            flash('Username already exists.')
            return redirect(url_for('signup'))
        
        # สร้าง user ใหม่
        user = User.create(username, password)
        if user:
            flash('Account created successfully. Please sign in.')
            return redirect(url_for('signin'))
        else:
            flash('Error creating account. Please try again.')
            return redirect(url_for('signup'))
    
    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.get_by_username(username)
        if user and check_password_hash(user.password, password):
            login_user(user)
            # อัพเดทเวลาล็อกอินล่าสุดใน MongoDB
            if mongodb.client:
                mongodb.update_last_login(user.id)
            return redirect(url_for('index'))
        flash('Invalid username or password.')
    return render_template('signin.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('signin'))

# Debug route - ลบได้เมื่อไม่ต้องการ
@app.route('/debug/users')
def debug_users():
    """แสดงรายชื่อ users ทั้งหมด (สำหรับ debug)"""
    if mongodb.client:
        users_list = mongodb.get_all_users()
        return jsonify({
            "total_users": len(users_list),
            "users": users_list
        })
    else:
        return jsonify({
            "error": "Database not available",
            "total_users": 0,
            "users": []
        })

# รันแอป
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)