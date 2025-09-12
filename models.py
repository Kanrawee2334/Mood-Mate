from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get(user_id):
        """ดึง user จาก MongoDB"""
        from database import mongodb
        
        if mongodb.client:
            user_data = mongodb.get_user_by_id(user_id)
            if user_data:
                return User(
                    user_data['user_id'],
                    user_data['username'], 
                    user_data['password']
                )
        # หาก MongoDB ไม่พร้อม ให้ return None
        return None

    @staticmethod
    def get_by_username(username):
        """ดึง user ตาม username จาก MongoDB"""
        from database import mongodb
        
        if mongodb.client:
            user_data = mongodb.get_user_by_username(username)
            if user_data:
                return User(
                    user_data['user_id'],
                    user_data['username'],
                    user_data['password']
                )
        # หาก MongoDB ไม่พร้อม ให้ return None
        return None

    @staticmethod
    def create(username, password):
        """สร้าง user ใหม่"""
        from werkzeug.security import generate_password_hash
        from database import mongodb
        
        # Generate user ID
        if mongodb.client:
            all_users = mongodb.get_all_users()
            user_id = str(len(all_users) + 1)
        else:
            # MongoDB not available, cannot create user
            return None
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # พยายามบันทึกลง MongoDB ก่อน
        if mongodb.client:
            success = mongodb.create_user(user_id, username, hashed_password)
            if success:
                return User(user_id, username, hashed_password)
        
        # หาก MongoDB ไม่พร้อม ให้ return None
        return None
