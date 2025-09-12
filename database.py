import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        """เชื่อมต่อกับ MongoDB Atlas"""
        try:
            # ใช้ MONGODB_URI จากไฟล์ .env
            uri = os.environ.get("MONGODB_URI")
            if not uri:
                print("MONGODB_URI not found in environment variables")
                return False

            print(f"Attempting to connect to MongoDB...")
            
            # แก้ไข URI หากมี username/password ที่ต้อง encode
            if "mongodb+srv://" in uri and "@" in uri:
                # แยก URI ออกเป็นส่วน ๆ
                parts = uri.split("//")[1]  # ตัด mongodb+srv:// ออก
                if "@" in parts:
                    auth_and_host = parts.split("@")
                    if len(auth_and_host) == 2 and ":" in auth_and_host[0]:
                        username, password = auth_and_host[0].split(":", 1)
                        encoded_username = urllib.parse.quote_plus(username)
                        encoded_password = urllib.parse.quote_plus(password)
                        # แยก host และ parameters
                        host_and_params = auth_and_host[1]
                        uri = f"mongodb+srv://{encoded_username}:{encoded_password}@{host_and_params}"

            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.db = self.client.kanrawee_db
            
            # ทดสอบการเชื่อมต่อ
            self.client.admin.command('ping')
            print("Connected to MongoDB successfully")
            return True
            
        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            print("Suggestion: Check your MongoDB Atlas credentials and IP whitelist")
            print("💡 App will use JSON fallback mode")
            return False

    def get_emotion_history(self, user_id, days=90):
        """ดึงประวัติอารมณ์ของ user ใน N วันที่ผ่านมา"""
        try:
            if not self.client or self.db is None:
                return []

            collection = self.db.emotion_history
            
            # คำนวณวันที่เริ่มต้น
            start_date = datetime.now() - timedelta(days=days-1)
            start_date_str = start_date.strftime("%Y-%m-%d")
            
            # ค้นหาข้อมูลของ user ที่มีวันที่ในช่วงที่กำหนด
            query = {
                "user_id": str(user_id),  # แน่ใจว่าเป็น string
                "date": {"$gte": start_date_str}
            }
            
            # เรียงตามวันที่ใหม่ไปเก่า
            results = list(collection.find(query, {"_id": 0}).sort("date", -1))
            
            # จัดการข้อมูลเก่าที่อาจไม่มี emotion และ summary fields
            processed_results = []
            for entry in results:
                # ถ้าไม่มี emotion หรือ summary field ให้ใช้ค่า default
                if 'emotion' not in entry and entry.get('analysis'):
                    entry['emotion'] = entry.get('analysis', 'N/A')[:50] + "..."  # ตัดสั้น
                elif 'emotion' not in entry:
                    entry['emotion'] = 'N/A'
                    
                if 'summary' not in entry and entry.get('analysis'):
                    entry['summary'] = entry.get('analysis', 'N/A')[:100] + "..."  # ตัดสั้น
                elif 'summary' not in entry:
                    entry['summary'] = 'N/A'
                    
                processed_results.append(entry)
            
            print(f"📊 Found {len(processed_results)} emotion entries for user {user_id} in last {days} days")
            return processed_results
            
        except Exception as e:
            print(f"❌ Error fetching emotion history: {e}")
            return []

    def save_emotion_entry(self, user_id, entry_data):
        """บันทึกข้อมูลอารมณ์ของ user"""
        try:
            if not self.client or self.db is None:
                return False

            collection = self.db.emotion_history
            
            # เพิ่ม user_id และ timestamp
            entry_data['user_id'] = str(user_id)  # แน่ใจว่าเป็น string
            entry_data['created_at'] = datetime.utcnow()
            
            # บันทึกลงฐานข้อมูล
            result = collection.insert_one(entry_data)
            print(f"✅ Emotion entry saved for user {user_id} with ID: {result.inserted_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving emotion entry: {e}")
            return False

    def get_user_stats(self, user_id, days=90):
        """คำนวณสถิติอารมณ์ของ user"""
        try:
            history = self.get_emotion_history(str(user_id), days)
            
            if not history:
                return {
                    "total_entries": 0,
                    "average_score": 0,
                    "highest_score": 0,
                    "lowest_score": 0,
                    "days_with_entries": 0,
                    "most_common_emotion": "N/A"
                }

            scores = [entry.get("emotionScore", 0) for entry in history if isinstance(entry.get("emotionScore"), (int, float))]
            emotions = [entry.get("emotion", "") for entry in history if entry.get("emotion")]
            unique_dates = set(entry.get("date", "") for entry in history if entry.get("date"))
            
            # หาอารมณ์ที่พบบ่อยที่สุด
            most_common_emotion = "N/A"
            if emotions:
                emotion_counts = {}
                for emotion in emotions:
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                most_common_emotion = max(emotion_counts.keys(), key=lambda x: emotion_counts[x])
            
            return {
                "total_entries": len(history),
                "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
                "highest_score": max(scores) if scores else 0,
                "lowest_score": min(scores) if scores else 0,
                "days_with_entries": len(unique_dates),
                "most_common_emotion": most_common_emotion
            }
            
        except Exception as e:
            print(f"❌ Error calculating user stats: {e}")
            return {
                "total_entries": 0,
                "average_score": 0,
                "highest_score": 0,
                "lowest_score": 0,
                "days_with_entries": 0,
                "most_common_emotion": "N/A"
            }

    def migrate_json_data(self, json_file_path):
        """ย้ายข้อมูลจาก JSON file ไปยัง MongoDB (ใช้ครั้งเดียว)"""
        try:
            import json
            
            if not os.path.exists(json_file_path):
                print(f"❌ JSON file not found: {json_file_path}")
                return False

            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not self.client or self.db is None:
                return False

            collection = self.db.emotion_history
            migrated_count = 0

            # ถ้าข้อมูลเป็น dict (แยกตาม user)
            if isinstance(data, dict):
                for user_id, entries in data.items():
                    for entry in entries:
                        entry['user_id'] = user_id
                        entry['created_at'] = datetime.utcnow()
                        collection.insert_one(entry)
                        migrated_count += 1

            # ถ้าข้อมูลเป็น list (รูปแบบเก่า)
            elif isinstance(data, list):
                for entry in data:
                    entry['user_id'] = "1"  # กำหนดให้ user id เริ่มต้น
                    entry['created_at'] = datetime.utcnow()
                    collection.insert_one(entry)
                    migrated_count += 1

            print(f"✅ Migrated {migrated_count} emotion entries to MongoDB")
            return True

        except Exception as e:
            print(f"❌ Error migrating JSON data: {e}")
            return False

    def get_user_by_id(self, user_id):
        """ดึงข้อมูล user ตาม ID"""
        try:
            if not self.client or self.db is None:
                return None

            collection = self.db.users
            user_data = collection.find_one({"user_id": user_id}, {"_id": 0})
            return user_data
            
        except Exception as e:
            print(f"❌ Error fetching user by ID: {e}")
            return None

    def get_user_by_username(self, username):
        """ดึงข้อมูล user ตาม username"""
        try:
            if not self.client or self.db is None:
                return None

            collection = self.db.users
            user_data = collection.find_one({"username": username}, {"_id": 0})
            return user_data
            
        except Exception as e:
            print(f"❌ Error fetching user by username: {e}")
            return None

    def create_user(self, user_id, username, hashed_password):
        """สร้าง user ใหม่"""
        try:
            if not self.client or self.db is None:
                return False

            collection = self.db.users
            
            # ตรวจสอบว่า username ซ้ำหรือไม่
            if self.get_user_by_username(username):
                print(f"⚠️ Username '{username}' already exists")
                return False
            
            user_data = {
                "user_id": user_id,
                "username": username,
                "password": hashed_password,
                "created_at": datetime.utcnow(),
                "last_login": None
            }
            
            result = collection.insert_one(user_data)
            print(f"✅ User created successfully: {username} (ID: {result.inserted_id})")
            return True
            
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            return False

    def update_last_login(self, user_id):
        """อัพเดทเวลาล็อกอินล่าสุด"""
        try:
            if not self.client or self.db is None:
                return False

            collection = self.db.users
            result = collection.update_one(
                {"user_id": user_id},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            return result.modified_count > 0
            
        except Exception as e:
            print(f"❌ Error updating last login: {e}")
            return False

    def get_all_users(self):
        """ดึงข้อมูล user ทั้งหมด (สำหรับ debug)"""
        try:
            if not self.client or self.db is None:
                return []

            collection = self.db.users
            users = list(collection.find({}, {"_id": 0}))
            return users
            
        except Exception as e:
            print(f"❌ Error fetching all users: {e}")
            return []

    def migrate_users_to_mongodb(self, in_memory_users):
        """ย้าย users จาก in-memory ไป MongoDB (ใช้ครั้งเดียว)"""
        try:
            if not self.client or self.db is None:
                return False

            collection = self.db.users
            migrated_count = 0

            for user_id, user in in_memory_users.items():
                # ตรวจสอบว่ามี user นี้ใน MongoDB แล้วหรือไม่
                existing_user = self.get_user_by_id(user_id)
                if not existing_user:
                    user_data = {
                        "user_id": user_id,
                        "username": user.username,
                        "password": user.password,
                        "created_at": datetime.utcnow(),
                        "last_login": None
                    }
                    collection.insert_one(user_data)
                    migrated_count += 1

            print(f"✅ Migrated {migrated_count} users to MongoDB")
            return True

        except Exception as e:
            print(f"❌ Error migrating users: {e}")
            return False

# สร้าง instance เดียวใช้ทั่วทั้งแอป
mongodb = MongoDB()
