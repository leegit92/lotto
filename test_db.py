import asyncio
import asyncpg

# Database config (same as in main.py)
DB_USER = 'postgres'
DB_PASS = 'postgres123'  # Replace with your actual password
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'lotto'

async def test_connection():
    try:
        # Test connection
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        print("✅ Database connection successful!")
        
        # Test if table exists
        result = await conn.fetch("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'generated_numbers')")
        if result[0]['exists']:
            print("✅ Table 'generated_numbers' exists!")
        else:
            print("❌ Table 'generated_numbers' does not exist!")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nPossible solutions:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your password in the code")
        print("3. Make sure the database 'lotto' exists")
        print("4. Make sure the user 'lotto_user' exists and has permissions")

if __name__ == "__main__":
    asyncio.run(test_connection()) 