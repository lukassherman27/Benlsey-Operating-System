"""
Contract API Routes

Endpoints for contract management and comparison
"""

from flask import Blueprint, request, jsonify, send_file
from backend.services.contract_service import ContractService
import os

contracts_bp = Blueprint('contracts', __name__)


@contracts_bp.route('/api/contracts', methods=['GET'])
def get_all_contracts():
    """
    Get all contracts with pagination and filtering

    Query params:
        - type: bensley_contract or external_contract
        - page: page number (default 1)
        - per_page: results per page (default 20)
        - sort_by: created_at, filename, filesize
        - sort_order: ASC or DESC
    """
    service = ContractService()

    contract_type = request.args.get('type')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'DESC')

    result = service.get_all_contracts(
        contract_type=contract_type,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return jsonify(result)


@contracts_bp.route('/api/contracts/stats', methods=['GET'])
def get_contract_stats():
    """Get contract statistics"""
    service = ContractService()
    stats = service.get_contract_stats()
    return jsonify(stats)


@contracts_bp.route('/api/contracts/project/<project_code>', methods=['GET'])
def get_contracts_for_project(project_code):
    """
    Get all contracts for a specific project

    Returns both Bensley and external contracts grouped by type
    """
    service = ContractService()
    contracts = service.get_all_contracts_for_project(project_code)
    return jsonify(contracts)


@contracts_bp.route('/api/contracts/project/<project_code>/latest', methods=['GET'])
def get_latest_contract_for_project(project_code):
    """
    Get the most recent contract for a project

    Query params:
        - type: bensley_contract or external_contract (optional)
    """
    service = ContractService()
    contract_type = request.args.get('type')

    contract = service.get_latest_contract_for_project(
        project_code=project_code,
        contract_type=contract_type
    )

    if contract:
        return jsonify(contract)
    else:
        return jsonify({'error': 'No contract found'}), 404


@contracts_bp.route('/api/contracts/search', methods=['GET'])
def search_contracts():
    """
    Search contracts by filename or subject

    Query params:
        - q: search term
        - limit: max results (default 10)
    """
    service = ContractService()
    search_term = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))

    if not search_term:
        return jsonify({'error': 'Search term required'}), 400

    results = service.find_contracts_by_filename(search_term, limit)
    return jsonify({'results': results})


@contracts_bp.route('/api/contracts/compare', methods=['GET'])
def compare_contracts():
    """
    Compare two contracts

    Query params:
        - id1: first attachment_id
        - id2: second attachment_id
    """
    service = ContractService()

    try:
        id1 = int(request.args.get('id1'))
        id2 = int(request.args.get('id2'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Both id1 and id2 required as integers'}), 400

    comparison = service.compare_contracts(id1, id2)
    return jsonify(comparison)


@contracts_bp.route('/api/contracts/<int:attachment_id>/versions', methods=['GET'])
def get_contract_versions(attachment_id):
    """Get version history for a contract"""
    service = ContractService()
    versions = service.get_contract_versions(attachment_id)
    return jsonify({'versions': versions})


@contracts_bp.route('/api/contracts/<int:attachment_id>/download', methods=['GET'])
def download_contract(attachment_id):
    """Download a contract file"""
    service = ContractService()

    # Get contract metadata
    sql = "SELECT filepath, filename FROM email_attachments WHERE attachment_id = ?"
    contract = service.execute_query(sql, (attachment_id,), fetch_one=True)

    if not contract:
        return jsonify({'error': 'Contract not found'}), 404

    filepath = contract['filepath']
    filename = contract['filename']

    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found on disk'}), 404

    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename
    )


@contracts_bp.route('/api/contracts/<int:attachment_id>', methods=['GET'])
def get_contract_detail(attachment_id):
    """Get detailed information about a contract"""
    service = ContractService()

    sql = """
        SELECT
            a.*,
            e.email_id,
            e.subject AS email_subject,
            e.sender_email,
            e.recipient_emails,
            e.date AS email_date,
            p.project_code,
            p.project_title
        FROM email_attachments a
        JOIN emails e ON a.email_id = e.email_id
        LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
        LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
        WHERE a.attachment_id = ?
    """
    contract = service.execute_query(sql, (attachment_id,), fetch_one=True)

    if not contract:
        return jsonify({'error': 'Contract not found'}), 404

    return jsonify(contract)
