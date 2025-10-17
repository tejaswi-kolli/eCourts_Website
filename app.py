from flask import Flask, render_template, request, send_file, jsonify
from io import BytesIO
from datetime import datetime
from reportlab.pdfgen import canvas
import zipfile

app = Flask(__name__)

# --- Dropdown endpoints ---
@app.route("/fetch_states")
def fetch_states():
    sample = [
        {"value": "AP", "label": "Andhra Pradesh"},
        {"value": "TS", "label": "Telangana"},
        {"value": "TN", "label": "Tamil Nadu"}
    ]
    return jsonify({"success": True, "items": sample})

@app.route("/fetch_districts")
def fetch_districts():
    state = request.args.get("state", "")
    fallback = []
    if state == "AP":
        fallback = [{"value": "Krishna", "label": "Krishna"}, {"value": "Guntur", "label": "Guntur"}]
    elif state == "TS":
        fallback = [{"value": "Hyderabad", "label": "Hyderabad"}, {"value": "Warangal", "label": "Warangal"}]
    elif state == "TN":
        fallback = [{"value": "Chennai", "label": "Chennai"}, {"value": "Coimbatore", "label": "Coimbatore"}]
    return jsonify({"success": True, "items": fallback})

@app.route("/fetch_complexes")
def fetch_complexes():
    district = request.args.get("district", "")
    fallback = [
        {"value": "Complex 1", "label": f"{district} - Court Complex 1"},
        {"value": "Complex 2", "label": f"{district} - Court Complex 2"},
    ]
    return jsonify({"success": True, "items": fallback})

@app.route("/fetch_courts")
def fetch_courts():
    complex_name = request.args.get("complex", "")
    fallback = [
        {"value": "Court 1", "label": f"{complex_name} - Court 1"},
        {"value": "Court 2", "label": f"{complex_name} - Court 2"},
    ]
    return jsonify({"success": True, "items": fallback})

# --- Download PDFs ---
@app.route("/download", methods=["POST"])
def download():
    state = request.form.get("state", "")
    district = request.form.get("district", "")
    complex_name = request.form.get("complex", "")
    court = request.form.get("court", "")
    download_all = request.form.get("download_all") == "on"

    # Validate selections
    if not all([state, district, complex_name, court]):
        return jsonify({"success": False, "error": "Please select all dropdowns."}), 400

    # Function to create PDF bytes for given inputs
    def create_pdf_bytes(state, district, complex_name, court):
        buffer = BytesIO()
        c = canvas.Canvas(buffer)
        c.setFont("Helvetica", 14)
        y = 800
        c.drawString(50, y, f"State: {state}"); y -= 30
        c.drawString(50, y, f"District: {district}"); y -= 30
        c.drawString(50, y, f"Complex: {complex_name}"); y -= 30
        c.drawString(50, y, f"Court: {court}"); y -= 30
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    # If download_all is checked, create separate PDFs for each selection and zip them
    if download_all:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Create PDF for this selection
            pdf_bytes = create_pdf_bytes(state, district, complex_name, court)
            filename = f"{state}_{district}_{complex_name}_{court}.pdf".replace(" ", "_")
            zf.writestr(filename, pdf_bytes.read())
        zip_buffer.seek(0)
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        return send_file(zip_buffer, as_attachment=True, download_name=f"ecourts_pdfs_{now}.zip", mimetype="application/zip")

    # Else, just download one PDF
    pdf_bytes = create_pdf_bytes(state, district, complex_name, court)
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{state}_{district}_{complex_name}_{court}.pdf".replace(" ", "_")
    return send_file(pdf_bytes, as_attachment=True, download_name=filename, mimetype="application/pdf")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
