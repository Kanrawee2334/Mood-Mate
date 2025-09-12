# วิธีตั้งค่า MongoDB สำหรับ Kanrawee Project

## ตัวเลือก 1: MongoDB Atlas (Cloud - แนะนำ)

1. ไปที่ https://www.mongodb.com/atlas/database
2. สมัครบัญชีฟรี (Free Tier)
3. สร้าง Cluster ใหม่
4. ตั้งค่า Database Access:
   - สร้าง Database User
   - จดชื่อผู้ใช้และรหัสผ่าน
5. ตั้งค่า Network Access:
   - เพิ่ม IP Address: 0.0.0.0/0 (Allow access from anywhere)
6. ได้ Connection String แบบนี้:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/kanrawee_db?retryWrites=true&w=majority
   ```
7. แทนที่ <username> และ <password> ด้วยข้อมูลจริง
8. อัพเดตใน .env:
   ```
   MONGODB_URI=mongodb+srv://your_username:your_password@cluster0.xxxxx.mongodb.net/kanrawee_db?retryWrites=true&w=majority
   ```

## ตัวเลือก 2: MongoDB Local

1. ดาวน์โหลด MongoDB Community Server จาก https://www.mongodb.com/try/download/community
2. ติดตั้งและเริ่มต้น MongoDB service
3. ใช้ URI ในไฟล์ .env:
   ```
   MONGODB_URI=mongodb://localhost:27017/kanrawee_db
   ```

## ตัวเลือก 3: Docker (สำหรับ Developer)

```bash
docker run -d --name kanrawee-mongo -p 27017:27017 mongo:latest
```

จากนั้นใช้:
```
MONGODB_URI=mongodb://localhost:27017/kanrawee_db
```

## การทดสอบ Connection

หลังจากตั้งค่าแล้ว รันคำสั่งนี้เพื่อทดสอบ:

```bash
python -c "from database import mongodb; print('Connection test:', mongodb.client is not None)"
```

## Migration ข้อมูลเก่า

เมื่อรันแอปครั้งแรก ระบบจะย้ายข้อมูลจาก `emotion_history.json` ไป MongoDB อัตโนมัติ
ไฟล์เก่าจะถูกเปลี่ยนชื่อเป็น `emotion_history.json.backup`
