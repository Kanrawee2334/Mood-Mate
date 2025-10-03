# Kanrawee — ไฟล์สรุปโครงการ

ไฟล์นี้รวมคำอธิบายสั้น ๆ ของไฟล์และโฟลเดอร์สำคัญในโปรเจกต์ Kanrawee เพื่อช่วยให้เข้าใจหน้าที่ของแต่ละไฟล์อย่างรวดเร็ว

## บทสรุปโปรเจกต์
- เว็บแอป Flask สำหรับวิเคราะห์อารมณ์ภาษาไทยโดยใช้ Google Gemini (google-generativeai)
- เก็บข้อมูลผู้ใช้และประวัติอารมณ์ด้วย MongoDB Atlas เป็นหลัก และมี `emotion_history.json` เป็น fallback เมื่อ MongoDB ไม่พร้อม
- ใช้ Flask-Login สำหรับการยืนยันตัวตน และมี frontend แบบ vanilla JS (fetch API)

## คำอธิบายไฟล์สำคัญ

- `app.py`
  - แอปหลักของ Flask: กำหนด route ทั้งหมด (เช่น `/`, `/analyze`, `/save`, `/history90`, `/signin`, `/signup`, `/logout`), รวมการเรียกใช้งาน Gemini AI, การตรวจสอบผู้ใช้ และการจัดการข้อมูล (MongoDB/JSON fallback).

- `database.py`
  - โมดูลเชื่อมต่อ MongoDB Atlas: สร้าง client, จัดการการเข้ารหัส URL ของ credential, ตั้งค่า timeout และมี logic fallback ไปยังไฟล์ JSON เมื่อเชื่อมต่อไม่สำเร็จ; ให้ฟังก์ชันระดับข้อมูล (CRUD) ที่ `app.py` เรียกใช้.

- `models.py`
  - โมเดลผู้ใช้สำหรับ Flask-Login: นิยามคลาส `User`, loader function และ logic สำหรับจัดเก็บ/เรียกข้อมูลผู้ใช้จาก MongoDB หรือ fallback; รวมการตรวจสอบรหัสผ่าน (hashing) และข้อมูล session.

- `emotion_history.json`
  - ไฟล์ fallback เก็บประวัติอารมณ์ตาม `user_id` เมื่อ MongoDB ไม่พร้อมใช้งาน; โค้ดรองรับการย้ายข้อมูลจากรูปแบบเก่า (legacy) และรับประกันการแยกข้อมูลของผู้ใช้.

- `templates/index.html`
  - หน้าแดชบอร์ดหลัก: UI เลือกอิโมจิ ป้อนข้อความอารมณ์ และแสดงผลการวิเคราะห์จาก AI แบบเรียลไทม์ (frontend JS ทำ fetch ไปยัง `/analyze` แล้ว `/save`).

- `templates/signin.html`
  - หน้าเข้าสู่ระบบ (form) สำหรับผู้ใช้ที่มีอยู่.

- `templates/signup.html`
  - หน้าแบบฟอร์มลงทะเบียนผู้ใช้ใหม่ และตรวจสอบ username ซ้ำ.

- `Procfile`
  - กำหนดคำสั่งรันเมื่อติดตั้งบนแพลตฟอร์ม (Heroku/Railway ฯลฯ). หมายเหตุ: ใน repo นี้ `Procfile` ถูกตั้งให้ใช้ `uvicorn` ซึ่งไม่ตรงกับ Flask (WSGI) — ควรเปลี่ยนเป็น `web: python app.py` เมื่อ deploy.

- `requirements.txt`
  - รายการ dependencies ของ Python (เช่น Flask, pymongo, flask-login, google-generativeai ฯลฯ) สำหรับติดตั้งใน virtualenv.

- `start.bat`
  - สคริปต์ Windows สำหรับสตาร์ทสภาพแวดล้อมการพัฒนา (มัก activate venv แล้วรัน `python app.py`).

- `ngrokstart.bat`
  - สคริปต์ช่วยสตาร์ท ngrok เพื่อเปิดพอร์ตแอปให้เข้าถึงจากภายนอกขณะทดสอบ.

- `BATCH_SCRIPTS.md`
  - อธิบายวิธีใช้งานสคริปต์ .bat ที่มาพร้อมโปรเจกต์ (เช่น setup, run_dev, test_system, db_manager).

- `ARCHITECTURE.md`
  - เอกสารสถาปัตยกรรมโปรเจกต์: อธิบายโครงสร้าง (MongoDB + JSON fallback, AI integration, user isolation, routes, data-flow) และข้อควรระวังสำหรับ production.

- `MONGODB_SETUP.md`
  - คำแนะนำการตั้งค่า MongoDB Atlas และการเตรียมตัวแปรสภาพแวดล้อม (`MONGODB_URI`).

- `anaprompt.md`
  - ข้อความ prompt ที่ใช้กับ Gemini AI เป็นภาษาไทย พร้อมข้อกำหนดให้ตอบเป็น JSON เข้มงวด (ฟิลด์ `emotion`, `summary`, `emotionScore`).

- `about.md`
  - คำอธิบายสั้น ๆ ของโปรเจกต์และวัตถุประสงค์หลัก.

- `howto.png`
  - ภาพประกอบการใช้งาน UI หรือไดอะแกรมการทำงานเล็ก ๆ ที่ช่วยอธิบายฟลูว์.

- `__pycache__/`
  - โฟลเดอร์เก็บไฟล์ .pyc (ไฟล์ไบต์คอมไพล์ของ Python) — ไม่ควรแก้ไขและมักจะอยู่ใน `.gitignore`.


## ข้อควรระวังและคำแนะนำสั้น ๆ
- อย่า commit คีย์/ความลับ (เช่น `GEMINI_API_KEY`, `MONGODB_URI`, `SECRET_KEY`) ลงใน repo — ให้ใช้ environment variables หรือไฟล์ `.env` ที่ไม่ถูก commit.
- ทุก route ที่เข้าถึงข้อมูลผู้ใช้ควรใช้ `str(current_user.id)` เพื่อแยกข้อมูลของผู้ใช้แต่ละคนอย่างเคร่งครัด.
- ตรวจสอบ `Procfile` ก่อน deploy — เปลี่ยนเป็น `web: python app.py` สำหรับ Flask.
- หากต้องการเก็บระยะยาว ควรพิจารณากลยุทธ์ archival สำหรับ `emotion_history.json` เพราะไฟล์จะโตขึ้นเรื่อย ๆ ถ้าใช้เป็น storage หลักใน fallback mode.

## รันแบบพัฒนาบน Windows (PowerShell)
ตัวอย่างคำสั่งที่มักใช้ (รันในโฟลเดอร์โปรเจกต์):

```powershell
# เปิด virtualenv (ถ้ามี)
& .\.venv\Scripts\Activate.ps1

# ติดตั้ง dependencies (ครั้งแรก)
pip install -r requirements.txt

# รันแอป
python app.py
```

หมายเหตุ: ถ้ามี `start.bat` หรือ `run_dev.bat` คุณสามารถรันสคริปต์เหล่านั้นเพื่อ activate venv และรันเซิร์ฟเวอร์อัตโนมัติได้

---

ถ้าต้องการ ผมช่วยทำได้เพิ่มเติมดังนี้:
- แก้ `Procfile` ให้ตรงกับ Flask
- สร้างจริง ๆ `README.md` แบบเต็ม (ภาษาไทย/อังกฤษ) บนพื้นฐานข้อความนี้
- เปิดดู `start.bat` แล้วอธิบายทีละบรรทัดหรือปรับให้ใช้งานได้






