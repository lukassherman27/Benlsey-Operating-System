#!/usr/bin/env python3
"""
scan_documents.py

Scans directories for project-related documents
Auto-links PDFs, drawings, and files to projects
"""

import sqlite3
import os
import re
from pathlib import Path
from datetime import datetime

class DocumentScanner:
    def __init__(self):
        self.master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
        
        # Directories to scan
        self.scan_dirs = [
            Path.home() / "Desktop",
            Path.home() / "Documents",
            Path.home() / "Downloads"
        ]
        
        # File extensions to look for
        self.doc_extensions = [
            '.pdf', '.dwg', '.dxf', '.skp', '.3dm', 
            '.docx', '.xlsx', '.pptx', '.jpg', '.png'
        ]
    
    def create_documents_table(self):
        """Create table for document tracking"""
        print("\n📄 Creating documents table...")
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_documents (
                document_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                file_path TEXT UNIQUE,
                file_name TEXT,
                file_type TEXT,
                file_size INTEGER,
                confidence REAL,
                link_method TEXT,
                evidence TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
        """)
        
        self.conn.commit()
        print("   ✅ Documents table ready")
    
    def extract_project_code_from_filename(self, filename):
        """Extract project code from filename"""
        # Look for BK-XXX pattern
        matches = re.findall(r'\b(?:\d{2}\s+)?BK-\d{3}\b', filename, re.IGNORECASE)
        return [m.strip().upper() for m in matches]
    
    def extract_project_code_from_path(self, filepath):
        """Extract project code from full file path"""
        path_str = str(filepath)
        matches = re.findall(r'\b(?:\d{2}\s+)?BK-\d{3}\b', path_str, re.IGNORECASE)
        return [m.strip().upper() for m in matches]
    
    def scan_directory(self, directory, max_files=1000):
        """Scan a directory for project documents"""
        print(f"\n🔍 Scanning: {directory}")
        
        files_found = []
        file_count = 0
        
        try:
            for root, dirs, files in os.walk(directory):
                # Skip hidden directories and common excludes
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                          ['node_modules', '__pycache__', '.git', 'Library', 'Applications']]
                
                for file in files:
                    if file_count >= max_files:
                        break
                    
                    # Check extension
                    ext = Path(file).suffix.lower()
                    if ext not in self.doc_extensions:
                        continue
                    
                    file_path = Path(root) / file
                    
                    # Skip if already processed
                    self.cursor.execute("""
                        SELECT document_id FROM project_documents WHERE file_path = ?
                    """, (str(file_path),))
                    
                    if self.cursor.fetchone():
                        continue
                    
                    # Look for project codes
                    codes_in_name = self.extract_project_code_from_filename(file)
                    codes_in_path = self.extract_project_code_from_path(file_path)
                    
                    all_codes = list(set(codes_in_name + codes_in_path))
                    
                    if all_codes:
                        try:
                            file_size = file_path.stat().st_size
                            files_found.append({
                                'path': file_path,
                                'name': file,
                                'type': ext,
                                'size': file_size,
                                'codes': all_codes
                            })
                            file_count += 1
                        except:
                            pass
                
                if file_count >= max_files:
                    break
        
        except PermissionError:
            print(f"   ⚠️  Permission denied")
        
        print(f"   ✅ Found {len(files_found)} project-related documents")
        return files_found
    
    def link_documents_to_projects(self, documents):
        """Link found documents to projects"""
        print("\n🔗 Linking documents to projects...")
        
        linked_count = 0
        
        for doc in documents:
            for code in doc['codes']:
                # Find project
                self.cursor.execute("""
                    SELECT project_id FROM projects WHERE project_code = ?
                """, (code,))
                
                result = self.cursor.fetchone()
                if not result:
                    continue
                
                project_id = result[0]
                
                # Determine confidence based on where code was found
                if code in str(doc['name']):
                    confidence = 0.95
                    evidence = f"Project code {code} in filename"
                else:
                    confidence = 0.85
                    evidence = f"Project code {code} in file path"
                
                try:
                    self.cursor.execute("""
                        INSERT OR IGNORE INTO project_documents
                        (project_id, file_path, file_name, file_type, file_size,
                         confidence, link_method, evidence)
                        VALUES (?, ?, ?, ?, ?, ?, 'filename_pattern', ?)
                    """, (project_id, str(doc['path']), doc['name'], doc['type'],
                          doc['size'], confidence, evidence))
                    
                    if self.cursor.rowcount > 0:
                        linked_count += 1
                
                except Exception as e:
                    pass
        
        self.conn.commit()
        print(f"   ✅ Linked {linked_count} documents")
        return linked_count
    
    def show_document_summary(self):
        """Show summary of linked documents"""
        print("\n" + "="*70)
        print("DOCUMENT SUMMARY")
        print("="*70)
        
        # Documents by project
        self.cursor.execute("""
            SELECT 
                p.project_code,
                p.project_title,
                COUNT(pd.document_id) as doc_count
            FROM projects p
            LEFT JOIN project_documents pd ON p.project_id = pd.project_id
            GROUP BY p.project_id
            HAVING doc_count > 0
            ORDER BY doc_count DESC
            LIMIT 10
        """)
        
        print("\n📊 Projects with most documents:")
        for code, title, count in self.cursor.fetchall():
            print(f"   {code}: {count} documents - {title[:40]}")
        
        # Documents by type
        self.cursor.execute("""
            SELECT file_type, COUNT(*) as count
            FROM project_documents
            GROUP BY file_type
            ORDER BY count DESC
        """)
        
        print("\n📄 Documents by type:")
        for file_type, count in self.cursor.fetchall():
            print(f"   {file_type}: {count}")
        
        # Total stats
        self.cursor.execute("SELECT COUNT(*), SUM(file_size) FROM project_documents")
        total_docs, total_size = self.cursor.fetchone()
        
        size_mb = (total_size or 0) / (1024 * 1024)
        print(f"\n📈 Total: {total_docs} documents ({size_mb:.1f} MB)")
    
    def run(self):
        """Main scanning process"""
        print("="*70)
        print("DOCUMENT SCANNER")
        print("="*70)
        print("\nScanning for project-related documents...")
        
        # Create table
        self.create_documents_table()
        
        # Scan each directory
        all_documents = []
        for directory in self.scan_dirs:
            if directory.exists():
                docs = self.scan_directory(directory, max_files=500)
                all_documents.extend(docs)
        
        # Link documents
        if all_documents:
            self.link_documents_to_projects(all_documents)
        
        # Show summary
        self.show_document_summary()
        
        print("\n✅ Document scanning complete!")
        
        self.conn.close()

def main():
    scanner = DocumentScanner()
    scanner.run()

if __name__ == '__main__':
    main()
