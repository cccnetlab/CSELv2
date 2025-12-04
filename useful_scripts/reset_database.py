#!/usr/bin/env .venv/bin/python3

"""
Reset the database by completely deleting and recreating it.
This script will:
1. Delete the existing database file(s)
2. Create a fresh database with default values
3. Initialize all tables and default categories
"""

import sys
import os
import time
import shutil
from datetime import datetime

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def reset_database():
    """Delete and recreate the database"""
    print("=" * 60)
    print("Database Complete Reset Tool")
    print("=" * 60)
    print()
    print("⚠️  WARNING: This will DELETE the entire database!")
    print("   All settings and configurations will be lost.")
    print()
    
    # Confirm deletion
    response = input("Are you sure you want to delete and recreate the database? (yes/NO): ")
    if response.lower() != 'yes':
        print("\nDatabase reset cancelled.")
        return False
    
    print()
    
    try:
        # Define database path
        db_path = "/etc/CYBERPATRIOT/save_data.db"
        db_wal = db_path + "-wal"
        db_shm = db_path + "-shm"
        backup_dir = "/etc/CYBERPATRIOT/backups"
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Backup existing database if it exists
        if os.path.exists(db_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"save_data.db.backup_{timestamp}")
            
            print(f"Creating backup of existing database...")
            shutil.copy2(db_path, backup_path)
            print(f"  ✓ Backup saved to: {backup_path}")
            print()
        
        # Delete database files
        print("Deleting database files...")
        files_deleted = []
        
        if os.path.exists(db_path):
            os.remove(db_path)
            files_deleted.append(db_path)
            print(f"  ✓ Deleted: {db_path}")
        
        if os.path.exists(db_wal):
            os.remove(db_wal)
            files_deleted.append(db_wal)
            print(f"  ✓ Deleted: {db_wal}")
        
        if os.path.exists(db_shm):
            os.remove(db_shm)
            files_deleted.append(db_shm)
            print(f"  ✓ Deleted: {db_shm}")
        
        if not files_deleted:
            print("  (No database files found to delete)")
        
        print()
        
        # Now import and recreate the database
        print("Creating new database...")
        from src import db_handler
        
        # The import and initialization will create the database
        settings = db_handler.Settings()
        categories = db_handler.Categories()
        vulnerabilities = db_handler.OptionTables()
        
        # Initialize the option tables
        vulnerabilities.initialize_option_table()
        
        print("  ✓ Database structure created")
        print("  ✓ Default settings initialized")
        print("  ✓ Categories initialized")
        print("  ✓ Vulnerability templates initialized")
        print()
        
        # Enable WAL mode for the new database
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.close()
        print("  ✓ WAL mode enabled")
        print()
        
        # Fix permissions on the database directory and files
        import subprocess
        import pwd
        current_user = pwd.getpwuid(os.geteuid()).pw_name
        
        if os.geteuid() == 0:  # Running as root
            # Get the sudo user if available
            sudo_user = os.environ.get('SUDO_USER', current_user)
            if sudo_user != 'root':
                subprocess.run(['chown', '-R', f'{sudo_user}:{sudo_user}', '/etc/CYBERPATRIOT'], check=True)
                print(f"  ✓ Permissions set for user: {sudo_user}")
        
        # Verify the new database with a fresh instance
        print("Verifying new database...")
        verify_settings = db_handler.Settings()
        data = verify_settings.get_settings(False)
        print(f"  Current Points: {data['Current Points']}")
        print(f"  Current Vulnerabilities: {data['Current Vulnerabilities']}")
        print(f"  Tally Points: {data['Tally Points']}")
        print(f"  Tally Vulnerabilities: {data['Tally Vulnerabilities']}")
        print()
        
        print("=" * 60)
        print("✓ Database successfully deleted and recreated!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Run the configurator to set up your image")
        print("  2. Configure all vulnerabilities and settings")
        print("  3. Commit the configuration")
        print("  4. Run ONE instance of scoring_engine.py")
        print()
        print("Remember: Always run only ONE scoring_engine.py at a time!")
        
        return True
            
    except Exception as e:
        print()
        print("=" * 60)
        print("✗ Error resetting database!")
        print("=" * 60)
        print(f"\nError: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = reset_database()
    sys.exit(0 if success else 1)
