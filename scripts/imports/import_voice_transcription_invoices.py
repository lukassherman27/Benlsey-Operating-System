#!/usr/bin/env python3
"""
Import Invoice Data from Voice Transcription
Source: Project Status as of 17th November 2025 Excel
Transcribed by Lukas on 2025-11-27

This script imports detailed invoice data for:
- 16 BK-079: JW Marriott Resort Jeju (Interior Design)
- 16 BK-076: JW Marriott Resort Jeju (Landscape Architecture)
- 20 BK-047: Oddly Square House Communal Spa (Interior Design)
- 19 BK-018: Villa Project Ahmedabad (LA, Arch, ID)
- 20 BK-092: Resort Project Udaipur (LA, Arch, ID)
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

# All invoice data parsed from transcription
INVOICE_DATA = [
    # ===== 16 BK-079: JW Marriott Resort Jeju - Interior Design =====
    {'project_code': '16 BK-079', 'discipline': 'Interior Design', 'phase': 'Mobilization',
     'invoice_number': 'I17-028', 'invoice_date': '2017-03-21', 'invoice_amount': 187500.00,
     'payment_date': '2017-03-23', 'payment_amount': 187500.00, 'status': 'paid'},
    {'project_code': '16 BK-079', 'discipline': 'Interior Design', 'phase': 'Concept Design',
     'invoice_number': 'I17-054', 'invoice_date': '2017-06-16', 'invoice_amount': 235375.00,
     'payment_date': '2017-08-07', 'payment_amount': 235375.00, 'status': 'paid', 'notes': '75% of concept design'},
    {'project_code': '16 BK-079', 'discipline': 'Interior Design', 'phase': 'Concept Design',
     'invoice_number': 'I18-029', 'invoice_date': '2018-02-19', 'invoice_amount': 78125.00,
     'payment_date': '2018-02-28', 'payment_amount': 78125.00, 'status': 'paid', 'notes': '25% of concept design'},
    {'project_code': '16 BK-079', 'discipline': 'Interior Design', 'phase': 'Design Development',
     'invoice_number': 'I18-037', 'invoice_date': '2018-04-05', 'invoice_amount': 187500.00,
     'payment_date': '2018-05-03', 'payment_amount': 187500.00, 'status': 'paid', 'notes': '50% of DD'},
    {'project_code': '16 BK-079', 'discipline': 'Interior Design', 'phase': 'Design Development',
     'invoice_number': 'I18-091', 'invoice_date': '2018-09-03', 'invoice_amount': 187500.00,
     'payment_date': '2018-11-02', 'payment_amount': 187500.00, 'status': 'paid', 'notes': '50% of DD'},
    {'project_code': '16 BK-079', 'discipline': 'Interior Design', 'phase': 'Construction Documents',
     'invoice_number': 'I20-007', 'invoice_date': '2020-02-03', 'invoice_amount': 93750.00,
     'payment_date': '2020-02-27', 'payment_amount': 93750.00, 'status': 'paid', 'notes': '50% of CD'},
    {'project_code': '16 BK-079', 'discipline': 'Interior Design', 'phase': 'Construction Documents',
     'invoice_number': 'I20-045', 'invoice_date': '2020-05-25', 'invoice_amount': 93750.00,
     'payment_date': '2020-09-11', 'payment_amount': 93750.00, 'status': 'paid', 'notes': '50% of CD - paid in 2 installments'},
    {'project_code': '16 BK-079', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I20-017', 'invoice_date': '2020-02-17', 'invoice_amount': 46875.00,
     'payment_date': '2021-07-17', 'payment_amount': 46875.00, 'status': 'paid', 'notes': '25% of CO'},
    {'project_code': '16 BK-079', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I21-002', 'invoice_date': '2021-01-07', 'invoice_amount': 46875.00,
     'payment_date': '2021-07-17', 'payment_amount': 46875.00, 'status': 'paid', 'notes': '25% of CO'},
    {'project_code': '16 BK-079', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I21-058', 'invoice_date': '2021-08-02', 'invoice_amount': 46875.00,
     'payment_date': '2022-02-21', 'payment_amount': 46875.00, 'status': 'paid', 'notes': '25% of CO'},
    {'project_code': '16 BK-079', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I22-018', 'invoice_date': '2022-03-03', 'invoice_amount': 46875.00,
     'payment_date': '2022-04-22', 'payment_amount': 46875.00, 'status': 'paid', 'notes': '25% of CO - final'},

    # ===== 16 BK-076: JW Marriott Resort Jeju - Landscape Architecture =====
    {'project_code': '16 BK-076', 'discipline': 'Landscape Architecture', 'phase': 'Mobilization',
     'invoice_number': 'I17-037', 'invoice_date': '2017-04-18', 'invoice_amount': 148350.00,
     'payment_date': '2017-04-28', 'payment_amount': 148350.00, 'status': 'paid'},
    {'project_code': '16 BK-076', 'discipline': 'Landscape Architecture', 'phase': 'Concept Design',
     'invoice_number': 'I17-055', 'invoice_date': '2017-06-16', 'invoice_amount': 185440.00,
     'payment_date': '2017-08-07', 'payment_amount': 185440.00, 'status': 'paid', 'notes': '75% of concept design'},
    {'project_code': '16 BK-076', 'discipline': 'Landscape Architecture', 'phase': 'Concept Design',
     'invoice_number': 'I18-030', 'invoice_date': '2018-02-19', 'invoice_amount': 61812.00,
     'payment_date': '2018-02-28', 'payment_amount': 61812.00, 'status': 'paid', 'notes': '25% of concept design'},
    {'project_code': '16 BK-076', 'discipline': 'Landscape Architecture', 'phase': 'Design Development',
     'invoice_number': 'I18-038', 'invoice_date': '2018-04-05', 'invoice_amount': 148350.00,
     'payment_date': '2018-05-03', 'payment_amount': 148350.00, 'status': 'paid', 'notes': '50% of DD'},
    {'project_code': '16 BK-076', 'discipline': 'Landscape Architecture', 'phase': 'Design Development',
     'invoice_number': 'I18-092', 'invoice_date': '2018-09-03', 'invoice_amount': 148350.00,
     'payment_date': '2018-12-14', 'payment_amount': 148350.00, 'status': 'paid', 'notes': '50% of DD'},
    {'project_code': '16 BK-076', 'discipline': 'Landscape Architecture', 'phase': 'Construction Documents',
     'invoice_number': 'I19-059', 'invoice_date': '2019-06-24', 'invoice_amount': 74175.00,
     'payment_date': '2020-07-27', 'payment_amount': 74175.00, 'status': 'paid', 'notes': '50% of CD'},
    {'project_code': '16 BK-076', 'discipline': 'Landscape Architecture', 'phase': 'Construction Documents',
     'invoice_number': 'I19-060', 'invoice_date': '2019-06-24', 'invoice_amount': 74175.00,
     'payment_date': '2020-09-28', 'payment_amount': 74175.00, 'status': 'paid', 'notes': '50% of CD'},
    {'project_code': '16 BK-076', 'discipline': 'Landscape Architecture', 'phase': 'Construction Observation',
     'invoice_number': 'I21-003', 'invoice_date': '2021-01-07', 'invoice_amount': 37087.00,
     'payment_date': '2021-07-14', 'payment_amount': 37087.00, 'status': 'paid', 'notes': '25% of CO'},
    {'project_code': '16 BK-076', 'discipline': 'Landscape Architecture', 'phase': 'Construction Observation',
     'invoice_number': 'I21-036', 'invoice_date': '2021-04-19', 'invoice_amount': 37087.00,
     'payment_date': '2021-07-14', 'payment_amount': 37087.00, 'status': 'paid', 'notes': '25% of CO'},
    {'project_code': '16 BK-076', 'discipline': 'Landscape Architecture', 'phase': 'Construction Observation',
     'invoice_number': 'I21-059', 'invoice_date': '2021-08-02', 'invoice_amount': 37087.00,
     'payment_date': '2022-02-21', 'payment_amount': 37087.00, 'status': 'paid', 'notes': '25% of CO'},
    {'project_code': '16 BK-076', 'discipline': 'Landscape Architecture', 'phase': 'Construction Observation',
     'invoice_number': 'I22-019', 'invoice_date': '2022-03-03', 'invoice_amount': 37087.00,
     'payment_date': '2022-04-22', 'payment_amount': 37087.00, 'status': 'paid', 'notes': '25% of CO - final'},
    {'project_code': '16 BK-076', 'discipline': 'Landscape Architecture', 'phase': 'Additional Services',
     'invoice_number': 'I20-019', 'invoice_date': '2020-02-18', 'invoice_amount': 20000.00,
     'payment_date': '2020-09-28', 'payment_amount': 20000.00, 'status': 'paid', 'notes': 'New room types design through CD'},

    # ===== 20 BK-047: Oddly Square House Communal Spa - Interior Design =====
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Concept Design',
     'invoice_number': 'I20-080', 'invoice_date': '2020-09-21', 'invoice_amount': 147539.00,
     'payment_date': '2020-10-30', 'payment_amount': 147539.00, 'status': 'paid', 'notes': '50% of concept design'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Concept Design',
     'invoice_number': 'I20-083', 'invoice_date': '2020-09-30', 'invoice_amount': 147539.00,
     'payment_date': '2020-12-22', 'payment_amount': 147539.00, 'status': 'paid', 'notes': '50% of concept design'},
    # Design Development - 6 equal payments of ~$57,750
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Design Development',
     'invoice_number': 'I21-012', 'invoice_date': '2021-03-03', 'invoice_amount': 57750.00,
     'payment_date': '2021-04-01', 'payment_amount': 57750.00, 'status': 'paid', 'notes': 'DD payment 1/6'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Design Development',
     'invoice_number': 'I21-013', 'invoice_date': '2021-03-03', 'invoice_amount': 57750.00,
     'payment_date': '2021-04-30', 'payment_amount': 57750.00, 'status': 'paid', 'notes': 'DD payment 2/6'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Design Development',
     'invoice_number': 'I21-014', 'invoice_date': '2021-03-03', 'invoice_amount': 57750.00,
     'payment_date': '2021-05-28', 'payment_amount': 57750.00, 'status': 'paid', 'notes': 'DD payment 3/6'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Design Development',
     'invoice_number': 'I21-015', 'invoice_date': '2021-03-03', 'invoice_amount': 57750.00,
     'payment_date': '2021-07-05', 'payment_amount': 57750.00, 'status': 'paid', 'notes': 'DD payment 4/6'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Design Development',
     'invoice_number': 'I21-047', 'invoice_date': '2021-06-07', 'invoice_amount': 57750.00,
     'payment_date': '2021-08-08', 'payment_amount': 57750.00, 'status': 'paid', 'notes': 'DD payment 5/6'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Design Development',
     'invoice_number': 'I21-054', 'invoice_date': '2021-07-05', 'invoice_amount': 57750.00,
     'payment_date': '2021-08-31', 'payment_amount': 57750.00, 'status': 'paid', 'notes': 'DD payment 6/6'},
    # Construction Documents
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Documents',
     'invoice_number': 'I22-015', 'invoice_date': '2022-02-24', 'invoice_amount': 30000.00,
     'payment_date': '2022-02-28', 'payment_amount': 30000.00, 'status': 'paid', 'notes': 'Wet communal area'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Documents',
     'invoice_number': 'I22-016', 'invoice_date': '2022-02-24', 'invoice_amount': 30000.00,
     'payment_date': '2022-04-01', 'payment_amount': 30000.00, 'status': 'paid', 'notes': 'Gym, pool hall, bar'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Documents',
     'invoice_number': 'I22-032', 'invoice_date': '2022-04-26', 'invoice_amount': 30000.00,
     'payment_date': '2022-04-29', 'payment_amount': 30000.00, 'status': 'paid', 'notes': 'Spa and treatment finishes'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Documents',
     'invoice_number': 'I22-038', 'invoice_date': '2022-05-18', 'invoice_amount': 30000.00,
     'payment_date': '2022-05-31', 'payment_amount': 30000.00, 'status': 'paid', 'notes': 'Gym pool hall bar'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Documents',
     'invoice_number': 'I22-039', 'invoice_date': '2022-05-18', 'invoice_amount': 30000.00,
     'payment_date': '2022-05-31', 'payment_amount': 30000.00, 'status': 'paid', 'notes': 'Spa treatment finishes'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Documents',
     'invoice_number': 'I22-050', 'invoice_date': '2022-06-01', 'invoice_amount': 10000.00,
     'payment_date': '2022-07-01', 'payment_amount': 10000.00, 'status': 'paid', 'notes': 'WP3B stage F1 1/4'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Documents',
     'invoice_number': 'I22-053', 'invoice_date': '2022-07-05', 'invoice_amount': 10000.00,
     'payment_date': '2022-08-01', 'payment_amount': 10000.00, 'status': 'paid', 'notes': 'WP3B stage F1 2/4'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Documents',
     'invoice_number': 'I22-060', 'invoice_date': '2022-08-08', 'invoice_amount': 10000.00,
     'payment_date': '2022-09-01', 'payment_amount': 10000.00, 'status': 'paid', 'notes': 'WP3B stage F1 3/4'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Documents',
     'invoice_number': 'I22-068', 'invoice_date': '2022-09-14', 'invoice_amount': 12500.00,
     'payment_date': '2022-09-30', 'payment_amount': 12500.00, 'status': 'paid', 'notes': 'WP3B stage F1 4/4'},
    # Construction Observation - 29 installments of $8,000 (or $8,500 for first few)
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I23-089', 'invoice_date': '2023-11-15', 'invoice_amount': 8500.00,
     'payment_date': '2023-12-01', 'payment_amount': 8500.00, 'status': 'paid', 'notes': 'CO installment 1'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I23-090', 'invoice_date': '2023-11-15', 'invoice_amount': 8000.00,
     'payment_date': '2023-12-01', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 2'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I23-091', 'invoice_date': '2023-11-15', 'invoice_amount': 8000.00,
     'payment_date': '2023-12-01', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 3'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I23-092', 'invoice_date': '2023-11-15', 'invoice_amount': 8000.00,
     'payment_date': '2023-12-01', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 4'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I23-105', 'invoice_date': '2023-12-07', 'invoice_amount': 8000.00,
     'payment_date': '2024-06-03', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 5'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I24-004', 'invoice_date': '2024-01-29', 'invoice_amount': 8000.00,
     'payment_date': '2024-02-29', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 6'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I24-012', 'invoice_date': '2024-02-19', 'invoice_amount': 8000.00,
     'payment_date': '2024-03-28', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 7'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I24-016', 'invoice_date': '2024-03-11', 'invoice_amount': 8000.00,
     'payment_date': '2024-04-30', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 8'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I24-027', 'invoice_date': '2024-04-02', 'invoice_amount': 8000.00,
     'payment_date': '2024-04-30', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 9'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I24-030', 'invoice_date': '2024-05-13', 'invoice_amount': 8000.00,
     'payment_date': '2024-05-31', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 10'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I24-036', 'invoice_date': '2024-06-03', 'invoice_amount': 8000.00,
     'payment_date': '2024-08-02', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 11'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I24-043', 'invoice_date': '2024-07-08', 'invoice_amount': 8000.00,
     'payment_date': '2024-08-30', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 12'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I24-050', 'invoice_date': '2024-08-06', 'invoice_amount': 8000.00,
     'payment_date': '2024-08-30', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 13'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I24-068', 'invoice_date': '2024-09-02', 'invoice_amount': 8000.00,
     'payment_date': '2024-09-30', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 14'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I24-077', 'invoice_date': '2024-10-01', 'invoice_amount': 8000.00,
     'payment_date': '2024-11-19', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 15'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I24-085', 'invoice_date': '2024-11-11', 'invoice_amount': 8000.00,
     'payment_date': '2024-12-29', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 16'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I24-091', 'invoice_date': '2024-12-02', 'invoice_amount': 8000.00,
     'payment_date': '2025-01-03', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 17'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I25-003', 'invoice_date': '2025-01-07', 'invoice_amount': 8000.00,
     'payment_date': '2025-01-31', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 18'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I25-012', 'invoice_date': '2025-02-03', 'invoice_amount': 8000.00,
     'payment_date': '2025-02-28', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 19'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I25-024', 'invoice_date': '2025-03-07', 'invoice_amount': 8000.00,
     'payment_date': '2025-04-01', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 20'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I25-032', 'invoice_date': '2025-04-09', 'invoice_amount': 8000.00,
     'payment_date': '2025-05-02', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 21'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I25-049', 'invoice_date': '2025-05-05', 'invoice_amount': 8000.00,
     'payment_date': '2025-06-06', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 22'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I25-062', 'invoice_date': '2025-06-06', 'invoice_amount': 8000.00,
     'payment_date': '2025-06-30', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 23'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I25-068', 'invoice_date': '2025-07-03', 'invoice_amount': 8000.00,
     'payment_date': '2025-07-31', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 24'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I25-087', 'invoice_date': '2025-08-26', 'invoice_amount': 8000.00,
     'payment_date': '2025-10-06', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 25'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I25-102', 'invoice_date': '2025-10-10', 'invoice_amount': 8000.00,
     'payment_date': '2025-11-03', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 26'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I25-103', 'invoice_date': '2025-10-10', 'invoice_amount': 8000.00,
     'payment_date': '2025-11-03', 'payment_amount': 8000.00, 'status': 'paid', 'notes': 'CO installment 27'},
    {'project_code': '20 BK-047', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I25-116', 'invoice_date': '2025-11-10', 'invoice_amount': 8000.00,
     'payment_date': None, 'payment_amount': 0, 'status': 'outstanding', 'notes': 'CO installment 28 - UNPAID'},
    # Note: 29th installment not yet invoiced, plus addendum for 14 more installments of $12,000 starting Jan 2026

    # ===== 20 BK-092: Resort Udaipur - Landscape Architecture =====
    {'project_code': '20 BK-092', 'discipline': 'Landscape Architecture', 'phase': 'Mobilization',
     'invoice_number': 'I20-094', 'invoice_date': '2020-11-24', 'invoice_amount': 50000.00,
     'payment_date': '2020-12-03', 'payment_amount': 50000.00, 'status': 'paid'},
    {'project_code': '20 BK-092', 'discipline': 'Landscape Architecture', 'phase': 'Concept Design',
     'invoice_number': 'I21-023', 'invoice_date': '2021-03-15', 'invoice_amount': 31312.00,
     'payment_date': '2021-05-19', 'payment_amount': 31312.00, 'status': 'paid', 'notes': '19% of concept design'},
    {'project_code': '20 BK-092', 'discipline': 'Landscape Architecture', 'phase': 'Concept Design',
     'invoice_number': 'I22-013', 'invoice_date': '2022-02-21', 'invoice_amount': 133488.00,
     'payment_date': '2022-07-15', 'payment_amount': 133488.00, 'status': 'paid', 'notes': '81% of concept design'},
    {'project_code': '20 BK-092', 'discipline': 'Landscape Architecture', 'phase': 'Design Development',
     'invoice_number': 'I22-072', 'invoice_date': '2022-09-22', 'invoice_amount': 80550.00,
     'payment_date': '2022-12-14', 'payment_amount': 80550.00, 'status': 'paid', 'notes': '50% of DD'},
    {'project_code': '20 BK-092', 'discipline': 'Landscape Architecture', 'phase': 'Design Development',
     'invoice_number': 'I22-087', 'invoice_date': '2022-12-06', 'invoice_amount': 80550.00,
     'payment_date': '2023-08-23', 'payment_amount': 80550.00, 'status': 'paid', 'notes': '50% of DD'},
    {'project_code': '20 BK-092', 'discipline': 'Landscape Architecture', 'phase': 'Construction Documents',
     'invoice_number': 'I24-053', 'invoice_date': '2024-08-26', 'invoice_amount': 80550.00,
     'payment_date': '2025-10-16', 'payment_amount': 80550.00, 'status': 'paid', 'notes': '100% of CD'},
    {'project_code': '20 BK-092', 'discipline': 'Landscape Architecture', 'phase': 'Construction Observation',
     'invoice_number': 'I25-020', 'invoice_date': '2025-03-07', 'invoice_amount': 8550.00,
     'payment_date': '2025-10-16', 'payment_amount': 8550.00, 'status': 'paid', 'notes': '100% of CO'},

    # ===== 20 BK-092: Resort Udaipur - Architecture =====
    {'project_code': '20 BK-092', 'discipline': 'Architecture', 'phase': 'Mobilization',
     'invoice_number': 'I20-094-A', 'invoice_date': '2020-11-24', 'invoice_amount': 70000.00,
     'payment_date': '2020-12-03', 'payment_amount': 70000.00, 'status': 'paid'},
    {'project_code': '20 BK-092', 'discipline': 'Architecture', 'phase': 'Concept Design',
     'invoice_number': 'I21-023-A', 'invoice_date': '2021-03-15', 'invoice_amount': 115600.00,
     'payment_date': '2021-05-19', 'payment_amount': 115600.00, 'status': 'paid', 'notes': '50% of concept design'},
    {'project_code': '20 BK-092', 'discipline': 'Architecture', 'phase': 'Concept Design',
     'invoice_number': 'I22-013-A', 'invoice_date': '2022-02-21', 'invoice_amount': 115600.00,
     'payment_date': '2022-07-15', 'payment_amount': 115600.00, 'status': 'paid', 'notes': '50% of concept design'},
    {'project_code': '20 BK-092', 'discipline': 'Architecture', 'phase': 'Design Development',
     'invoice_number': 'I22-072-A', 'invoice_date': '2022-09-22', 'invoice_amount': 112950.00,
     'payment_date': '2022-12-14', 'payment_amount': 112950.00, 'status': 'paid', 'notes': '50% of DD'},
    {'project_code': '20 BK-092', 'discipline': 'Architecture', 'phase': 'Design Development',
     'invoice_number': 'I22-087-A', 'invoice_date': '2022-12-06', 'invoice_amount': 112950.00,
     'payment_date': '2023-08-23', 'payment_amount': 112950.00, 'status': 'paid', 'notes': '50% of DD'},
    {'project_code': '20 BK-092', 'discipline': 'Architecture', 'phase': 'Construction Documents',
     'invoice_number': 'I24-047', 'invoice_date': '2024-08-02', 'invoice_amount': 112950.00,
     'payment_date': '2025-04-01', 'payment_amount': 112950.00, 'status': 'paid', 'notes': '100% of CD'},
    {'project_code': '20 BK-092', 'discipline': 'Architecture', 'phase': 'Construction Observation',
     'invoice_number': 'I24-054', 'invoice_date': '2024-08-26', 'invoice_amount': 28237.50,
     'payment_date': '2025-10-16', 'payment_amount': 28237.50, 'status': 'paid', 'notes': '25% of CO'},
    {'project_code': '20 BK-092', 'discipline': 'Architecture', 'phase': 'Construction Observation',
     'invoice_number': 'I25-021', 'invoice_date': '2025-03-07', 'invoice_amount': 84712.50,
     'payment_date': '2025-10-27', 'payment_amount': 84712.50, 'status': 'paid', 'notes': '75% of CO'},

    # ===== 20 BK-092: Resort Udaipur - Interior Design =====
    {'project_code': '20 BK-092', 'discipline': 'Interior Design', 'phase': 'Mobilization',
     'invoice_number': 'I20-094-I', 'invoice_date': '2020-11-24', 'invoice_amount': 80000.00,
     'payment_date': '2020-12-03', 'payment_amount': 80000.00, 'status': 'paid'},
    {'project_code': '20 BK-092', 'discipline': 'Interior Design', 'phase': 'Concept Design',
     'invoice_number': 'I21-023-I', 'invoice_date': '2021-03-15', 'invoice_amount': 52720.00,
     'payment_date': '2021-05-19', 'payment_amount': 52720.00, 'status': 'paid', 'notes': '20% of concept design'},
    {'project_code': '20 BK-092', 'discipline': 'Interior Design', 'phase': 'Concept Design',
     'invoice_number': 'I22-013-I', 'invoice_date': '2022-02-21', 'invoice_amount': 210880.00,
     'payment_date': '2022-07-15', 'payment_amount': 210880.00, 'status': 'paid', 'notes': '80% of concept design'},
    {'project_code': '20 BK-092', 'discipline': 'Interior Design', 'phase': 'Design Development',
     'invoice_number': 'I22-072-I', 'invoice_date': '2022-09-22', 'invoice_amount': 128850.00,
     'payment_date': '2022-12-14', 'payment_amount': 128850.00, 'status': 'paid', 'notes': '50% of DD'},
    {'project_code': '20 BK-092', 'discipline': 'Interior Design', 'phase': 'Design Development',
     'invoice_number': 'I22-088', 'invoice_date': '2022-12-06', 'invoice_amount': 128850.00,
     'payment_date': '2024-08-22', 'payment_amount': 128850.00, 'status': 'paid', 'notes': '50% of DD'},
    {'project_code': '20 BK-092', 'discipline': 'Interior Design', 'phase': 'Construction Documents',
     'invoice_number': 'I24-055', 'invoice_date': '2024-08-26', 'invoice_amount': 64425.00,
     'payment_date': '2025-02-10', 'payment_amount': 64425.00, 'status': 'paid', 'notes': '50% of CD'},
    {'project_code': '20 BK-092', 'discipline': 'Interior Design', 'phase': 'Construction Documents',
     'invoice_number': 'I24-071', 'invoice_date': '2024-09-09', 'invoice_amount': 64425.00,
     'payment_date': '2025-02-10', 'payment_amount': 64425.00, 'status': 'paid', 'notes': '50% of CD'},
    {'project_code': '20 BK-092', 'discipline': 'Interior Design', 'phase': 'Construction Observation',
     'invoice_number': 'I25-022', 'invoice_date': '2025-03-07', 'invoice_amount': 128850.00,
     'payment_date': '2025-10-27', 'payment_amount': 128850.00, 'status': 'paid', 'notes': '100% of CO'},
]

# 19 BK-018 already has 28 invoices - skip for now as it may be complete


def get_project_id(conn, project_code: str) -> Optional[int]:
    """Get project_id from project_code"""
    c = conn.cursor()
    c.execute('SELECT project_id FROM projects WHERE project_code = ?', (project_code,))
    result = c.fetchone()
    return result[0] if result else None


def invoice_exists(conn, invoice_number: str) -> bool:
    """Check if invoice already exists"""
    c = conn.cursor()
    c.execute('SELECT 1 FROM invoices WHERE invoice_number = ?', (invoice_number,))
    return c.fetchone() is not None


def import_invoices(dry_run: bool = True):
    """Import all invoices from the transcription data"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    stats = {
        'total': len(INVOICE_DATA),
        'imported': 0,
        'skipped_exists': 0,
        'skipped_no_project': 0,
        'errors': 0
    }

    print(f"{'DRY RUN - ' if dry_run else ''}Importing {len(INVOICE_DATA)} invoices...")
    print("=" * 60)

    for inv in INVOICE_DATA:
        project_code = inv['project_code']
        invoice_number = inv['invoice_number']

        # Get project_id
        project_id = get_project_id(conn, project_code)
        if not project_id:
            print(f"⚠️  Project not found: {project_code} - skipping {invoice_number}")
            stats['skipped_no_project'] += 1
            continue

        # Check if invoice exists
        if invoice_exists(conn, invoice_number):
            print(f"⏭️  Invoice exists: {invoice_number}")
            stats['skipped_exists'] += 1
            continue

        try:
            if not dry_run:
                c.execute('''
                    INSERT INTO invoices (
                        project_id, invoice_number, invoice_date,
                        invoice_amount, payment_date, payment_amount,
                        status, notes, source_type, source_reference
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    project_id,
                    invoice_number,
                    inv['invoice_date'],
                    inv['invoice_amount'],
                    inv.get('payment_date'),
                    inv.get('payment_amount', 0),
                    inv.get('status', 'paid'),
                    inv.get('notes', ''),
                    'voice_transcription',
                    'project_status_17nov2025_excel'
                ))

            stats['imported'] += 1
            status_icon = '✅' if inv.get('status') == 'paid' else '⚠️'
            print(f"{status_icon} {project_code} | {invoice_number} | ${inv['invoice_amount']:,.2f} | {inv.get('status', 'paid')}")

        except Exception as e:
            print(f"❌ Error importing {invoice_number}: {e}")
            stats['errors'] += 1

    if not dry_run:
        conn.commit()

    conn.close()

    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print(f"Total invoices: {stats['total']}")
    print(f"Imported: {stats['imported']}")
    print(f"Skipped (exists): {stats['skipped_exists']}")
    print(f"Skipped (no project): {stats['skipped_no_project']}")
    print(f"Errors: {stats['errors']}")

    if dry_run:
        print("\n⚠️  DRY RUN - No changes made. Run with --commit to import.")

    return stats


def update_project_name():
    """Update 16 BK-076 project name"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE projects
        SET project_title = 'JW Marriott Resort Jeju, South Korea - Landscape Architecture'
        WHERE project_code = '16 BK-076' AND (project_title IS NULL OR project_title = '')
    ''')
    if c.rowcount > 0:
        print("✅ Updated 16 BK-076 project name")
    conn.commit()
    conn.close()


if __name__ == '__main__':
    import sys

    # Update project name first
    update_project_name()

    # Check for --commit flag
    if '--commit' in sys.argv:
        print("\n🚀 COMMITTING CHANGES TO DATABASE\n")
        import_invoices(dry_run=False)
    else:
        print("\n📋 DRY RUN MODE - Preview only\n")
        import_invoices(dry_run=True)
        print("\nTo actually import, run: python3 scripts/imports/import_voice_transcription_invoices.py --commit")
