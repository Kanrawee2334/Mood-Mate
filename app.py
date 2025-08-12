import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder="templates")

# Configure the Gemini API
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.0-flash')
except KeyError:
    model = None
    print("ข้อผิดพลาด: ไม่พบ GEMINI_API_KEY ในไฟล์ .env")
except Exception as e:
    model = None
    print(f"เกิดข้อผิดพลาดในการตั้งค่า Gemini API: {e}")


DATA_FILE = "emotion_history.json"

def load_history():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            # Check if file is empty
            content = f.read()
            if not content:
                return []
            return json.loads(content)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        # If the file contains invalid JSON, treat as empty
        return []

def save_history(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
            "message": "คะแนนอารมณ์อยู่ในระดับพึ่งเริ่ม เข้าค่ายที่จะเป็นภาวะซึมเศร้า อาจมีความเครียดหรือวิตกกังวล "
        }
    else:
        return {
            "level": "ปกติ",
            "message": "คะแนนอารมณ์อยู่ในระดับปกติ ไม่มีความเสี่ยงซึมเศร้าในระดับน่ากังวล"
        }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if not model:
        return jsonify({"error": "Gemini API is not configured."}), 500

    data = request.get_json()
    message = data.get("message", "").strip()
    emoji = data.get("emoji", "").strip()

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
        # Clean up the response to get only the JSON part
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        ai_result = json.loads(cleaned_response)

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
        print(f"Error calling Gemini API or parsing JSON: {e}")
        # Fallback to a mock response in case of AI failure
        fallback_entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "message": message,
            "emoji": emoji,
            "emotion": "ไม่สามารถวิเคราะห์ได้",
            "summary": f"เกิดข้อผิดพลาดในการสื่อสารกับ AI: {e}",
            "emotionScore": 50,
        }
        return jsonify(fallback_entry), 500


@app.route("/save", methods=["POST"])
def save_entry():
    entry = request.get_json()

    # Validate the received data
    if not isinstance(entry, dict) or not entry.get("message") or not entry.get("emoji"):
        return jsonify({"error": "Invalid or incomplete entry data"}), 400

    # Ensure the date is the server's current date upon saving
    entry['date'] = datetime.now().strftime("%Y-%m-%d")

    history = load_history()

    # Ensure history is a list before appending
    if not isinstance(history, list):
        history = []

    history.append(entry)
    save_history(history)

    return jsonify({"status": "saved", "entry": entry})

@app.route("/history")
def history():
    history = load_history()
    if not isinstance(history, list):
        history = [] # Ensure it's a list if file is corrupted
    history_sorted = sorted(history, key=lambda x: x.get("date", ""), reverse=True)
    last_30 = history_sorted[:30]
    return jsonify(last_30)

@app.route("/history7")
def history7():
    history = load_history()
    if not isinstance(history, list):
        history = [] # Ensure it's a list if file is corrupted

    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=6)

    filtered = []
    for entry in history:
        try:
            entry_date = datetime.strptime(entry.get("date", ""), "%Y-%m-%d").date()
            if seven_days_ago <= entry_date <= today:
                filtered.append(entry)
        except (ValueError, TypeError):
            # Skip entries with invalid date format or missing date
            continue

    if not filtered:
        return jsonify({"history7": [], "averageScore": 0, "risk": evaluate_depression_risk(0)})

    total_score = sum(entry.get("emotionScore", 0) for entry in filtered)
    avg_score = total_score / len(filtered) if filtered else 0
    risk = evaluate_depression_risk(avg_score)

    return jsonify({
        "history7": filtered,
        "averageScore": avg_score,
        "risk": risk,
    })

if __name__ == "__main__":
    if not model:
        print("="*50)
        print("ไม่สามารถเริ่มเซิร์ฟเวอร์ได้ กรุณาตรวจสอบการตั้งค่า API Key")
        print("="*50)
    else:
        app.run(debug=True, port=5000)
