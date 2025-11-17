#!/usr/bin/env python3
"""
Bensley Intelligence Platform - Quick Start Setup

This script automates the initial setup process:
1. Checks Python version
2. Creates virtual environment
3. Installs dependencies
4. Sets up .env configuration
5. Initializes database
6. Tests connections
7. Creates example project

Usage:
    python quickstart.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


class QuickStartSetup:
    def __init__(self):
        self.root_path = Path(__file__).parent
        self.venv_path = self.root_path / "venv"
        self.data_path = self.root_path / "data"
        self.db_path = self.root_path / "database" / "bensley_master.db"

    def print_header(self, text):
        """Print a nice header"""
        print(f"\n{'='*70}")
        print(f"  {text}")
        print(f"{'='*70}\n")

    def print_step(self, number, text):
        """Print step number"""
        print(f"\n📍 STEP {number}: {text}")
        print("-" * 70)

    def check_python_version(self):
        """Check Python version"""
        self.print_step(1, "Checking Python version")

        version = sys.version_info
        print(f"   Python version: {version.major}.{version.minor}.{version.micro}")

        if version.major < 3 or (version.major == 3 and version.minor < 9):
            print(f"   ❌ ERROR: Python 3.9+ required")
            print(f"   Please install Python 3.9 or higher")
            return False

        print(f"   ✅ Python version OK")
        return True

    def create_virtual_environment(self):
        """Create Python virtual environment"""
        self.print_step(2, "Creating virtual environment")

        if self.venv_path.exists():
            print(f"   ⚠️  Virtual environment already exists")
            response = input(f"   Recreate? (y/N): ").strip().lower()
            if response == 'y':
                import shutil
                shutil.rmtree(self.venv_path)
            else:
                print(f"   ✅ Using existing virtual environment")
                return True

        try:
            print(f"   Creating venv at: {self.venv_path}")
            subprocess.run([sys.executable, "-m", "venv", str(self.venv_path)], check=True)
            print(f"   ✅ Virtual environment created")
            return True
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            return False

    def get_venv_python(self):
        """Get path to venv Python executable"""
        if platform.system() == "Windows":
            return self.venv_path / "Scripts" / "python.exe"
        else:
            return self.venv_path / "bin" / "python"

    def install_dependencies(self):
        """Install Python dependencies"""
        self.print_step(3, "Installing dependencies")

        python_exe = self.get_venv_python()

        try:
            print(f"   Installing from requirements.txt...")
            subprocess.run(
                [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"],
                check=True,
                capture_output=True
            )
            subprocess.run(
                [str(python_exe), "-m", "pip", "install", "-r", "requirements.txt"],
                check=True
            )
            print(f"   ✅ Dependencies installed")
            return True
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            return False

    def setup_env_file(self):
        """Set up .env configuration"""
        self.print_step(4, "Configuring environment")

        env_file = self.root_path / ".env"

        if env_file.exists():
            print(f"   ⚠️  .env file already exists")
            response = input(f"   Overwrite? (y/N): ").strip().lower()
            if response != 'y':
                print(f"   ✅ Using existing .env file")
                return True

        print(f"\n   Let's configure your environment...")

        # Get email credentials
        print(f"\n   Email Server Configuration:")
        email_server = input(f"   Email server (default: tmail.bensley.com): ").strip() or "tmail.bensley.com"
        email_port = input(f"   Email port (default: 993): ").strip() or "993"
        email_username = input(f"   Email username: ").strip()
        email_password = input(f"   Email password: ").strip()

        # Get OpenAI key (optional)
        print(f"\n   AI Configuration (optional - press Enter to skip):")
        openai_key = input(f"   OpenAI API key: ").strip()

        # Create .env content
        env_content = f"""# Bensley Intelligence Platform Configuration

# Database
DATABASE_PATH={self.db_path}

# Data folder
DATA_ROOT_PATH={self.data_path}

# Email Configuration
EMAIL_SERVER={email_server}
EMAIL_PORT={email_port}
EMAIL_USERNAME={email_username}
EMAIL_PASSWORD={email_password}

# AI Configuration (optional)
OPENAI_API_KEY={openai_key}

# Neo4j (optional - for graph features)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Redis (optional - for caching)
REDIS_HOST=localhost
REDIS_PORT=6379
"""

        with open(env_file, 'w') as f:
            f.write(env_content)

        print(f"   ✅ .env file created")
        return True

    def initialize_database(self):
        """Initialize the database"""
        self.print_step(5, "Initializing database")

        python_exe = self.get_venv_python()

        try:
            # Create database directory if needed
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"   Running database initialization...")
            result = subprocess.run(
                [str(python_exe), "database/init_database.py"],
                check=True,
                capture_output=True,
                text=True
            )
            print(result.stdout)
            print(f"   ✅ Database initialized at: {self.db_path}")
            return True
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            return False

    def test_connections(self):
        """Test email and database connections"""
        self.print_step(6, "Testing connections")

        python_exe = self.get_venv_python()

        # Test database
        print(f"   Testing database connection...")
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM projects")
            count = cursor.fetchone()[0]
            conn.close()
            print(f"   ✅ Database OK - {count} projects found")
        except Exception as e:
            print(f"   ⚠️  Database test failed: {e}")

        # Test email (optional)
        print(f"\n   Test email connection? (y/N): ", end='')
        if input().strip().lower() == 'y':
            try:
                print(f"   Testing email connection...")
                result = subprocess.run(
                    [str(python_exe), "-c", """
import os
import imaplib
from dotenv import load_dotenv
load_dotenv()
mail = imaplib.IMAP4_SSL(os.getenv('EMAIL_SERVER'), int(os.getenv('EMAIL_PORT')))
mail.login(os.getenv('EMAIL_USERNAME'), os.getenv('EMAIL_PASSWORD'))
print('✅ Email connection OK')
mail.logout()
"""],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"   {result.stdout}")
            except Exception as e:
                print(f"   ⚠️  Email test failed - you may need to configure this later")

        return True

    def create_example_project(self):
        """Create an example project"""
        self.print_step(7, "Creating example project")

        print(f"   Create an example project to test the system? (Y/n): ", end='')
        if input().strip().lower() == 'n':
            print(f"   Skipped")
            return True

        python_exe = self.get_venv_python()

        try:
            print(f"   Creating BK-EXAMPLE project...")
            result = subprocess.run(
                [str(python_exe), "-c", """
from backend.services.project_creator import ProjectCreator
creator = ProjectCreator()
creator.create_project(
    project_code='BK-EXAMPLE',
    project_name='Example Test Project',
    client_name='Example Developer Corp',
    operator_name='Example Hotel Brand',
    contract_value=1000000,
    status='active'
)
"""],
                check=True,
                capture_output=True,
                text=True
            )
            print(result.stdout)
            print(f"   ✅ Example project created")
            return True
        except Exception as e:
            print(f"   ⚠️  Could not create example project: {e}")
            return True  # Don't fail overall setup

    def print_next_steps(self):
        """Print what to do next"""
        self.print_header("Setup Complete! 🎉")

        venv_activate = "venv\\Scripts\\activate" if platform.system() == "Windows" else "source venv/bin/activate"

        print(f"""
✅ Your Bensley Intelligence Platform is ready to use!

Next steps:

1. Activate the virtual environment:
   {venv_activate}

2. Import your existing projects from Excel:
   python backend/services/excel_importer.py --file path/to/projects.xlsx

3. Sync emails from your email server:
   python backend/services/email_importer.py

4. Create a new project:
   python backend/services/project_creator.py

5. Start the API server (optional):
   python -m uvicorn backend.api.main:app --reload
   Then visit: http://localhost:8000/docs

6. Check the database:
   - Install DB Browser for SQLite (free)
   - Open: {self.db_path}

📖 Documentation:
   - DEPLOYMENT_GUIDE.md - Detailed setup instructions
   - FOUNDATION_BUILT.md - Architecture overview
   - data/README.md - File organization guide

💡 Tips:
   - All project files go in: data/04_ACTIVE_PROJECTS/
   - Each project has standard folder structure
   - Daily work reports with photos go in: 04_SCHEDULING/daily_reports/
   - Forward planning goes in: 04_SCHEDULING/forward_schedule/

Questions? Check the documentation or ask for help!
""")

    def run(self):
        """Run the complete setup"""
        self.print_header("Bensley Intelligence Platform - Quick Start")

        print("This script will set up your Bensley Intelligence Platform.")
        print("It will take about 2-5 minutes.\n")

        response = input("Ready to begin? (Y/n): ").strip().lower()
        if response == 'n':
            print("Setup cancelled.")
            return

        # Run all setup steps
        steps = [
            self.check_python_version,
            self.create_virtual_environment,
            self.install_dependencies,
            self.setup_env_file,
            self.initialize_database,
            self.test_connections,
            self.create_example_project,
        ]

        for step in steps:
            if not step():
                print(f"\n❌ Setup failed. Please fix the errors and try again.")
                return

        self.print_next_steps()


def main():
    try:
        setup = QuickStartSetup()
        setup.run()
    except KeyboardInterrupt:
        print(f"\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
