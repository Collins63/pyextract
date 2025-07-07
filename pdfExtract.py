# app.py
from flask import Flask, request, jsonify , send_file
import pdfplumber
import re
import qrcode
from PIL import Image
import io
import os
import fitz # PyMuPDF



app = Flask(__name__)

# @app.route('/extract_invoice', methods=['POST'])
# def extract_invoice():
#     file = request.files['file']
#     with pdfplumber.open(file) as pdf:
#         page = pdf.pages[0]
#         text = page.extract_text()

#         # Extract line items table
#         table = page.extract_table()
#         line_items = []
#         if table and len(table) > 1:
#             headers = table[0]
#             for row in table[1:]:
#                 item = dict(zip(headers, row))
#                 description = item.get('Description')
#                 if description and description.strip():
#                     line_items.append(item)

#         # Function to extract field using regex
#         def extract_field(pattern):
#             match = re.search(pattern, text, re.IGNORECASE)
#             if match and match.group(1):
#                 return match.group(1).strip()
#             return None

#         # Detect document type
#         is_credit_note = "FISCAL CREDIT NOTE" in text.upper()

#         # Common fields
#         tin = extract_field(r'TIN Number:\s*(\d{10})')
#         vat = extract_field(r'VAT Number:\s*(\d{9,12})')
#         email = extract_field(r'Customer Email Address:\s*([\w\.-]+@[\w\.-]+)?')
#         phone = extract_field(r'Customer Phone Number:\s*(\d{7,15})')
#         currency = extract_field(r'Currency:\s*([A-Z]+)')
#         customer_name = extract_field(r'Customer:\s*(.+)')
        
#         result = {
#             "document_type": "credit_note" if is_credit_note else "invoice",
#             "line_items": line_items,
#         }

#         if is_credit_note:
#             credit_note_number = extract_field(r'Credit Note #:\s*(\d+)')
#             reason_for_credit = extract_field(r'Reason for Credit:\s*(.+)')
#             reference_number = extract_field(r'Reference #:\s*(\d+)')

#             result["credit_note_details"] = {
#                 "buyer_tin": tin,
#                 "buyer_vat": vat,
#                 "email": email,
#                 "phone": phone,
#                 "currency": currency,
#                 "credit_note_number": credit_note_number,
#                 "reason_for_credit": reason_for_credit,
#                 "reference_number": reference_number
#             }
#         else:
#             invoice_number = extract_field(r'Invoice #:\s*(\d+)')
#             invoice_total = extract_field(r'Invoice Total\s*([\d.]+)')

#             result["invoice_details"] = {
#                 "customer_name" : customer_name,
#                 "buyer_tin": tin,
#                 "buyer_vat": vat,
#                 "email": email,
#                 "phone": phone,
#                 "currency": currency,
#                 "invoice_number": invoice_number,
#                 "invoice_total": invoice_total
#             }

#         return jsonify(result)

@app.route('/extract_invoice', methods=['POST'])
def extract_invoice():
    file = request.files['file']
    with pdfplumber.open(file) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()

        # Extract line items table
        table = page.extract_table()
        line_items = []
        if table and len(table) > 1:
            headers = table[0]
            for row in table[1:]:
                item = dict(zip(headers, row))
                description = item.get('Description')
                if description and description.strip():
                    line_items.append(item)

        # Extract field (first match)
        def extract_field(pattern):
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.group(1):
                return match.group(1).strip()
            return None

        # Extract last occurrence (e.g., for buyer's TIN/VAT at bottom)
        def extract_last_field(pattern):
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[-1].strip()
            return None

        # Safely extract customer name before product section
        def extract_customer_name(text):
            pattern = r'Customer:\s*(.*)'
            lines = text.splitlines()
            for line in lines:
                match = re.match(pattern, line.strip(), re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    # Remove anything that looks like a date or next label
                    name = re.split(r'Date:|\d{1,2}/\d{1,2}/\d{4}', name)[0].strip()
                    return name
            return None

        # Detect document type
        is_credit_note = "FISCAL CREDIT NOTE" in text.upper()

        # Extract relevant fields
        tin = extract_last_field(r'TIN Number:\s*(\d{10})')     # Buyer's TIN (last one on page)
        vat = extract_last_field(r'VAT Number:\s*(\d{9,12})')   # Buyer's VAT (last one on page)
        email = extract_field(r'Customer Email Address:\s*([\w\.-]+@[\w\.-]+)?')
        phone = extract_field(r'Customer Phone Number:\s*(\d{7,15})')
        currency = extract_field(r'Currency:\s*([A-Z]+)')
        customer_name = extract_customer_name(text)

        # Result dictionary
        result = {
            "document_type": "credit_note" if is_credit_note else "invoice",
            "line_items": line_items,
        }

        if is_credit_note:
            credit_note_number = extract_field(r'Credit Note #:\s*(\d+)')
            reason_for_credit = extract_field(r'Reason for Credit:\s*(.+)')
            reference_number = extract_field(r'Reference #:\s*(\d+)')

            result["credit_note_details"] = {
                "customer_name": customer_name,
                "buyer_tin": tin,
                "buyer_vat": vat,
                "email": email,
                "phone": phone,
                "currency": currency,
                "credit_note_number": credit_note_number,
                "reason_for_credit": reason_for_credit,
                "reference_number": reference_number
            }
        else:
            invoice_number = extract_field(r'Invoice #:\s*(\d+)')
            invoice_total = extract_field(r'Invoice Total\s*([\d.]+)')

            result["invoice_details"] = {
                "customer_name": customer_name,
                "buyer_tin": tin,
                "buyer_vat": vat,
                "email": email,
                "phone": phone,
                "currency": currency,
                "invoice_number": invoice_number,
                "invoice_total": invoice_total
            }

        return jsonify(result)


# @app.route('/extract_receipt', methods=['POST'])
# def extract_receipt():
#     file = request.files['file']
#     with pdfplumber.open(file) as pdf:
#         page = pdf.pages[0]
#         text = page.extract_text()

#         # Helper functions
#         def extract_field(pattern):
#             match = re.search(pattern, text, re.IGNORECASE)
#             if match:
#                 return match.group(1).strip()
#             return None

#         def extract_all_line_items(text):
#             # line_pattern = r'(?:Z|T|E):\s*([\d]+)\s*:\s*(.*?)\n\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)'
#             line_pattern = r'([EZT]):\s*(\d+)\s*:\s*(.*?)\n\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)'
#             matches = re.findall(line_pattern, text)
#             items = []
#             for tax_letter ,code, desc, qty, unit_price, vat, total in matches:
#                 items.append({
#                     "tax_letter": tax_letter,
#                     "hs_code": code,
#                     "description": desc.strip(),
#                     "quantity": int(qty),
#                     "unit_price": float(unit_price),
#                     "vat": float(vat),
#                     "amount_incl": float(total)
#                 })
#             return items
        
#         def extract_customer_name(text):
#             pattern = r'^Customer:\s*(\S.+)?$'  # Only matches if there's something after the colon
#             lines = text.splitlines()
#             for line in lines:
#                 match = re.match(pattern, line.strip(), re.IGNORECASE)
#                 if match:
#                     name = match.group(1)
#                     if name:
#                         # Trim off anything that looks like a date or accidental spillover
#                         name = re.split(r'Date:|\d{1,2}/\d{1,2}/\d{4}', name)[0].strip()
#                         return name
#                     else:
#                         return None  # Line matched but no actual name
#             return None

#         # Extract fields
#         invoice_number = extract_field(r'Invoice Number:\s*(\d+)')
#         invoice_date = extract_field(r'Invoice Date:\s*([\d/]+)')
#         invoice_time = extract_field(r'Invoice Time:\s*(\d{4})')

#         customer_name = extract_customer_name(text)
#         address = extract_field(r'Address:\s*(.*)')
#         phone = extract_field(r'Phone #:\s*(\d{7,15})')
#         tin = extract_field(r'TIN Number:\s*(\d{10})')
#         vat_number = extract_field(r'VAT Number:\s*(\d{9,12})')
#         email = extract_field(r'Email:\s*([\w\.-]+@[\w\.-]+)')
#         currency = extract_field(r'HS Code\s*:\s*Description\s+([A-Z]{3})')

#         invoice_subtotal = extract_field(r'Inv\. Subtotal:\s*([\d.]+)')
#         total_vat = extract_field(r'Total VAT:\s*([\d.]+)')
#         discount = extract_field(r'Inv\. Discount:\s*([\d.]+)')
#         invoice_total = extract_field(r'Invoice Total:\s*([\d.]+)')
#         paid = extract_field(r'PAID:\s*([\d.]+)')
#         change = extract_field(r'CHANGE:\s*([\d.]+)')

#         line_items = extract_all_line_items(text)

#         result = {
#             "document_type": "receipt",
#             "invoice_number": invoice_number,
#             "invoice_date": invoice_date,
#             "invoice_time": invoice_time,
#             "invoice_currency": currency,
#             "customer_details": {
#                 "name": customer_name,
#                 "address": address,
#                 "phone": phone,
#                 "email": email,
#                 "tin": tin,
#                 "vat_number": vat_number,
#             },
#             "line_items": line_items,
#             "totals": {
#                 "invoice_subtotal": invoice_subtotal,
#                 "total_vat": total_vat,
#                 "discount": discount,
#                 "invoice_total": invoice_total,
#                 "paid": paid,
#                 "change": change
#             }
#         }

#         return jsonify(result)
@app.route('/extract_receipt', methods=['POST'])
def extract_receipt():
    file = request.files['file']
    with pdfplumber.open(file) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()

        # Helper functions
        def extract_field(pattern):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            return None

        # def extract_all_line_items(text):
        #     line_pattern = r'([EZT]):\s*(\d+)\s*-\s*(.*?)\n\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)'
        #     matches = re.findall(line_pattern, text)
        #     items = []
        #     for tax_letter, code, desc, qty, unit_price, vat, total in matches:
        #         items.append({
        #             "tax_letter": tax_letter,
        #             "hs_code": code,
        #             "description": desc.strip(),
        #             "quantity": int(qty),
        #             "unit_price": float(unit_price),
        #             "vat": float(vat),
        #             "amount_incl": float(total)
        #         })
        #     return items
        
        def extract_all_line_items(text):
            # line_pattern = r'(?:Z|T|E):\s*([\d]+)\s*:\s*(.*?)\n\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)'
            line_pattern = r'([EZT]):\s*(\d+)\s*:\s*(.*?)\n\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)'
            matches = re.findall(line_pattern, text)
            items = []
            for tax_letter ,code, desc, qty, unit_price, vat, total in matches:
                items.append({
                    "tax_letter": tax_letter,
                    "hs_code": code,
                    "description": desc.strip(),
                    "quantity": int(qty),
                    "unit_price": float(unit_price),
                    "vat": float(vat),
                    "amount_incl": float(total)
                })
            return items
        
        # Helper function to parse the address
        def parse_address(raw_address):
            parts = [part.strip() for part in raw_address.split(',')]
            return {
                "houseNo": parts[0] if len(parts) > 0 else None,
                "street": parts[1] if len(parts) > 1 else None,
                "city": parts[2] if len(parts) > 2 else None,
                "province": parts[3] if len(parts) > 3 else None,
                "country": "Zimbabwe"
            }


        def extract_customer_name(text):
            pattern = r'^Customer:\s*(\S.+)?$'
            lines = text.splitlines()
            for line in lines:
                match = re.match(pattern, line.strip(), re.IGNORECASE)
                if match:
                    name = match.group(1)
                    if name:
                        name = re.split(r'Date:|\d{1,2}/\d{1,2}/\d{4}', name)[0].strip()
                        return name
                    else:
                        return None
            return None

        # Detect document type
        is_credit_note = "CREDIT NOTE" in text.upper()

        # Common fields
        invoice_number = extract_field(r'Invoice Number:\s*(\d+)')
        invoice_date = extract_field(r'Invoice Date:\s*([\d/]+)')
        invoice_time = extract_field(r'Invoice Time:\s*(\d{4})')
        currency = extract_field(r'HS Code\s*:\s*Description\s+([A-Z]{3})')

        line_items = extract_all_line_items(text)

        result = {
            "document_type": "credit_note" if is_credit_note else "receipt",
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "invoice_time": invoice_time,
            "invoice_currency": currency,
            "line_items": line_items,
            "totals": {
                "invoice_subtotal": extract_field(r'Inv\. Subtotal:\s*([\d.]+)'),
                "total_vat": extract_field(r'Total VAT:\s*([\d.]+)'),
                "discount": extract_field(r'Inv\. Discount:\s*([\d.]+)'),
                "invoice_total": extract_field(r'Invoice Total:\s*([\d.]+)'),
                "paid": extract_field(r'PAID:\s*([\d.]+)'),
                "change": extract_field(r'CHANGE:\s*([\d.]+)')
            }
        }

        # Customer info (for receipts)
        if not is_credit_note:
            raw_address = extract_field(r'Address:\s*(.*)')
            result["customer_details"] = {
                "name": extract_customer_name(text),
                "buyerAddress": parse_address(raw_address) if raw_address else {},
                "phone": extract_field(r'Phone #:\s*(\d{7,15})'),
                "email": extract_field(r'Email:\s*([\w\.-]+@[\w\.-]+)'),
                "tin": extract_field(r'TIN Number:\s*(\d{10})'),
                "vat_number": extract_field(r'VAT Number:\s*(\d{9,12})'),
            }

        # Credit note-specific fields
        if is_credit_note:
            result["credit_note_details"] = {
                "credit_note_number": extract_field(r'Credit Note Number:\s*(\d+)'),
                "reason_for_credit": extract_field(r'Comments:\s*(.+)'),
                "reference_number": invoice_number
            }

        return jsonify(result)


    
@app.route('/stamp_invoice', methods=['POST'])
def stamp_invoice():
    file = request.files['file']
    day_no = request.form.get('day_no', '001')
    receipt_global_no = request.form.get('receipt_global_no', 'RGN00000000')
    signature = request.form.get('signature', '')

    qr_data = signature
    
    # Save uploaded file temporarily
    temp_input = "temp_invoice.pdf"
    file.save(temp_input)

    # Generate QR code
    qr = qrcode.make(qr_data)
    qr_path = "temp_qr.png"
    qr.save(qr_path)

    # Load PDF and stamp it
    doc = fitz.open(temp_input)
    page = doc[0]

    # Insert QR code image
    qr_rect = fitz.Rect(50, 720, 150, 820)
    page.insert_image(qr_rect, filename=qr_path)
    
    # Insert text to the right of QR code
    text = f"Day No: {day_no}   |   Receipt Global No: {receipt_global_no}"
    text_position = fitz.Point(160, 130)  # Slightly higher to vertically align with QR
    page.insert_text(text_position, text, fontsize=10, fontname="helv", color=(0, 0, 0))

    output_dir = r"C:/Fiscal/Done"  # use raw string or escape backslashes
    os.makedirs(output_dir, exist_ok=True)
    
    output_pdf_path = os.path.join(output_dir, f"Pharmacute_{receipt_global_no}.pdf")
    doc.save(output_pdf_path)
    doc.close()

    return send_file(output_pdf_path, as_attachment=True)
    

if __name__ == '__main__':
    app.run(debug=True)
