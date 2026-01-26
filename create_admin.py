# create_admin.py
import database as db

# 1. Initialize DB just in case
db.init_db()

# 2. Add the Admin User
# Change 'admin123' to whatever password you want
result = db.add_user("chatradi.surya@gmail.com", "System Admin", "surya16")

if result == "SUCCESS":
    print("✅ SUCCESS: Admin account created!")
    print("Email: admin@campus.com")
    print("Password: admin123")
elif result == "EXISTS":
    print("ℹ️ INFO: Admin account already exists. You can just login.")
else:
    print(f"❌ ERROR: {result}")