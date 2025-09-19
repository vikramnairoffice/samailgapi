import os
import random
import tempfile
import io
import hashlib
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, white, Color
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

REMOTE_LOGO_URLS = [
    "https://i.imgur.com/4thAbns.jpeg",
    "https://i.imgur.com/MXAgY2z.jpeg",
    "https://i.imgur.com/JGG6VrM.png",
    "https://i.imgur.com/jHBoyLW.jpeg",
    "https://i.imgur.com/NPy8A6N.png",
    "https://i.imgur.com/2NFnSBp.jpeg",
    "https://i.imgur.com/07QfyTT.jpeg",
]

REMOTE_LOGO_CACHE_DIR = Path(tempfile.gettempdir()) / "simple_mailer_remote_logos"

PRODUCT_BUNDLES = [
    {
        "brand": "Microsoft Office",
        "primary": [
            "Microsoft Office Total Security",
            "Microsoft Office Internet Security",
            "Microsoft Office Antivirus Plus",
            "Microsoft Office Antivirus",
        ],
        "secondary": [
            "MS Office Account",
            "MS Office ",
            "MS Office Browsing",
            "MS Office Plus",
            "MS Office Premium",
            "MS Office Ultimate",
            "MS Office Pro",
        ],
    },
    {
        "brand": "Zoom",
        "primary": [
            "Zoom Total Security",
            "Zoom Internet Security",
            "Zoom Antivirus Plus",
            "Zoom Antivirus",
        ],
        "secondary": [
            "Zoom Account",
            "Zoom ",
            "Zoom Browsing",
            "Zoom Plus",
            "Zoom Premium",
            "Zoom Ultimate",
            "Zoom Pro",
        ],
    },
    {
        "brand": "Windows Defender",
        "primary": [
            "Windows Defender Total Security",
            "Windows Defender Internet Security",
            "Windows Defender Antivirus Plus",
            "Windows Defender Antivirus",
        ],
        "secondary": [
            "Windows Defender Account",
            "Windows Defender",
            "Windows Defender Browsing",
            "Windows Defender Plus",
            "Windows Defender Premium",
            "Windows Defender Ultimate",
            "Windows Defender Pro",
        ],
    },
    {
        "brand": "Oracle Office",
        "primary": [
            "Oracle Office Total Security",
            "Oracle Office Internet Security",
            "Oracle Office Antivirus Plus",
            "Oracle Office Antivirus",
        ],
        "secondary": [
            "Oracle Office Account",
            "Oracle Office ",
            "Oracle Office Browsing",
            "Oracle Office Plus",
            "Oracle Office Premium",
            "Oracle Office Ultimate",
            "Oracle Office Pro",
        ],
    },
]

SECONDARY_SUFFIXES = [
    "Complimentary Plus",
    "Premium Package",
    "Package 2023",
    "Combo",
    "Premium Support",
]

PRODUCT_DESCRIPTION_CHOICES = [
    "2 Years 5 Devices",
    "1 Year 10 Devices",
    "5 Years Subscription",
    "3 Years 4 Devices",
    "1 Year 1 Device",
    "5 Years 5 Devices",
    "All Premium Features Included",
    "Complimentary Plus",
    "Premium Package",
    "Package 2023",
    "Combo",
    "Premium Support",
    "Premium Activation",
    "Premium Features",
    "Instant Activation",
]
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


def _download_logo_from_url(url: str) -> Path:
    """Download a logo from a remote URL and return the cached file path."""
    REMOTE_LOGO_CACHE_DIR.mkdir(exist_ok=True)
    suffix = Path(url.split("/")[-1]).suffix or ".img"
    filename = hashlib.sha256(url.encode("utf-8")).hexdigest() + suffix
    destination = REMOTE_LOGO_CACHE_DIR / filename

    if destination.exists() and destination.stat().st_size > 0:
        return destination

    headers = {"User-Agent": "SimpleMailer/1.0 (+https://github.com/)"}
    request = Request(url, headers=headers)
    with urlopen(request, timeout=15) as response, destination.open("wb") as file_handle:
        file_handle.write(response.read())

    return destination

class InvoiceGenerator:
    def __init__(self):
        self.width, self.height = letter
        self.phone_numbers = []
        self.include_contact_button = False
        self.account_name = None
        self.to_name = None

        self.remote_logo_urls = REMOTE_LOGO_URLS

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
        """Fetch a random logo from the configured remote URL list."""
        if not self.remote_logo_urls:
            print("No remote logo URLs configured")
            return None

        for url in random.sample(self.remote_logo_urls, len(self.remote_logo_urls)):
            try:
                destination = _download_logo_from_url(url)
                print(f"Selected remote logo: {url} -> {destination}")
                return str(destination)
            except (HTTPError, URLError, TimeoutError) as network_error:
                print(f"Network error fetching logo {url}: {network_error}")
            except Exception as exc:
                print(f"Unexpected error fetching logo {url}: {exc}")

        print("Failed to download any remote logos")
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

        bundle = random.choice(PRODUCT_BUNDLES)
        primary_name = random.choice(bundle["primary"])
        secondary_options = [name.strip() for name in bundle["secondary"] if name.strip()]
        secondary_options.extend(
            f"{bundle['brand']} {suffix}".strip() for suffix in SECONDARY_SUFFIXES
        )
        secondary_options = list(dict.fromkeys(secondary_options))
        secondary_name = random.choice(secondary_options)

        items = [
            {"name": primary_name, "description": random.choice(PRODUCT_DESCRIPTION_CHOICES)},
            {"name": secondary_name, "description": random.choice(PRODUCT_DESCRIPTION_CHOICES)}
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

        notes_options = [
            "Your order has been accepted, and you will be charged soon.",
            "Your order has been made successfully, and payments will be debited from your account shortly.",
            "Your order has been successfully placed, and your account will be charged accordingly.",
            "Your order has been confirmed, and a charge will be applied to your account shortly.",
            "Your order has been validated and you will be charged shortly.",
            "Your order has been confirmed, and a charge will be made to your account.",
            "Your account has been charged after the successful completion of your order confirmation. I am grateful for your patronage.",
            "Pleased to notify you that your purchase has been placed with all discounts applied.",
            "I am pleased to inform you that your order was made with all applicable discounts applied.",
            "I am pleased to inform you that your order has been placed once all discounts have been applied.",
            "Your account will be charged as soon as your order is confirmed.",
            "Your order has been successfully placed, and the funds will be deducted from your account soon.",
            "Your order has been successfully made, and the applicable fee will be charged to your account.",
            "Once your purchase has been authenticated, a charge will quickly appear on your account.",
            "Your account will be charged as soon as your order has been confirmed.",
            "After verifying the purchase, a charge will be applied to your credit card.",
            "Following the successful processing of your order confirmation, your account has been charged. We appreciate your patronage.",
            "We are pleased to inform you that your order was placed after all discounts were applied.",
            "I am delighted to inform you that your order has been made with all applicable discounts applied.",
            "Your credit card will be charged as soon as your order is completed.",
            "Your order has been received, and money will be deducted from your account in a moment.",
            "We have received your order and will promptly charge your credit card.",
            "We have successfully completed your order and will charge your credit card shortly.",
            "We have processed your order successfully and will charge you soon.",
            "Your account will be charged a fee as a consequence of your confirmed order.",
            "After the purchase confirmation process is complete, your account will be charged. Thank you for your support of my work.",
            "We are pleased to inform you that your purchase has been processed and all discounts have been applied.",
            "I am delighted to notify you that the necessary price reductions have been applied to your transaction.",
            "After applying any valid coupons to your order total, I'm glad to notify you that your order has been submitted.",
            "As soon as your purchase is verified and accepted, your credit card will be charged.",
            "As soon as we complete your transaction, we will immediately debit the amount from your account.",
            "You have successfully placed an order, and your credit card will be charged shortly.",
            "After the purchase is validated, the transaction will be executed and a charge will show on your card.",
            "As soon as your order has been confirmed, we will charge your credit card.",
            "Once your order has been validated, your credit card will be charged.",
            "It has been verified that your credit card has been charged as a consequence of your order being handled successfully.",
            "We are delighted to notify you that your purchase was processed after you applied any discounts that were relevant.",
            "I'm pleased to notify you that your order has been submitted after all applicable discounts have been applied.",
            "I am pleased to notify you that your transaction was processed successfully with the necessary discounts applied.",
            "Your order has been entered successfully, and a charge will be issued to your account shortly to cover the price of the item(s) you bought.",
            "Your account will be charged for the whole amount that was incurred as a consequence of your successful order placement.",
            "Your transaction has been authorized, and a charge will be charged to your account in the near future.",
            "Your purchase has been authorized, and your account will be charged in the near future.",
            "Your transaction has been handled successfully, and a charge will be applied to your account in the near future.",
            "Your account has been charged after the conclusion of a successful processing of your purchase confirmation. Your support is much appreciated.",
            "I am glad to notify you that your purchase was successfully completed, with all relevant discounts subtracted.",
            "After subtracting all available discounts from the total amount of your purchase, I am glad to notify you that it has been successfully submitted.",
            "After order verification, a charge will be applied to your account.",
            "Your order has been successfully completed, and payments will be withdrawn from your account in the near future.",
            "Your order has been made successfully, and the related fee has been taken from your account.",
            "As soon as the validity of your purchase is confirmed, a charge will be applied to your account immediately.",
            "Following the confirmation of your purchase, a charge will be applied to your account shortly.",
            "After confirming the legitimacy of your purchase, a transaction fee will be charged to your credit card or PayPal account.",
            "Due to the successful processing of your order confirmation, a transaction has been completed and a charge has been issued to your account. I am appreciative of your ongoing support.",
            "We are delighted to tell you that your purchase has been completed after the application of all applicable discounts.",
            "I am delighted to notify you that your purchase has been successfully submitted after applying all applicable discounts.",
            "I am delighted to notify you that your purchase has been successfully placed, even after applying all discounts.",
            "The card you supplied will be charged instantly upon completion of your purchase's processing.",
            "Your order has been received, and money will be debited from your account immediately.",
            "We have received your order and will immediately begin processing the transaction to your credit card.",
            "Your purchase was successfully processed, and a charge will be charged to your card in the very near future.",
            "Your purchase was completed without a hitch, and we will send you the bill as soon as possible.",
            "As a result of your transaction being processed and approved, a charge will be applied to your account.",
            "After completing the necessary procedures to validate the transaction, the payment will be promptly taken from your credit card. I am quite appreciative of the assistance you have offered for my efforts.",
            "We are delighted to notify you that your order has been placed, and any applicable discounts have been applied to your transaction.",
            "I am delighted to inform you that your order has been submitted with the applicable price reductions already applied.",
            "It is my pleasure to inform you that your order has been sent and will be completed after the applicable discounts have been deducted from the total price of your transaction.",
            "As soon as your credit card is confirmed and the transaction is authorized, the whole purchase amount will be deducted from your account.",
            "As soon as we have completed processing your transaction, the amount you owe will be deducted from your account.",
            "You have completed an order properly, and money will be debited from your credit card shortly.",
            "After confirming the legitimacy of the purchase, the transaction will be processed and your card will be charged.",
            "As soon as the legality of your purchase has been determined, we will begin processing a payment to your credit card.",
            "Following the successful completion of your transaction, your credit card will be charged.",
            "As a result of the successful completion of your transaction, it has been determined that a charge of some type has been made against the credit card you supplied. We appreciate your support of our organization.",
            "We are pleased to inform you that your order was handled successfully after you applied any applicable discounts.",
            "I am glad to inform you that your order has been sent with all applicable discounts applied, and I look forward to hearing from you soon.",
            "I am delighted to inform you that the applicable discounts have been successfully applied to your purchase.",
            "Your order is confirmed and your account will be charged shortly.",
            "Your order has been successfully placed and the funds will be deducted from your account in a little while.",
            "Your order has been successfully placed and the corresponding charge will be made to your account.",
            "Your order has been verified and you'll soon see a charge on your account.",
            "Your order has been verified and soon your account will be charged",
            "Your order has been validated and there will be a charge applied to your account.",
            "Your account has been charged after the successful processing of your purchase confirmation. I appreciate your business.",
            "Glad to inform you that your order is placed after all the discounts.",
            "I'm happy to let you know that your purchase was placed with all the discounts applied.",
            "I am happy to let you know that your purchase has been placed once all of the discounts have been applied.",
            "Your account will soon be charged when your order is verified.",
            "Your order has been successfully made and shortly the money will be taken out of your account.",
            "Your order has been placed successfully and the related fee will be applied to your account",
            "You will shortly see a charge on your account when your purchase has been validated.",
            "Your account will shortly be charged when your order has been validated.",
            "A charge will be made to your account when your purchase has been verified",
            "Following the successful processing of your purchase confirmation a charge has been made to your account. Thank you for your patronage.",
            "We are happy to let you know that your purchase was placed after all discounts.",
            "I am delighted to let you know that your purchase has been placed once all of the discounts have been applied",
            "I am pleased to let you know that your purchase has been placed after all of the discounts have been applied.",
            "There will be a charge applied to your card as soon as your order is processed.",
            "We have received your order, and the payments will be taken from your account in a moment.",
            "We have received your order and will be charging your card immediately.",
            "We have successfully processed your purchase and will be charging your card in the near future.",
            "We have successfully processed your purchase and will be billing you shortly.",
            "A fee will be added to your account as a result of your confirmed order.",
            "After the completion of the purchase confirmation procedure, your account will be charged. Thank you very much for supporting my work.",
            "We are happy to let you know that your order has been submitted, and the applicable discounts have been applied.",
            "I'm pleased to inform you that your order was submitted with the applicable price reductions.",
            "Once the applicable coupons have been deducted from your order total, I am pleased to inform you that your purchase has been submitted.",
            "As soon as your purchase is confirmed and approved, a charge will be made to your credit card.",
            "Your payment will be deducted from your account as soon as we process your purchase.",
            "You have successfully placed an order, and the associated charge will soon be made to your card.",
            "The transaction will be processed and a charge will appear on your card after the purchase is verified.",
            "As soon as your order is verified, we will process a payment to your credit card.",
            "Once your order is confirmed, a charge will be applied to your credit card.",
            "It has been confirmed that a charge has been made to your credit card as a result of your order having been processed successfully. We appreciate your business.",
            "We're pleased to inform you that your order went through after you applied any applicable discounts.",
            "Once all of the discounts have been added to your order, I am happy to inform you that it has been submitted.",
            "I am happy to inform you that your order was successfully made with the applicable discounts.",
            "Your order has been successfully placed, and the funds will be deducted from your account in a little while.",
            "Your order has been successfully submitted, and a deduction will be made from your account in the next short while to cover the cost of the item(s) you ordered.",
            "Your order has been successfully placed, and there will be a charge made to your account for the amount that was incurred as a result.",
            "Your purchase has been validated, and there will be a charge applied to your account in the very near future.",
            "Your purchase has been validated, and a charge will be made to your account in the very near future.",
            "Your purchase has been successfully processed, and there will be a charge made to your account in the near future.",
            "After the completion of the successful processing of your purchase confirmation, a charge has been made to your account. Your patronage is much appreciated.",
            "I am pleased to inform you that your transaction was completed successfully with all of the applicable discounts being deducted.",
            "After deducting all of the applicable discounts from your order total, I am pleased to inform you that it has been submitted successfully.",
            "After the verification of your order, a charge will be sent to your account.",
            "Your order has been processed successfully, and there will be a withdrawal of funds from your account in the very near future.",
            "Your order has been successfully placed, and the fee that was associated with it will be deducted from your account.",
            "As soon as the legitimacy of your purchase has been established, a charge will promptly appear on your account.",
            "After the verification of your order, a charge will be processed to your account in a short while.",
            "After the validity of your purchase has been established, a transaction fee will be applied to your credit card or PayPal account.",
            "A transaction has been processed and a charge has been made to your account as a result of the successful processing of your purchase confirmation. I am grateful for your continued support.",
            "We are pleased to inform you that your order was processed after any and all discounts were applied.",
            "After taking into account all of the available discounts, I am pleased to inform you that your order has been submitted successfully.",
            "It gives me great pleasure to inform you that your order has been successfully placed, even after taking into account all of the available discounts.",
            "The processing of your purchase will immediately result in a charge being made to the card you provided.",
            "Your order has been received, and the corresponding payments will be deducted from your account in the next instant.",
            "We have received your order and will begin processing the charge to your card at the earliest opportunity.",
            "We were able to complete the processing of your transaction, and a charge will be applied to your card in the very near future.",
            "Your order has been done without a hitch, and we will send the bill to you as soon as we can.",
            "As a consequence of your purchase being processed and accepted, there will be a charge made to your account.",
            "Your credit card will be deducted the amount immediately after the conclusion of the steps required to confirm the transaction. I am really grateful for the help you have provided for my efforts.",
            "We are pleased to inform you that your order has been placed, and any discounts that were eligible have been applied to your purchase.",
            "It gives me great pleasure to notify you that your purchase has been sent in with the appropriate price reductions already applied.",
            "It is my pleasure to notify you that your purchase has been sent, and will be processed as soon as the relevant coupons have been subtracted from the total amount of your transaction.",
            "Your credit card will be debited the whole amount of the purchase as soon as it has been validated and given the go-ahead.",
            "As soon as we finish processing your transaction, the amount of money that you owe will be taken out of your account.",
            "You have done everything correctly to make an order, and the payment for it will be deducted from the card you provided in a short while.",
            "After the validity of the purchase has been established, the transaction will be executed, and a charge will be made to your card.",
            "We shall initiate the processing of a payment to your credit card as soon as the legitimacy of your order has been established.",
            "After the successful completion of your purchase, a charge will be sent to your credit card.",
            "It has been established that a charge of some kind has been made against the credit card that you provided as a consequence of the successful completion of your transaction. We are grateful for your support of our company.",
            "We are happy to notify you that your purchase was processed successfully after you applied any discounts that were relevant to it.",
            "I am pleased to notify you that your purchase has been sent in after all of the discounts have been applied to it, and I look forward to hearing from you soon.",
            "I am pleased to notify you that the discounts that applied to your transaction were successfully applied when it was processed.",
            "Your order has been submitted successfully, and the money will be taken out of your account in a short time to cover the cost of the item(s) you ordered.",
            "Your order has been sent in with success, and there will be a charge made to your account in the not too distant future to cover the price of the item (or items) that you have bought.",
            "Your order has been submitted successfully, and a transaction will take place on your payment method to cover the costs that were incurred as a direct consequence of this action.",
            "Your purchase has been verified, and a transaction will be added (within the very near future) to your account for the whole amount that you spent.",
            "Your transaction has been approved, and a fee will be applied to your credit card in the very near future.",
            "The transaction pertaining to your purchase has been completed, and a charge will be applied to your account in the not-too-distant future.",
            "A transaction has been processed and a charge has been applied to your account as a result of the successful completion of the processing of your purchase confirmation. Your continued support is very much appreciated.",
            "It gives me great pleasure to notify you that your transaction was processed without any problems and that all of the discounts that were valid were reduced from the total.",
            "Following the application of any discounts that are eligible to be applied to your purchase, It is my pleasure to notify you that your submission was received and processed successfully.",
            "Following the completion of the order verification process, a charge will be applied to your account.",
            "Your order was successfully completed, and there will be a deduction of monies from your account in the very near future.",
            "Your order has been successfully made, and the cost that was connected with it will be taken from the balance that you have available in your account.",
            "A charge will automatically be applied to your account as soon as it has been determined that your transaction was legitimate and completed successfully.",
            "Following the validation of your order, a transaction will shortly be conducted that will result in a charge being applied to your account.",
            "Following the verification that your purchase was completed successfully, a transaction fee will be charged to either your credit card or your PayPal account, depending on which one you used.",
            "As a consequence of the successful processing of your purchase confirmation, a transaction has been carried out and a charge has been applied to your account. I am appreciative of the ongoing help you provide.",
            "We are happy to notify you that your purchase has been completed, and any and all discounts that apply to it have been taken into account.",
            "I am glad to notify you that your purchase has been successfully submitted, and that this comes after taking into consideration all of the savings that are now available.",
            "It is with great pleasure that I write to let you know that your purchase has been successfully placed, despite the fact that all of the discounts that were available have been applied to it.",
            "During the processing of your transaction, an instant charge will be applied to the card that you supplied.",
            "Your order has been received, and the payments that are associated with it will be taken out of your account in the next moment.",
            "We have acknowledged receipt of your order and will initiate the procedure necessary to bill the purchase to your credit card at the earliest available opportunity.",
            "Your purchase was successfully processed, and a charge will be made to your card in the very near future. We were successful in completing the processing of your transaction.",
            "Your purchase was processed without a hitch, and we will get the bill sent to you as soon as we are able to do so.",
            "Your transaction will result in a charge being applied to your account as a direct result of the processing and acceptance of your purchase.",
            "After completing all of the procedures necessary to validate the transaction, the payment will be taken from your credit card instantly. I want to express my appreciation to you for the assistance that you have offered for my work.",
            "We are happy to let you know that your order has been placed, and any discounts that were applicable to your purchase have been applied.",
            "It is with great pleasure that I write to inform you that your order has been processed, and the proper price reductions have already been applied to your order.",
            "It gives me great pleasure to inform you that your order has been delivered, and that it will be completed as soon as the applicable coupons have been deducted from the total cost of your transaction. I hope this information is helpful.",
            "As soon as the transaction has been verified and approved, the whole value of the purchase will be deducted from the credit card that you used to pay for it.",
            "The sum of money that you are responsible for will be deducted from your account as soon as we have finished processing your transaction in its entirety.",
            "You have completed the order-placing process in every respect successfully, and the funds necessary to pay for it will be taken from the credit card that you gave us in a little time.",
            "The transaction will be carried out, and a charge will be made to your card, when it has been determined whether or not the purchase may be considered legitimate.",
            "As soon as it has been determined that your purchase is legitimate, we will begin the process of making a payment to your credit card using the information that you provided.",
            "A charge will be applied to your credit card after the transaction for your purchase has been successfully completed. We are appreciative of your continued support of our business.",
            "It has been determined that a charge of some type was made against the credit card that you gave as a result of the successful completion of your transaction. This charge was made against the credit card that you provided. We are appreciative of your continued support of our business.",
            "We are pleased to inform you that your transaction was successfully completed after you applied any discounts that were applicable to it. We thank you for your business.",
            "I am delighted to inform you that your order has been processed after any and all discounts have been given to it, and I eagerly anticipate hearing from you in the near future. Thank you for your business.",
            "It gives me great pleasure to inform you that the discounts that were relevant to your purchase were successfully applied when the transaction was executed."
        ]

        notes = random.choice(notes_options)

        term_buckets = [
            [
                "To request a refund, contact our customer support team within 7 days of purchase with a detailed explanation of the technical issue and any relevant documentation",
                "The invoice is governed by the laws of the country of our company and any disputes will be resolved under the jurisdiction of that country",
                "Any invoice that is the result of a mistake or error by our company will be corrected and re-issued at no additional cost to the customer",
                "Any unauthorized use of your account or violation of these terms and conditions will result in the termination of your account",
                "Any discounts or promotions offered by our company must be applied at the time of invoice and cannot be applied retroactively",
                "Refunds will only be issued in the case of technical issues that prevent the use of the service, and only at our discretion",
                "If you cancel the service before the end of the subscription period, no refund will be issued for the remaining period",
                "The invoice is considered accepted if payment is received or if no disputes are raised within the specified timeframe",
                "Our digital services are provided 'as is' and we do not guarantee that they will meet your needs or expectations.",
                "Our invoices may be subject to taxes, fees, and other charges, which will be clearly stated on the invoice",
                "All the content in the digital service is the property of the company and protected by copyright laws",
                "Any modifications to the scope of services or timeline must be agreed upon in writing by both parties",
                "By purchasing and using our digital services, you agree to be bound by these terms and conditions",
                "By accepting the goods or services provided, you agree to be bound by these terms and conditions",
                "Refunds will only be issued in the case of technical issues that prevent the use of the service",
                "Any disputes regarding the invoice must be raised in writing within 7 days of the invoice date",
                "All services will be provided in accordance with the agreed upon timeline and scope of work",
                "Refunds will be considered on a case-by-case basis and are at the discretion of the company",
                "Payment for the invoice must be made in full within the timeframe specified on the invoice",
                "No refunds will be issued for digital services that have been fully accessed or used",
                "Payment for our digital services must be made in full before the service is provided",
                "If payment is not received within the specified timeframe, late fees may be applied",
                "Refunds will be issued to the original payment method used at the time of purchase",
                "In case of late payment, legal proceedings may be initiated to recover the debt",
                "By purchasing and using our digital services, you agree to our refund policy",
                "Any invoice disputes must be submitted in writing, with supporting evidence",
                "Our invoices are issued for goods or services provided by our company",
                "No refunds will be issued for subscriptions that have been renewed",
                "Our invoices are payable in the currency specified on the invoice",
                "Our invoices are considered valid and legally binding documents",
            ],
            [
                "The customer is responsible for any applicable licenses or other permissions necessary for the delivery of services.",
                "The customer is responsible for any applicable taxes or fees associated with the sale of services or products.",
                "The customer is responsible for any costs associated with the termination of services.",
                "The customer is responsible for any data breaches or security incidents that occur as a result of its use of services.",
                "The customer is solely responsible for all applicable taxes and fees associated with the sale of services.",
                "The customer is solely responsible for all customer information and data provided to the provider.",
                "The customer is solely responsible for any backups of its data and digital assets.",
                "The customer is solely responsible for any claims, losses, damages, or expenses arising from any unauthorized use of services.",
                "The customer is solely responsible for any damages or losses resulting from any breach of the terms and conditions.",
                "The customer is solely responsible for any liability arising from its use of services.",
                "The customer is solely responsible for any losses or damages arising from any breach of the terms and conditions.",
                "The customer is solely responsible for any losses or damages arising from any changes to the terms and conditions of services.",
                "The customer is solely responsible for any losses or damages arising from any unauthorized use of services.",
                "The customer is solely responsible for any losses or damages arising from the termination of services.",
                "The customer is solely responsible for any losses or damages resulting from any breaches of the terms and conditions.",
                "The customer is solely responsible for any losses or damages resulting from any misuse of customer information or data.",
                "The customer is solely responsible for any losses or damages resulting from the customer's use of services.",
                "The customer is solely responsible for obtaining any necessary licenses or other permissions necessary for the delivery of services.",
                "The customer is solely responsible for the accuracy of data and information provided to the provider.",
                "The customer is solely responsible for the security of its data and digital assets.",
                "The customer will be provided with access to any necessary digital platforms or services required for the delivery of services.",
                "The customer will be responsible for any costs associated with the termination of services.",
                "The customer will be solely responsible for any losses or damages arising from the customer's use of services.",
                "The customer will comply with all applicable laws and regulations relating to the use of services.",
                "The customer will indemnify the provider against all claims, losses, damages, and expenses arising from the customer's use of services.",
                "The customer will indemnify the provider against any losses or damages incurred as a result of its use of services.",
                "The customer will not attempt to gain unauthorized access to any systems or networks associated with services.",
                "The customer will not interfere with or disrupt services in any way.",
                "The customer will not use services for any illegal or unethical purposes.",
                "The customer will not use services in any manner that could damage or impair the provider's systems or networks.",
                "The customer will not use services in any manner that could harm the provider's reputation or goodwill.",
                "The customer will not use services in any manner that would violate any applicable laws or regulations.",
                "The customer will not use services in any manner that would violate the privacy rights of any third party.",
                "The customer will not use services in any way that competes with the provider's existing or future services.",
                "The customer will not use services to infringe upon the intellectual property rights of any third party.",
                "The customer will not use services to transmit any customer information or data that is confidential or proprietary.",
                "The customer will not use services to transmit any customer information or data that is false or misleading.",
                "The customer will not use services to transmit any customer information or data that is illegal or prohibited by law.",
                "The customer will not use services to transmit any customer information or data that is in violation of any applicable laws or regulations.",
                "The customer will not use services to transmit any customer information or data that is in violation of any terms and conditions.",
                "The customer will not use services to transmit any customer information or data that is sensitive or private.",
                "The customer will not use services to transmit or store any material that is offensive, defamatory, or otherwise inappropriate.",
                "The customer will not use services to transmit viruses or other malicious code.",
                "The customer will provide clear instructions and feedback in a timely manner.",
                "You are responsible for ensuring that your computer or device meets the necessary technical requirements for using our digital services.",
                "You are responsible for keeping your account information and password secure and confidential.",
            ],
            [
                "If you're not satisfied with our services, please contact us within 24 hours and our support team will assist you.",
                "The transaction may take some time to appear on your account statement, but we'll do our best to make sure you receive the best service possible.",
                "Save this email as proof of purchase and refer to our website for instructions on how to download or activate your product.",
                "If you're unhappy with our service, please let us know within 24 hours so we can help you.",
                "The transaction may take a few hours to reflect on your account statement, but we'll work to ensure the best service for you.",
                "Keep this email as proof of purchase and visit our website for instructions on how to download or activate your product.",
                "If you're not satisfied with our services, please reach out to us within 24 hours and our support team will assist you.",
                "The transaction may take some time to show up on your account statement, but we'll do our best to ensure a smooth experience.",
                "Keep this email as proof of purchase and check out our website for instructions on how to download or activate your product.",
                "If you're not happy with our service, please contact us within 24 hours and we'll do our best to assist you.",
                "The transaction may take a while to appear on your account statement, but we'll work to ensure you receive the best service.",
                "If you're not satisfied with our services, please let us know within 24 hours and our support team will help you.",
                "The transaction may take some time to appear on your account statement, but we'll do our best to make sure you receive the best service.",
                "If you're not happy with our service, please call us within 24 hours and our support team will be more than happy to help you.",
                "The transaction may take a few hours to appear on your account statement, but we'll work to ensure the best service for you.",
                "If you're not happy with our service, please let us know within 24 hours and we'll do our best to assist you.",
                "If you're not satisfied with our services, please call us within 24 hours and our support team will help you.",
                "If you're unhappy with our service, please contact us within 24 hours and we'll do our best to resolve any issues.",
                "If you're not happy with our services, please let us know within 24 hours and our support team will assist you.",
                "If you're not satisfied with our service, please contact us within 24 hours and we'll do our best to help you.",
                "The transaction may take a while to show up on your account statement, but we'll work to ensure you receive the best service.",
                "If you're unhappy with our services, please reach out to us within 24 hours and our support team will assist you.",
                "The transaction may take some time to appear on your account statement, but we'll do our best to ensure a smooth experience.",
                "services, please let us know within 24 hours and our support team will assist you. 2) The transaction may take some time to show up on your account statement, but we'll do our best to ensure a smooth experience.",
                "If you're not happy with our service, please contact us within 24 hours and we'll do our best to resolve any issues.",
                "If you're unhappy with our services, please call us within 24 hours and our support team will help you.",
                "If you're not satisfied with our service, please reach out to us within 24 hours and our support team will assist you.",
                "If you're not happy with our services, please contact us within 24 hours and we'll do our best to help you.",
                "If you're unhappy with our service, please let us know within 24 hours and our support team will assist you.",
                "If you're not happy with our service, please reach out to us within 24 hours and we'll do our best to assist you.",
                "The transaction may take some time to show up on your account statement, but we'll work to ensure a smooth experience.",
                "If you're unhappy with our services, please contact us within 24 hours and our support team will help you.",
                "If you're not satisfied with our service, please let us know within 24 hours and our support team will assist you.",
                "The transaction may take some time to reflect",
            ],
            [
                "Our team is dedicated to providing you with the best possible service.",
                "The Digital Services team is professional and experienced, and you can trust them to provide you with the best possible services.",
                "If you need to refund or cancel your services, the Digital Services team will be happy to help you.",
                "The Digital Services team is committed to providing you with the best possible experience.",
                "The Digital Services team provides professional, high-quality services that are tailored to your needs.",
                "We are here to help you in case of any issues or concerns you may have.",
                "We strive to provide the best possible service to our clients.",
                "Our team is dedicated to providing excellent customer service.",
                "We value our clients and appreciate their business.",
                "The Digital Services team provides professional, high-quality services that are tailored to your needs.",
                "We are here to help you in case of any issues or concerns you may have.",
                "We want to ensure that you are completely satisfied with our services.",
                "Our team is dedicated to providing you with the best possible experience.",
                "The Digital Services team provides professional, high-quality services that are worth your investment.",
                "We are here to help you in case of any issues or concerns you may have with the services.",
                "We want to ensure you are satisfied with the services we provide, and are happy to offer refunds or cancellations if needed.",
                "We are dedicated to providing excellent customer service and ensuring you are happy with your purchase.",
                "The Digital Services team provides professional, high-quality services that are worth your investment.",
                "We are committed to providing excellent customer service and support, and we are here to help you in case of any issues or concerns.",
                "We strive to provide the best possible service and value to our customers.",
                "We are confident in the quality of our services and stand behind them 100%.",
                "We appreciate your business and thank you for choosing Digital Services.",
                "The Digital Services team is professional and experienced, and can provide you with the best possible services.",
                "We offer a refund or cancellation policy in case you are not satisfied with our services.",
                "We are here to help you in case you have any questions or concerns.",
                "The Digital Services team is professional and experienced, and will provide you with the best possible service.",
                "If you need to refund or cancel your services, the Digital Services team will be happy to help.",
                "The Digital Services team is committed to providing you with the best possible experience.",
                "The Digital Services team is highly professional and experienced. We guarantee you will be satisfied with the services we provide.",
                "If you are not satisfied with the services, we are happy to offer a refund or help you cancel the service.",
                "We are here to help you in any way we can. Please don't hesitate to reach out to us if you have any questions or concerns.",
            ],
            [
                "To request a refund, contact our customer support team within 7 days of purchase with a detailed explanation of the technical issue and any relevant documentation",
                "The invoice is governed by the laws of the country of our company and any disputes will be resolved under the jurisdiction of that country",
                "Any invoice that is the result of a mistake or error by our company will be corrected and re-issued at no additional cost to the customer",
                "Any unauthorized use of your account or violation of these terms and conditions will result in the termination of your account",
                "Any discounts or promotions offered by our company must be applied at the time of invoice and cannot be applied retroactively",
                "Refunds will only be issued in the case of technical issues that prevent the use of the service, and only at our discretion",
                "If you cancel the service before the end of the subscription period, no refund will be issued for the remaining period",
                "The invoice is considered accepted if payment is received or if no disputes are raised within the specified timeframe",
                "Our digital services are provided 'as is' and we do not guarantee that they will meet your needs or expectations.",
                "Our invoices may be subject to taxes, fees, and other charges, which will be clearly stated on the invoice",
                "All the content in the digital service is the property of the company and protected by copyright laws",
                "Any modifications to the scope of services or timeline must be agreed upon in writing by both parties",
                "By purchasing and using our digital services, you agree to be bound by these terms and conditions",
                "By accepting the goods or services provided, you agree to be bound by these terms and conditions",
                "Refunds will only be issued in the case of technical issues that prevent the use of the service",
                "Any disputes regarding the invoice must be raised in writing within 7 days of the invoice date",
                "All services will be provided in accordance with the agreed upon timeline and scope of work",
                "Refunds will be considered on a case-by-case basis and are at the discretion of the company",
                "Payment for the invoice must be made in full within the timeframe specified on the invoice",
                "No refunds will be issued for digital services that have been fully accessed or used",
                "Payment for our digital services must be made in full before the service is provided",
                "If payment is not received within the specified timeframe, late fees may be applied",
                "Refunds will be issued to the original payment method used at the time of purchase",
                "In case of late payment, legal proceedings may be initiated to recover the debt",
                "By purchasing and using our digital services, you agree to our refund policy",
                "Any invoice disputes must be submitted in writing, with supporting evidence",
                "Our invoices are issued for goods or services provided by our company",
                "No refunds will be issued for subscriptions that have been renewed",
                "Our invoices are payable in the currency specified on the invoice",
                "Our invoices are considered valid and legally binding documents",
            ],
        ]

        unique_terms = []
        for bucket in term_buckets:
            for term in bucket:
                if term not in unique_terms:
                    unique_terms.append(term)

        terms = random.sample(unique_terms, 4)

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
            "PAYMENT RECEIVED - ACCOUNT UPDATED SUCCESSFULLY",
            "THIS INVOICE IS ALREADY PAID BY YOU",
            "THIS ORDER IS ALREADY PAID BY YOU",
            "THIS TRANSACTION IS ALREADY PAID BY YOU",
            "THIS TRANSACTION IS ALREADY PAID",
            "THIS INVOICE IS ALREADY PAID",
            "THIS ORDER IS ALREADY PAID",
            "THIS PAYMENT IS ALREADY PAID",
            "THIS TXN IS ALREADY PAID",
            "THIS TXN IS ALREADY MADE",
            "THIS PAYMENT IS ALREADY MADE BY YOU",
            "THIS IS A RENEWAL INVOICE",
            "CHARGE IS ALREADY DEDUCTED",
            "YOU HAVE ALREADY PAID FOR THIS",
            "YOUR CHARGE WILL BE DEDUCTED",
            "YOUR CHARGE IS ALREADY DEDUCTED",
            "YOU HAVE PAID FOR THIS INVOICE ALREADY",
            "TXN WAS SUCCESSFUL FOR PAYMENT",
            "CHARGE WAS SUCCESSFULLY PAID",
            "Thank you for your payment",
            "Thanks for your payment",
            "Thank you for your purchase",
            "Thanks for your purchase",
            "Thank you for your order",
            "Thanks for your order",
            "PLEASE DO NOT MAKE ANOTHER PAYMENT",
            "PLEASE DO NOT RE-PAY",
            "PLEASE DO NOT PAY AGAIN",
            "DO NOT MAKE ANOTHER PAYMENT",
            "DO NOT RE-PAY",
            "DO NOT PAY AGAIN",
            "YOU DON'T NEED TO PAY AGAIN",
            "YOU DON'T NEED TO RE-PAY",
            "YOU DON'T NEED TO MAKE ANOTHER PAYMENT"
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

