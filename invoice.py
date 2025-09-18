import os
import random
import tempfile
import io
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, white, Color

try:
    from faker import Faker
    fake = Faker('en_US')
    FAKER_AVAILABLE = True
except ImportError:
    print("Warning: faker library not available. Invoice generation will use placeholder data.")
    fake = None
    FAKER_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    print("Warning: PyMuPDF library not available. PDF to image conversion will not be supported.")
    fitz = None
    PYMUPDF_AVAILABLE = False

try:
    from PIL import Image
    import pillow_heif
    # Enable HEIF support in Pillow
    pillow_heif.register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    print("HEIF support not available. Install with: pip install pillow-heif pillow")
    HEIF_AVAILABLE = False

class InvoiceGenerator:
    def __init__(self):
        self.width, self.height = letter
        self.phone_numbers = []
        self.include_contact_button = False
        self.account_name = None
        self.to_name = None

        # Define colors
        self.primary_text_color = Color(0.2, 0.2, 0.2)
        self.secondary_text_color = Color(0.5, 0.5, 0.5)
        self.table_header_bg = Color(0.25, 0.25, 0.25)
        self.amt_paid_bg = Color(0.95, 0.95, 0.95)
        self.button_bg_color = Color(0.25, 0.25, 0.25)
        self.button_text_color = white

    def convert_pdf_to_image(self, pdf_path, output_path, dpi=135):
        """Convert PDF to high-quality image using PyMuPDF"""
        if not PYMUPDF_AVAILABLE:
            print("Error: PyMuPDF not available. Cannot convert PDF to image.")
            return False
            
        try:
            doc = fitz.open(pdf_path)
            page = doc.load_page(0)  # Get first page
            mat = fitz.Matrix(dpi/72, dpi/72)  # 72 is default DPI
            pix = page.get_pixmap(matrix=mat)
            pix.save(output_path)
            doc.close()
            print(f"Converted to image: {output_path}")
            return True
        except Exception as e:
            print(f"Error converting PDF to image: {e}")
            return False

    def convert_pdf_to_heif(self, pdf_path, output_path, dpi=135):
        """Convert PDF to HEIF format using PyMuPDF and Pillow"""
        if not HEIF_AVAILABLE:
            print("HEIF support not available. Please install: pip install pillow-heif pillow")
            return False
            
        if not PYMUPDF_AVAILABLE:
            print("Error: PyMuPDF not available. Cannot convert PDF to HEIF.")
            return False
            
        try:
            # First convert PDF to image data using PyMuPDF
            doc = fitz.open(pdf_path)
            page = doc.load_page(0)  # Get first page
            mat = fitz.Matrix(dpi/72, dpi/72)  # 72 is default DPI
            pix = page.get_pixmap(matrix=mat)
            
            # Convert pixmap to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Save as HEIF
            img.save(output_path, format="HEIF")
            doc.close()
            print(f"Converted to HEIF: {output_path}")
            return True
        except Exception as e:
            print(f"Error converting PDF to HEIF: {e}")
            return False

    def get_random_logo(self):
        """Get random logo from well-known asset directories."""
        search_dirs = []

        env_dir = os.environ.get("SIMPLE_MAILER_LOGO_DIR")
        if env_dir:
            search_dirs.append(Path(env_dir).expanduser())

        module_dir = Path(__file__).resolve().parent
        search_dirs.append(module_dir / "logos")
        search_dirs.append(Path.cwd() / "logos")

        unique_dirs = []
        seen = set()
        for directory in search_dirs:
            if directory is None:
                continue
            try:
                resolved = directory.resolve()
            except FileNotFoundError:
                resolved = directory
            if resolved in seen:
                continue
            seen.add(resolved)
            unique_dirs.append(resolved)

        candidates = []
        for directory in unique_dirs:
            if not directory.exists():
                continue
            for pattern in ("*.png", "*.jpg", "*.jpeg"):
                candidates.extend(list(directory.glob(pattern)))

        if candidates:
            selected_logo = random.choice(candidates)
            print(f"Selected logo: {selected_logo}")
            return str(selected_logo)

        print("No logos found in available directories")
        return None

    def generate_company_name(self):
        """Generate random company name"""
        if FAKER_AVAILABLE:
            return fake.company()
        else:
            return "Sample Company LLC"

    def generate_address(self):
        """Generate random US address"""
        if FAKER_AVAILABLE:
            street = fake.street_address()
            city = fake.city()
            state = fake.state_abbr()
            zipcode = fake.zipcode()
            return street, city, state, zipcode
        else:
            return "123 Main St", "Sample City", "CA", "90210"

    def generate_invoice_data(self):
        """Generate all random invoice data"""
        header_line = "THIS IS A RENEWAL INVOICE. PLEASE DO NOT MAKE ANOTHER PAYMENT."
        company_name = self.generate_company_name()
        street, city, state, zipcode = self.generate_address()
        date = datetime.now().strftime("%d %b %Y")
        invoice_number = random.randint(100000, 999999)

        items = [
            {"name": "Zoom Antivirus", "description": "3 Years 4 Devices"},
            {"name": "Zoom Complimentary Plus", "description": "Premium Support"}
        ]

        total_target = random.uniform(399, 799)
        discount = random.uniform(15, 50)
        subtotal_before_tax_and_discount = (total_target + discount) / 1.1

        price1_ratio = random.uniform(0.7, 0.9)
        price1 = round(subtotal_before_tax_and_discount * price1_ratio, 2)
        price2 = round(subtotal_before_tax_and_discount - price1, 2)

        subtotal = price1 + price2
        tax = round(subtotal * 0.1, 2)
        total = round(subtotal - discount + tax, 2)

        notes = "We were able to complete the processing of your transaction, and a charge will be applied to your card in the very near future. Keep this email as proof of purchase and visit our website for instructions on how to download or activate your product."

        terms = [
            "All the content in the digital service is the property of the company and protected by copyright laws",
            "Our team is dedicated to providing you with the best possible service."
        ]

        # Add the final support line with provided phone numbers
        if len(self.phone_numbers) >= 2:
            final_support_line = f"If you want to check the status of your purchase or cancel it, please contact us at: {self.phone_numbers[0]} or {self.phone_numbers[1]}"
        elif len(self.phone_numbers) == 1:
            final_support_line = f"If you want to check the status of your purchase or cancel it, please contact us at: {self.phone_numbers[0]}"
        else:
            final_support_line = "If you want to check the status of your purchase or cancel it, please contact us."
        terms.append(final_support_line)

        return {
            'header_line': header_line, 'company_name': company_name, 'street': street,
            'city': city, 'state': state, 'zipcode': zipcode, 'date': date,
            'invoice_number': invoice_number,
            'items': [
                {'name': items[0]['name'], 'desc': items[0]['description'], 'qty': 1, 'price': price1},
                {'name': items[1]['name'], 'desc': items[1]['description'], 'qty': 1, 'price': price2}
            ],
            'subtotal': subtotal, 'discount': discount, 'tax': tax, 'total': total,
            'notes': notes, 'terms': terms
        }

    def wrap_text(self, text, canvas_obj, max_width, font_name="Helvetica", font_size=9):
        """Wrap text to fit within a specified width."""
        canvas_obj.setFont(font_name, font_size)
        lines = []
        words = text.split()
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if canvas_obj.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines

    def create_pdf(self, filename="invoice.pdf"):
        """Create the PDF invoice with professional styling."""
        data = self.generate_invoice_data()
        c = canvas.Canvas(filename, pagesize=letter)

        # === Header with Logo ===
        logo_path = self.get_random_logo()
        if logo_path:
            try:
                # Draw logo at top left
                c.drawImage(logo_path, 40, self.height - 100, 
                           width=120, height=50, 
                           preserveAspectRatio=True, mask='auto')
                print(f"Logo drawn successfully: {logo_path}")
            except Exception as e:
                print(f"Error drawing logo: {e}")
                # Continue without logo if there's an error
        
        # "INVOICE" Title (top right)
        c.setFont("Helvetica-Bold", 34)
        c.setFillColor(self.primary_text_color)
        c.drawRightString(self.width - 40, self.height - 60, "INVOICE")

        # Professional Payment Confirmation
        c.setFont("Helvetica", 10)
        c.setFillColor(self.primary_text_color)
        payment_messages = [
            "PAYMENT PROCESSED SUCCESSFULLY - TRANSACTION COMPLETE",
            "INVOICE PAID IN FULL - NO FURTHER ACTION REQUIRED",
            "PAYMENT CONFIRMED - SERVICES ACTIVATED",
            "TRANSACTION COMPLETED - THANK YOU FOR YOUR PAYMENT",
            "PAYMENT RECEIVED - ACCOUNT UPDATED SUCCESSFULLY"
        ]
        selected_message = random.choice(payment_messages)
        c.drawRightString(self.width - 40, self.height - 80, selected_message)

        left_margin = 40
        right_margin = self.width - 40

        # === Custom Top Section ===
        y_pos = self.height - 120
        
        # Account
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(self.primary_text_color)
        c.drawString(left_margin, y_pos, "Account:")
        c.setFont("Helvetica", 20)
        c.setFillColor(self.secondary_text_color)
        c.drawString(left_margin + 120, y_pos, f"{self.account_name}")
        y_pos -= 28
        
        # Support with provided phone numbers
        if len(self.phone_numbers) >= 1:
            c.setFont("Helvetica-Bold", 20)
            c.setFillColor(self.primary_text_color)
            c.drawString(left_margin, y_pos, f"Support: {self.phone_numbers[0]}")
            y_pos -= 20
            
            if len(self.phone_numbers) >= 2:
                c.setFont("Helvetica-Bold", 13)
                c.drawString(left_margin, y_pos, f"Alt: {self.phone_numbers[1]}")
                y_pos -= 30
            else:
                y_pos -= 10
        else:
            y_pos -= 10
        
        # Company Info
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(self.primary_text_color)
        c.drawString(left_margin, y_pos, data['company_name'])
        c.setFont("Helvetica", 11)
        c.setFillColor(self.secondary_text_color)
        y_pos -= 16
        c.drawString(left_margin, y_pos, data['street'])
        y_pos -= 14
        c.drawString(left_margin, y_pos, f"{data['city']}, {data['state']} {data['zipcode']}")
        y_pos -= 14
        c.drawString(left_margin, y_pos, "United States")

        # === Invoice Details (Right) ===
        details_y = self.height - 120
        details_x_label = self.width - 150
        c.setFont("Helvetica", 11)
        c.setFillColor(self.secondary_text_color)
        c.drawString(details_x_label, details_y, "Date:")
        c.drawRightString(right_margin, details_y, data['date'])
        details_y -= 18
        c.drawString(details_x_label, details_y, "Order No.:")
        c.drawRightString(right_margin, details_y, str(data['invoice_number']))
        details_y -= 18
        c.drawString(details_x_label, details_y, "Payment Status:")
        c.drawRightString(right_margin, details_y, "Done")
        details_y -= 90
        
        # Amount Paid Box
        box_height = 60
        box_width = (right_margin - details_x_label) + 20
        c.setFillColor(self.amt_paid_bg)
        c.rect(details_x_label - 10, details_y - 5, box_width, box_height, stroke=0, fill=1)
        center_x = details_x_label - 10 + box_width / 2
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(self.primary_text_color)
        c.drawCentredString(center_x, details_y + box_height // 2 + 8, "Amt Paid:")
        c.setFont("Helvetica-Bold", 26)
        c.drawCentredString(center_x, details_y + box_height // 2 - 14, f"${data['total']:.2f}")

        # === Items Table ===
        table_y = self.height - 340
        c.setFillColor(self.table_header_bg)
        c.rect(left_margin, table_y, self.width - (2 * left_margin), 25, stroke=0, fill=1)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left_margin + 10, table_y + 8, "Item")
        c.drawRightString(right_margin - 150, table_y + 8, "Qty")
        c.drawRightString(right_margin - 80, table_y + 8, "Price")
        c.drawRightString(right_margin - 10, table_y + 8, "Amount")

        # Items
        item_y = table_y - 25
        for item in data['items']:
            c.setFillColor(self.primary_text_color)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(left_margin + 10, item_y, item['name'])
            c.setFillColor(self.secondary_text_color)
            c.setFont("Helvetica", 10)
            c.drawString(left_margin + 10, item_y - 12, item['desc'])
            c.setFont("Helvetica", 11)
            c.drawRightString(right_margin - 150, item_y, str(item['qty']))
            c.drawRightString(right_margin - 80, item_y, f"${item['price']:.2f}")
            c.drawRightString(right_margin - 10, item_y, f"${item['price']:.2f}")
            item_y -= 45

        # === Totals ===
        totals_y = item_y
        c.setFont("Helvetica", 11)
        c.setFillColor(self.secondary_text_color)
        c.drawRightString(right_margin - 80, totals_y, "Subtotal:")
        c.drawRightString(right_margin - 10, totals_y, f"${data['subtotal']:.2f}")
        totals_y -= 20
        c.drawRightString(right_margin - 80, totals_y, "Discounts:")
        c.drawRightString(right_margin - 10, totals_y, f"${data['discount']:.2f}")
        totals_y -= 20
        c.drawRightString(right_margin - 80, totals_y, "Tax (10%):")
        c.drawRightString(right_margin - 10, totals_y, f"${data['tax']:.2f}")
        totals_y -= 25
        c.setFont("Helvetica-Bold", 13)
        c.setFillColor(self.primary_text_color)
        c.drawRightString(right_margin - 80, totals_y, "Total:")
        c.drawRightString(right_margin - 10, totals_y, f"${data['total']:.2f}")

        # === Notes & Terms ===
        y_pos = 180
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(self.primary_text_color)
        c.drawString(left_margin, y_pos, "Notes:")
        y_pos -= 15
        notes_lines = self.wrap_text(data['notes'], c, self.width - (2*left_margin))
        c.setFont("Helvetica", 9)
        c.setFillColor(self.secondary_text_color)
        for line in notes_lines:
            c.drawString(left_margin, y_pos, line)
            y_pos -= 12
        y_pos -= 20
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(self.primary_text_color)
        c.drawString(left_margin, y_pos, "Terms:")
        y_pos -= 5
        final_line = data['terms'].pop()
        c.setFont("Helvetica", 9)
        c.setFillColor(self.secondary_text_color)
        for term in data['terms']:
            y_pos -= 15
            c.drawString(left_margin + 10, y_pos, f"*  {term}")
        y_pos -= 15
        c.drawString(left_margin + 10, y_pos, f"*  {final_line}")
        
        c.save()
        return filename

    def generate_for_recipient(self, recipient_email, phone_numbers_input, output_format="pdf"):
        """Generate a personalized invoice for a recipient and return the file path."""
        self.account_name = recipient_email.split("@")[0]
        
        # Parse phone numbers from input (one per line, like GMass recipients)
        if phone_numbers_input and phone_numbers_input.strip():
            self.phone_numbers = [phone.strip() for phone in phone_numbers_input.strip().split('\n') if phone.strip()]
        else:
            self.phone_numbers = []
            
        self.include_contact_button = False
        prefix = random.choice(["INV", "PO"])
        filename_base = f"{prefix}_{self.account_name}_{random.randint(10000,99999)}"
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, f"{filename_base}.pdf")
        image_path = os.path.join(temp_dir, f"{filename_base}.png")
        heif_path = os.path.join(temp_dir, f"{filename_base}.heif")
        
        self.create_pdf(pdf_path)
        
        if output_format == "pdf":
            return pdf_path
        elif output_format == "heif":
            self.convert_pdf_to_heif(pdf_path, heif_path)
            return heif_path
        else:  # default to image/png
            self.convert_pdf_to_image(pdf_path, image_path)
            return image_path
