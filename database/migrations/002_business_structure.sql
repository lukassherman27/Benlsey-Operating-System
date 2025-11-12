-- Migration 002: Business Structure Tables
-- Adds clients, operators, invoicing, payments, staff, drawings

-- CLIENTS (who pay for projects)
CREATE TABLE IF NOT EXISTS clients (
    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT UNIQUE NOT NULL,
    client_code TEXT,
    contact_person TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    billing_address TEXT,
    payment_terms TEXT DEFAULT 'Net 30',
    base_path TEXT,
    relationship_status TEXT DEFAULT 'active',
    total_contracted REAL DEFAULT 0,
    total_paid REAL DEFAULT 0,
    total_outstanding REAL DEFAULT 0,
    projects_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OPERATORS (hotel brands/operators)
CREATE TABLE IF NOT EXISTS operators (
    operator_id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator_name TEXT UNIQUE NOT NULL,
    operator_code TEXT,
    brand_guidelines_path TEXT,
    design_standards_path TEXT,
    base_path TEXT,
    projects_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Update PROJECTS table
ALTER TABLE projects ADD COLUMN client_id INTEGER REFERENCES clients(client_id);
ALTER TABLE projects ADD COLUMN operator_id INTEGER REFERENCES operators(operator_id);
ALTER TABLE projects ADD COLUMN base_path TEXT;
ALTER TABLE projects ADD COLUMN current_phase TEXT;
ALTER TABLE projects ADD COLUMN team_lead TEXT;
ALTER TABLE projects ADD COLUMN target_completion DATE;

-- INVOICES
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    invoice_number TEXT UNIQUE NOT NULL,
    amount REAL NOT NULL,
    phase TEXT,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    paid_date DATE,
    status TEXT DEFAULT 'draft',
    file_path TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

-- PAYMENTS
CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_date DATE NOT NULL,
    payment_method TEXT,
    reference_number TEXT,
    receipt_path TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

-- STAFF ASSIGNMENTS
CREATE TABLE IF NOT EXISTS staff_assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    staff_name TEXT NOT NULL,
    role TEXT NOT NULL,
    discipline TEXT,
    allocation_percent INTEGER DEFAULT 100,
    start_date DATE NOT NULL,
    end_date DATE,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- DRAWINGS / DESIGN FILES
CREATE TABLE IF NOT EXISTS drawings (
    drawing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    drawing_number TEXT NOT NULL,
    drawing_name TEXT,
    discipline TEXT NOT NULL,
    revision TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    revision_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT 1,
    notes TEXT,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- FILES TRACKING (all project files)
CREATE TABLE IF NOT EXISTS files (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    client_id INTEGER,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT,
    file_category TEXT,
    file_size INTEGER,
    mime_type TEXT,
    uploaded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by TEXT,
    tags TEXT,
    indexed BOOLEAN DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

-- MILESTONES
CREATE TABLE IF NOT EXISTS milestones (
    milestone_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    milestone_name TEXT NOT NULL,
    description TEXT,
    target_date DATE NOT NULL,
    completion_date DATE,
    status TEXT DEFAULT 'pending',
    deliverables TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_invoices_project ON invoices(project_id);
CREATE INDEX IF NOT EXISTS idx_invoices_client ON invoices(client_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payments_project ON payments(project_id);
CREATE INDEX IF NOT EXISTS idx_staff_project ON staff_assignments(project_id);
CREATE INDEX IF NOT EXISTS idx_drawings_project ON drawings(project_id);
CREATE INDEX IF NOT EXISTS idx_drawings_current ON drawings(is_current);
CREATE INDEX IF NOT EXISTS idx_files_project ON files(project_id);
CREATE INDEX IF NOT EXISTS idx_milestones_project ON milestones(project_id);
