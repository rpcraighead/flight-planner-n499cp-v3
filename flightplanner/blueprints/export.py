from flask import Blueprint, jsonify, request, Response
from flightplanner.services.pdf_export import generate_navlog_pdf

export_bp = Blueprint('export', __name__)


@export_bp.route('/pdf', methods=['POST'])
def export_pdf():
    data = request.json
    pdf_bytes = generate_navlog_pdf(data)
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': 'attachment; filename=navlog.pdf'}
    )
