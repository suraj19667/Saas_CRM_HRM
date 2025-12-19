import sqlite3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mini_saas_project.settings')
django.setup()

# Connect to the database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Check and add missing columns
try:
    # Check if columns exist
    cursor.execute("PRAGMA table_info(tenants)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print("Existing columns:", columns)
    
    # Add razorpay_payment_id if not exists
    if 'razorpay_payment_id' not in columns:
        cursor.execute("ALTER TABLE tenants ADD COLUMN razorpay_payment_id VARCHAR(100)")
        print("Added razorpay_payment_id column")
    else:
        print("razorpay_payment_id already exists")
    
    # Add razorpay_order_id if not exists
    if 'razorpay_order_id' not in columns:
        cursor.execute("ALTER TABLE tenants ADD COLUMN razorpay_order_id VARCHAR(100)")
        print("Added razorpay_order_id column")
    else:
        print("razorpay_order_id already exists")
    
    # Add slug if not exists
    if 'slug' not in columns:
        cursor.execute("ALTER TABLE tenants ADD COLUMN slug VARCHAR(50)")
        print("Added slug column")
    else:
        print("slug already exists")
    
    conn.commit()
    print("\nAll columns added successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
