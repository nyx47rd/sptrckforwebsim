# This script is to be run once manually by the user on their local machine
# to set up the database tables in their Render PostgreSQL instance.

import os
from dotenv import load_dotenv

print("Loading environment variables for database setup...")
# The user should create a local .env file with their Render DATABASE_URL.
# Example: DATABASE_URL=postgresql://user:password@host:port/database
load_dotenv()

# We import the engine and Base from our main application file.
# This ensures we use the exact same configuration.
# The script needs the DATABASE_URL to be set in the environment to do this.
if not os.getenv("DATABASE_URL"):
    print("---")
    print("Error: DATABASE_URL environment variable not set.")
    print("Please create a file named .env in this directory.")
    print("Inside the .env file, add one line with your Render PostgreSQL URL:")
    print("DATABASE_URL=postgresql://user:password@host:port/database")
    print("---")
else:
    try:
        # We import these after ensuring the environment variable is set.
        from api.index import engine, Base

        print("Connecting to the database and creating tables...")

        # The Base object from our application knows about all the models (User, Token, etc.).
        # The engine object knows how to connect to the database.
        # This command tells the database to create any tables that don't exist yet.
        Base.metadata.create_all(bind=engine)

        print("\nSuccess! Database tables created.")
        print("You can now deploy your application to Vercel.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please check your DATABASE_URL in the .env file and ensure the database is accessible from your computer.")
