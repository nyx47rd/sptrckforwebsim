# This script is run automatically by the Vercel build process.
# It connects to the database and creates all necessary tables.

# The DATABASE_URL is loaded from Vercel's environment variables.
from api.index import engine, Base

print("Connecting to the database to create tables...")

# The Base object from our application knows about all the models.
# The engine object knows how to connect to the database.
# This command tells the database to create any tables that don't exist yet.
Base.metadata.create_all(bind=engine)

print("Successfully created tables (if they didn't exist).")
