#!/usr/bin/env python3
"""
add_confidence_tracking.py

Adds confidence scoring infrastructure to the system.
SAFE: Only adds new tables/columns, doesn't modify existing data.

Creates:
- data_quality_tracking table (tracks issues)
- data_confidence_scores table (scores all data)
- Adds confidence columns where missing
- Calculates initial confidence scores

Updated: Oct 24, 2025
"""

import sqlite3
from pathlib import Path
from datetime import datetime

class ConfidenceTracker:
    def __init__(self):
        self.master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
    
    def create_tracking_tables(self):
        """Create new tracking tables (non-destructive)"""
        print("="*70)
        print("CREATING CONFIDENCE TRACKING TABLES")
        print("="*70)
        
        # 1. Data Quality Tracking Table
        print("\n📋 Creating data_quality_tracking table...")
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_quality_tracking (
                issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_table TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                issue_type TEXT NOT NULL,
                severity TEXT CHECK(severity IN ('critical', 'high', 'medium', 'low')),
                description TEXT,
                suggested_fix TEXT,
                suggested_value TEXT,
                ai_confidence REAL,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'reviewed', 'approved', 'rejected', 'fixed')),
                reviewed_by TEXT,
                reviewed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ Created")
        
        # 2. Data Confidence Scores Table
        print("\n📊 Creating data_confidence_scores table...")
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_confidence_scores (
                score_id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_table TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                field_value TEXT,
                confidence_score REAL NOT NULL,
                source TEXT,
                calculation_method TEXT,
                calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(data_table, record_id, field_name)
            )
        """)
        print("   ✅ Created")
        
        # 3. AI Suggestions Queue
        print("\n🤖 Creating ai_suggestions_queue table...")
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_suggestions_queue (
                suggestion_id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_table TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                current_value TEXT,
                suggested_value TEXT NOT NULL,
                confidence REAL NOT NULL,
                reasoning TEXT,
                evidence TEXT,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'applied')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                reviewed_at DATETIME,
                applied_at DATETIME
            )
        """)
        print("   ✅ Created")
        
        # 4. Learning Patterns Table (for ML)
        print("\n🧠 Creating learning_patterns table...")
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_patterns (
                pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_name TEXT NOT NULL,
                pattern_rule TEXT NOT NULL,
                confidence_weight REAL DEFAULT 1.0,
                times_used INTEGER DEFAULT 0,
                times_correct INTEGER DEFAULT 0,
                accuracy REAL,
                source TEXT CHECK(source IN ('manual', 'ai_learned', 'user_correction')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used DATETIME
            )
        """)
        print("   ✅ Created")
        
        self.conn.commit()
        print("\n✅ All tracking tables created!")
    
    def add_confidence_columns(self):
        """Add confidence columns to existing tables (safe)"""
        print("\n" + "="*70)
        print("ADDING CONFIDENCE COLUMNS")
        print("="*70)
        
        # Check if columns already exist
        tables_to_update = {
            'email_project_links': 'confidence',
            'rfis': 'extraction_confidence',
            'action_items_tracking': 'confidence',
            'project_status_tracking': 'confidence'
        }
        
        for table, col_name in tables_to_update.items():
            try:
                # Check if column exists
                self.cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in self.cursor.fetchall()]
                
                if col_name in columns:
                    print(f"   ⏩ {table}.{col_name} already exists")
                else:
                    print(f"   ➕ Adding {table}.{col_name}...")
                    # Some tables already have 'confidence', others need it added
                    if col_name not in columns:
                        self.cursor.execute(f"""
                            ALTER TABLE {table} 
                            ADD COLUMN {col_name} REAL DEFAULT 0.5
                        """)
                        print(f"      ✅ Added")
            except Exception as e:
                print(f"   ⚠️  {table}: {e}")
        
        self.conn.commit()
        print("\n✅ Confidence columns ready!")
    
    def calculate_initial_scores(self):
        """Calculate confidence scores for existing data"""
        print("\n" + "="*70)
        print("CALCULATING INITIAL CONFIDENCE SCORES")
        print("="*70)
        
        scores_added = 0
        
        # 1. Email Project Links
        print("\n📧 Scoring email-project links...")
        self.cursor.execute("""
            SELECT 
                epl.email_id,
                epl.project_code,
                epl.link_method,
                epl.confidence
            FROM email_project_links epl
        """)
        
        links = self.cursor.fetchall()
        for email_id, project_code, method, current_conf in links:
            # Calculate confidence based on link method
            if method == 'manual':
                score = 1.0
            elif method == 'exact_match':
                score = 0.95
            elif method == 'pattern_match':
                score = 0.8
            elif current_conf and current_conf > 0:
                score = current_conf
            else:
                score = 0.6  # Default for old links
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO data_confidence_scores
                (data_table, record_id, field_name, field_value, confidence_score, source, calculation_method)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('email_project_links', email_id, 'project_code', project_code, 
                  score, method or 'legacy', 'link_method_based'))
            
            scores_added += 1
        
        print(f"   ✅ Scored {scores_added} email links")
        
        # 2. Project Data Completeness
        print("\n📊 Scoring project data completeness...")
        self.cursor.execute("SELECT project_id, project_code FROM projects")
        projects = self.cursor.fetchall()
        
        for project_id, project_code in projects:
            # Calculate completeness score
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total_fields,
                    SUM(CASE 
                        WHEN project_title IS NOT NULL AND project_title != '' THEN 1 
                        ELSE 0 
                    END) +
                    SUM(CASE 
                        WHEN country IS NOT NULL AND country != '' THEN 1 
                        ELSE 0 
                    END) +
                    SUM(CASE 
                        WHEN city IS NOT NULL AND city != '' THEN 1 
                        ELSE 0 
                    END) +
                    SUM(CASE 
                        WHEN client_id IS NOT NULL THEN 1 
                        ELSE 0 
                    END) +
                    SUM(CASE 
                        WHEN date_created IS NOT NULL AND date_created < '2025-10-22' THEN 1 
                        ELSE 0 
                    END) as filled_fields
                FROM projects
                WHERE project_id = ?
            """, (project_id,))
            
            total, filled = self.cursor.fetchone()
            completeness = filled / 5.0 if filled else 0.2
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO data_confidence_scores
                (data_table, record_id, field_name, field_value, confidence_score, source, calculation_method)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('projects', project_id, 'data_completeness', 
                  f'{filled}/5', completeness, 'calculated', 'field_count'))
        
        print(f"   ✅ Scored {len(projects)} projects")
        
        # 3. RFIs
        print("\n📋 Scoring RFIs...")
        self.cursor.execute("""
            SELECT rfi_id, rfi_number, date_due, date_responded
            FROM rfis
        """)
        
        rfis = self.cursor.fetchall()
        for rfi_id, rfi_num, due, responded in rfis:
            score = 0.7  # Base score
            if rfi_num and rfi_num != 'None':
                score += 0.2  # Has RFI number
            if due:
                score += 0.1  # Has due date
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO data_confidence_scores
                (data_table, record_id, field_name, field_value, confidence_score, source, calculation_method)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('rfis', rfi_id, 'extraction_quality', rfi_num, 
                  score, 'extracted', 'field_presence'))
        
        print(f"   ✅ Scored {len(rfis)} RFIs")
        
        self.conn.commit()
        print("\n✅ Initial confidence scores calculated!")
    
    def create_initial_patterns(self):
        """Create initial pattern recognition rules"""
        print("\n" + "="*70)
        print("CREATING INITIAL LEARNING PATTERNS")
        print("="*70)
        
        patterns = [
            ('email_linking', 'project_code_in_subject', 
             'Subject contains BK-XXX format', 0.9, 'manual'),
            ('email_linking', 'rfi_number_pattern', 
             'Subject contains RFI #XXX or DAE-RFI-CIR-XXX', 0.95, 'manual'),
            ('location_extraction', 'country_in_title', 
             'Project title ends with country name', 0.85, 'manual'),
            ('location_extraction', 'city_in_title', 
             'Project title contains city name before country', 0.8, 'manual'),
            ('client_extraction', 'known_brand_names', 
             'Title contains known hotel brands', 0.9, 'manual'),
            ('timeline_validation', 'chronological_order', 
             'Events must be in logical date order', 1.0, 'manual'),
        ]
        
        for ptype, pname, prule, weight, source in patterns:
            self.cursor.execute("""
                INSERT OR IGNORE INTO learning_patterns
                (pattern_type, pattern_name, pattern_rule, confidence_weight, source)
                VALUES (?, ?, ?, ?, ?)
            """, (ptype, pname, prule, weight, source))
        
        self.conn.commit()
        print(f"   ✅ Created {len(patterns)} initial patterns")
    
    def generate_summary(self):
        """Show summary of confidence tracking setup"""
        print("\n" + "="*70)
        print("CONFIDENCE TRACKING SUMMARY")
        print("="*70)
        
        # Count scores
        self.cursor.execute("SELECT COUNT(*) FROM data_confidence_scores")
        score_count = self.cursor.fetchone()[0]
        
        # Count patterns
        self.cursor.execute("SELECT COUNT(*) FROM learning_patterns")
        pattern_count = self.cursor.fetchone()[0]
        
        print(f"\n📊 Confidence scores created: {score_count}")
        print(f"🧠 Learning patterns created: {pattern_count}")
        print(f"📋 Quality tracking: Ready")
        print(f"🤖 AI suggestions queue: Ready")
        
        print("\n✅ System is ready for:")
        print("   1. Data quality improvements")
        print("   2. AI suggestion integration")
        print("   3. Learning from corrections")
        
        print("\n" + "="*70)
    
    def run(self):
        """Execute all setup steps"""
        self.create_tracking_tables()
        self.add_confidence_columns()
        self.calculate_initial_scores()
        self.create_initial_patterns()
        self.generate_summary()
        self.conn.close()

def main():
    print("Starting confidence tracking setup...")
    print("This is SAFE - only adds new tables/scores, doesn't modify existing data\n")
    
    tracker = ConfidenceTracker()
    tracker.run()
    
    print("\n🎉 COMPLETE! Your system now has confidence tracking!")
    print("\nNext steps:")
    print("  1. Run data_quality_dashboard.py to see updated scores")
    print("  2. Work on weekend data integration")
    print("  3. Come back Monday for AI integration!")

if __name__ == '__main__':
    main()
