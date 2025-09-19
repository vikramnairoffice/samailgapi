import random
import string
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Mapping, Optional

from faker import Faker


fake = Faker()

DEFAULT_SUBJECTS = [
    "Notice", "Confirmation", "Alert Release", "New Update Purchase", "New Update Confirmation", "Thank you for contribution", "Thanks for your interest", "Maintenance Invoice", "Purchase Notification", "Maintenance Confirmation", "Purchase Confirmation", "Purchase Invoice", "Immediately notify", "Alert", "Update", "Hello", "Thank You", "Thanks", "Thanks Again", "Notify", "Notification", "Alert Update", "Renewal", "Subscription", "Activation", "Purchase Report", "Purchase Receipt", "New Receipt", "Modification in Receipt", "Modification in Invoice", "Thanks for your order", "Thanks for your Purchase", "Thanks for your confirmation of renewal", "Thanks for transaction", "New transaction found", "Renewal Transaction Update", "Transaction Notification", "Transaction success Alert", "Transaction Activation Update", "Transaction Subscription Notify", "Purchase Confirmation", "Invoice Update", "Document Ready", "Order Status"
]

DEFAULT_BODIES = [
    "Hello, Please find the attached documents for your review. We appreciate your prompt attention to this matter. Thank you.",
    "Greetings, The files you requested are attached. Please let us know if you have any questions. Best regards.",
    "Dear User, Attached is the information pertaining to your account. Please review it at your earliest convenience. Sincerely.",
]

DEFAULT_GMASS_RECIPIENTS = [
    "ajaygoel999@gmail.com",
    "test@chromecompete.com", 
    "test@ajaygoel.org",
    "me@dropboxslideshow.com",
    "test@wordzen.com",
    "rajgoel8477@gmail.com",
    "rajanderson8477@gmail.com",
    "rajwilson8477@gmail.com",
    "briansmith8477@gmail.com",
    "oliviasmith8477@gmail.com",
    "ashsmith8477@gmail.com",
    "shellysmith8477@gmail.com",
    "ajay@madsciencekidz.com",
    "ajay2@ctopowered.com",
    "ajay@arena.tec.br",
    "ajay@daustin.co"
]

PDF_ATTACHMENT_DIR = "./pdfs"
IMAGE_ATTACHMENT_DIR = "./images"
SEND_DELAY_SECONDS = 4.5

SENDER_NAME_TYPES = ["business", "personal"]
DEFAULT_SENDER_NAME_TYPE = "business"

BUSINESS_SUFFIXES = [
    "Foundation", "Fdn", "Consulting", "Co", "Services", "Ltd", "Instituto", "Institute", "Corp.",
    "Trustees", "Incorporated", "Technologies", "Assoc.", "Trustee", "Company", "Industries", "LLP",
    "Corp", "Assoc", "Associazione", "Trust", "Solutions", "Group", "Associa", "Corporation",
    "Trusts", "Corpo", "Inc", "PC", "LLC", "Institutes", "Associates"
]

R1_DELIMITER = " | "
R1_ALPHA_POOL = string.ascii_uppercase + string.digits


TagContext = Optional[Mapping[str, str]]
TagGenerator = Callable[[TagContext], str]


@dataclass(frozen=True)
class TagDefinition:
    name: str
    description: str
    example: str
    generator: TagGenerator


def _context_lookup(context: TagContext, key: str) -> Optional[str]:
    if context:
        value = context.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def _random_numeric_string(min_digits: int, max_digits: int) -> str:
    length = random.randint(min_digits, max_digits)
    return ''.join(random.choices(string.digits, k=length))


def _random_letter_string(min_length: int, max_length: int, alphabet: str) -> str:
    length = random.randint(min_length, max_length)
    return ''.join(random.choices(alphabet, k=length))


def _random_upper_alphanumeric(min_length: int, max_length: int) -> str:
    length = random.randint(min_length, max_length)
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(random.choices(alphabet, k=length))


def _tag_date_multi(_: TagContext = None) -> str:
    today = datetime.now()
    formats = ["%d %B, %Y", "%B %d, %Y", "%d %b %Y"]
    return today.strftime(random.choice(formats))


def _tag_date_numeric(_: TagContext = None) -> str:
    today = datetime.now()
    formats = ["%m/%d/%Y", "%d/%m/%Y"]
    return today.strftime(random.choice(formats))


def _tag_datetime(_: TagContext = None) -> str:
    today = datetime.now()
    formats = ["%d %B, %Y %H:%M:%S", "%d %b %Y %H:%M:%S", "%m/%d/%Y %H:%M:%S"]
    return today.strftime(random.choice(formats))


def _tag_single_name(_: TagContext = None) -> str:
    return fake.first_name()


def _tag_full_name(_: TagContext = None) -> str:
    return f"{fake.first_name()} {fake.last_name()}"


def _tag_unique_name(_: TagContext = None) -> str:
    initial = fake.first_name()[0]
    primary = fake.first_name()
    last = fake.last_name()
    return f"{initial}. {primary} {last}"


def _tag_email(_: TagContext = None) -> str:
    return fake.email()


def _tag_content(context: TagContext = None) -> str:
    value = _context_lookup(context, 'content')
    if value:
        return value
    return "Content"


def _tag_invoice(_: TagContext = None) -> str:
    prefix = ''.join(random.choices(string.ascii_uppercase, k=10))
    mid = _random_numeric_string(7, 8)
    suffix = ''.join(random.choices(string.ascii_uppercase, k=5))
    return f"INV-{prefix}-{mid}-{suffix}"


def _tag_short_numeric(_: TagContext = None) -> str:
    return _random_numeric_string(5, 10)


def _tag_long_numeric(_: TagContext = None) -> str:
    return _random_numeric_string(10, 15)


def _tag_short_mixed_letters(_: TagContext = None) -> str:
    return _random_letter_string(10, 15, string.ascii_letters)


def _tag_long_mixed_letters(_: TagContext = None) -> str:
    return _random_letter_string(20, 30, string.ascii_letters)


def _tag_short_upper_letters(_: TagContext = None) -> str:
    return _random_letter_string(10, 15, string.ascii_uppercase)


def _tag_long_upper_letters(_: TagContext = None) -> str:
    return _random_letter_string(20, 30, string.ascii_uppercase)


def _tag_short_lower_letters(_: TagContext = None) -> str:
    return _random_letter_string(10, 15, string.ascii_lowercase)


def _tag_long_lower_letters(_: TagContext = None) -> str:
    return _random_letter_string(20, 30, string.ascii_lowercase)


def _tag_uuid(_: TagContext = None) -> str:
    return str(uuid.uuid4())


def _tag_trx(_: TagContext = None) -> str:
    return _random_upper_alphanumeric(35, 40)


def _tag_address(_: TagContext = None) -> str:
    return fake.street_address()


def _tag_full_address(_: TagContext = None) -> str:
    raw = fake.address()
    clean = raw.replace('\r\n', '\n').replace('\n', ', ')
    return clean.strip()


def _tag_tfn(context: TagContext = None) -> str:
    value = _context_lookup(context, 'tfn')
    if value:
        return value
    return fake.phone_number()


TAG_DEFINITIONS: Dict[str, TagDefinition] = {
    "#DATE#": TagDefinition(
        name="#DATE#",
        description="Generates the current date in multiple formats.",
        example="18 June, 2024",
        generator=_tag_date_multi,
    ),
    "#DATE1#": TagDefinition(
        name="#DATE1#",
        description="Generates the current date in various numeric formats.",
        example="07/05/2025",
        generator=_tag_date_numeric,
    ),
    "#DATETIME#": TagDefinition(
        name="#DATETIME#",
        description="Generates the current date and time in different formats.",
        example="20 May, 2025 00:00:00",
        generator=_tag_datetime,
    ),
    "#NAME#": TagDefinition(
        name="#NAME#",
        description="Generates a random single name.",
        example="Crystle",
        generator=_tag_single_name,
    ),
    "#FNAME#": TagDefinition(
        name="#FNAME#",
        description="Generates a random full name.",
        example="Robert Schmidt",
        generator=_tag_full_name,
    ),
    "#UNAME#": TagDefinition(
        name="#UNAME#",
        description="Generates a random unique name.",
        example="R. Nathan Hahn",
        generator=_tag_unique_name,
    ),
    "#EMAIL#": TagDefinition(
        name="#EMAIL#",
        description="Retrieves the client's email address.",
        example="alex2024@gmail.com",
        generator=_tag_email,
    ),
    "#CONTENT#": TagDefinition(
        name="#CONTENT#",
        description="Gets the main body content entered in the body box using this tag.",
        example="Content",
        generator=_tag_content,
    ),
    "#INV#": TagDefinition(
        name="#INV#",
        description="Generates a unique sequence number.",
        example="INV-FIGGRWNNFIT-04446407-SJXNE",
        generator=_tag_invoice,
    ),
    "#INUM#": TagDefinition(
        name="#INUM#",
        description="Generates a short numeric value (5 to 10 digits).",
        example="494500",
        generator=_tag_short_numeric,
    ),
    "#LNUM#": TagDefinition(
        name="#LNUM#",
        description="Generates a long numeric value (10 to 15 digits).",
        example="0770431750123",
        generator=_tag_long_numeric,
    ),
    "#SMLETT#": TagDefinition(
        name="#SMLETT#",
        description="Generates a short mixed-case letter string (10 to 15 characters).",
        example="FzsAcgjWqN",
        generator=_tag_short_mixed_letters,
    ),
    "#LMLETT#": TagDefinition(
        name="#LMLETT#",
        description="Generates a long mixed-case letter string (20 to 30 characters).",
        example="JVyDJmYahbZGHJQUtdBF",
        generator=_tag_long_mixed_letters,
    ),
    "#SCLETT#": TagDefinition(
        name="#SCLETT#",
        description="Generates a short uppercase letter string (10 to 15 characters).",
        example="EVOUAHLEM",
        generator=_tag_short_upper_letters,
    ),
    "#LCLETT#": TagDefinition(
        name="#LCLETT#",
        description="Generates a long uppercase letter string (20 to 30 characters).",
        example="PEQLXACTDWRDPHZTT",
        generator=_tag_long_upper_letters,
    ),
    "#SLLETT#": TagDefinition(
        name="#SLLETT#",
        description="Generates a short lowercase letter string (10 to 15 characters).",
        example="mxsebrvl",
        generator=_tag_short_lower_letters,
    ),
    "#LLLETT#": TagDefinition(
        name="#LLLETT#",
        description="Generates a long lowercase letter string (20 to 30 characters).",
        example="igxnibvmtqksywep",
        generator=_tag_long_lower_letters,
    ),
    "#UKEY#": TagDefinition(
        name="#UKEY#",
        description="Generates a unique UUID key.",
        example="1038df95-d2db-4fff-a668-c4cde9f7ec30",
        generator=_tag_uuid,
    ),
    "#TRX#": TagDefinition(
        name="#TRX#",
        description="Generates a random alphanumeric string (35 to 40 characters).",
        example="2CHCICPY1U0EVU6SMZZ1A3M0GGG05JPNETYYSI",
        generator=_tag_trx,
    ),
    "#ADDRESS#": TagDefinition(
        name="#ADDRESS#",
        description="Generates a random postal address.",
        example="108 Hemway Center",
        generator=_tag_address,
    ),
    "#ADDRESS1#": TagDefinition(
        name="#ADDRESS1#",
        description="Generates a random full address.",
        example="3356 Leon Keys Suite 431 Shawton, VY 88912",
        generator=_tag_full_address,
    ),
    "#TFN#": TagDefinition(
        name="#TFN#",
        description="Retrieves the number entered in the TFN input box.",
        example="+1 (856) 347-2649",
        generator=_tag_tfn,
    ),
}


def get_tag_definitions() -> List[TagDefinition]:
    """Return tag definitions preserving declaration order."""
    return list(TAG_DEFINITIONS.values())


def generate_tag_value(tag_name: str, context: TagContext = None) -> str:
    """Return a realized tag value for the provided tag name."""
    definition = TAG_DEFINITIONS.get(tag_name)
    if definition is None:
        raise KeyError(f"Unknown tag: {tag_name}")
    return definition.generator(context)


R1_PREFIX_CHOICES = ["Automatic", "Automated", "FWD", "FWD.", "FWD:"]
R1_KEYWORD_CHOICES = [
    "Auotmaitc",
    "Debit",
    "Delivery",
    "Deposit",
    "Details",
    "Project",
    "Proposal",
    "Ticket",
    "Recipet",
    "Refund",
    "Registered",
    "Re-Rrint",
    "Receipt",
    "Registrations",
    "Reimbursement",
    "Reminder",
    "Renewal",
    "Reply",
    "Report",
    "Rerserach",
    "Reservation",
    "Snapshot",
    "Subscription",
    "Updated",
    "Paid",
]
R1_NAME_TAGS = ["#NAME#", "#FNAME#", "#UNAME#"]
R1_DATE_TAGS = ["#DATE#", "#DATE1#", "#DATETIME#"]
R1_STRING_TAGS = [
    "#INV#",
    "#UKEY#",
    "#TRX#",
    "#SMLETT#",
    "#LMLETT#",
    "#SCLETT#",
    "#LCLETT#",
    "#SLLETT#",
    "#LLLETT#",
    "#INUM#",
    "#LNUM#",
]


def generate_r1_tag_entry(tag_context: TagContext = None) -> str:
    """Assemble the R1 Tag content string using the shared tag system."""
    components: List[str] = []
    if random.random() < 0.5:
        components.append(random.choice(R1_PREFIX_CHOICES))

    core_parts = [
        random.choice(R1_KEYWORD_CHOICES),
        generate_tag_value(random.choice(R1_NAME_TAGS), tag_context),
        generate_tag_value(random.choice(R1_DATE_TAGS), tag_context),
        generate_tag_value(random.choice(R1_STRING_TAGS), tag_context),
    ]
    random.shuffle(core_parts)
    components.extend(core_parts)
    return R1_DELIMITER.join(components)


def generate_business_name():
    """Generate business name: FirstName + RandomLetters + BusinessWord + RandomLetters + Suffix"""
    first_name = fake.first_name()
    random_letters_1 = fake.lexify("??").upper()
    business_word = fake.word().capitalize()
    random_letters_2 = fake.lexify("??").upper()
    suffix = random.choice(BUSINESS_SUFFIXES)
    
    return f"{first_name} {random_letters_1} {business_word} {random_letters_2} {suffix}"

def generate_personal_name():
    """Generate personal name: FirstName + RandomTwoLetters"""
    first_name = fake.first_name()
    random_letters = fake.lexify("? ?").upper()
    
    return f"{first_name} {random_letters[0]}. {random_letters[2]}."

def generate_sender_name(name_type="business"):
    """
    Generate sender name based on type
    Args:
        name_type: "business" or "personal"
    Returns:
        Generated sender name string
    """
    if name_type == "business":
        return generate_business_name()
    elif name_type == "personal":
        return generate_personal_name()
    else:
        return generate_business_name()


class ContentManager:
    """Backend-only content generation - NO UI exposure"""
    
    def __init__(self):
        # Template 1: Own Proven Bodies (Spintax)
        self.body_parts = {
            "part1": ["Thank You for your Order.",
                      "Thank You for renewing your sub.",
                      "Success on your order status.",
                      "Update on your order status.",
                      "Successful renewal.",
                      "We're glad for your order.",
                      "We thank you for your renewal.",
                      "We thank you for your order.",
                      "We're glad on successful renewal.",
                      "Important update about your order.",
                      "Your order is confirmed.",
                      "Your order is placed.",
                      "Your order is renewed.",
                      "Your order is successful.",
                      "We appreciate your Purchase.",
                      "A subscription to your site is renewed with gratitude.",
                      "Thank you for your order, which has been processed successfully.",
                      "Let you know where your order stands at this time.",
                      "We were able to renew our lease with no problems.",
                      "We appreciate your purchase.",
                      "We appreciate your continued support and commitment to our mission.",
                      "We appreciate your business.",
                      "The renewal's success makes us happy.",
                      "This is a very important message about your purchase.",
                      "You have successfully placed an order.",
                      "The order has been submitted.",
                      "I'm re-confirming your order.",
                      "We have accepted your order.",
                      "We appreciate your Purchase.",
                      "A subscription to your site is renewed with gratitude.",
                      "Thank you for your order, which has been processed successfully.",
                      "Let you know where your order stands at this time.",
                      "We were able to renew our lease with no problems.",
                      "We appreciate your purchase.",
                      "We appreciate your continued support and commitment to our mission.",
                      "We appreciate your business.",
                      "The renewal's success makes us happy.",
                      "This is a very important message about your purchase.",
                      "You have successfully placed an order.",
                      "The order has been submitted.",
                      "I'm re-confirming your order.",
                      "We have accepted your order.",
                      "Thank you so much for your purchase.",
                      "My appreciation includes renewing my membership to your website.",
                      "The order you placed has been completed successfully, and we thank you for your patience.",
                      "Give you an update on the status of your order.",
                      "The lease renewal process went well.",
                      "Thank you for your purchase; we really value your business.",
                      "Your unwavering belief in us and dedication to our cause is much appreciated.",
                      "We value you as a customer.",
                      "We're glad that the renewal went well.",
                      "Please read this notice carefully as it pertains to your transaction.",
                      "The order you just placed went through without a hitch.",
                      "The request for service has been sent in.",
                      "Your order has been reconfirmed.",
                      "We will fulfill your purchase as soon as possible.",
                      "We are grateful to you for your Order.",
                      "I want to thank you for keeping your subscription active.",
                      "Congratulations on the success of your order status.",
                      "Any updates on the progress of your order? Renewal that goes smoothly",
                      "We're delighted for your order.",
                      "We are appreciative of your continued support.",
                      "We are grateful to you for placing your purchase.",
                      "We are happy to report that the renewal was successful.",
                      "Important new information about your purchase. Your order has been successfully processed.",
                      "Your order has been submitted.",
                      "Your order has been reactivated.",
                      "Your order has been processed successfully.",
                      "Thank you so much for your purchase.",
                      "I would like to express my appreciation by renewing a membership to your website.",
                      "We are grateful to you for your purchase; we have been able to properly complete processing it.",
                      "I just wanted to let you know the current status of your purchase.",
                      "We had no issues whatsoever when it came to renewing our lease.",
                      "We are grateful that you made this purchase.",
                      "We are grateful for your unwavering support and dedication to our organization's work.",
                      "We are grateful for your support of our company.",
                      "The successful completion of the renewal makes us delighted.",
                      "Regarding your purchase, there is a very important message that you must read.",
                      "You have completed the order placement process with success.",
                      "The order has been sent in successfully.",
                      "I am reiterating my confirmation of your purchase.",
                      "Your order has been processed and accepted.",
                      "Thank you so much for your purchase.",
                      "I would like to express my appreciation by renewing a membership to your website.",
                      "We are grateful to you for your purchase; we have been able to properly complete processing it.",
                      "I just wanted to let you know the current status of your purchase.",
                      "We had no issues whatsoever when it came to renewing our lease.",
                      "We are grateful that you made this purchase.",
                      "We are grateful for your unwavering support and dedication to our organization's work.",
                      "We are grateful for your support of our company.",
                      "The successful completion of the renewal makes us delighted.",
                      "Regarding your purchase, there is a very important message that you must read.",
                      "You have completed the order placement process with success.",
                      "The order has been sent in successfully.",
                      "I am reiterating my confirmation of your purchase.",
                      "Your order has been processed and accepted.",
                      "I am really grateful to you for your purchase.",
                      "As a token of my thanks, I have decided to continue my membership on your website.",
                      "We appreciate your patience in waiting for the completion of the order that you made; it was successfully fulfilled.",
                      "I wanted to keep you up to date on the progress of your purchase.",
                      "The procedure for renewing the lease proceeded smoothly.",
                      "We are grateful to you for your purchase; we place a high importance on your company.",
                      "We are grateful for your consistent support of us and commitment to the mission that we are working toward.",
                      "We appreciate having you as a client.",
                      "We are glad to hear that the renewal was successful.",
                      "In light of the fact that it refers to your transaction, please read this notification very carefully.",
                      "Your recent purchase went through without a hitch thanks to your careful attention to detail.",
                      "The service request has been sent successfully.",
                      "Your order has been verified for accuracy.",
                      "We will go to work on fulfilling your order as soon as we can.",
                      "We appreciate your Order.",
                      "Thanks for renewing your subscription.",
                      "Congratulations on the order status.",
                      "Update on the progress of your order.",
                      "Successful renewal.",
                      "We're delighted for your order.",
                      "We appreciate your renewal.",
                      "We appreciate your order.",
                      "We are pleased with the renewal.",
                      "Important update regarding your order.",
                      "Your order has been accepted.",
                      "The order has been placed.",
                      "Your order has been reinstated.",
                      "Your order has been accepted.",
                      "We are grateful for your Purchase.",
                      "Your website's membership is renewed with appreciation.",
                      "Thank you for your order, which was successfully processed.",
                      "Inform you of the status of your order at this time.",
                      "We were able to successfully renew our lease.",
                      "We are grateful for your purchase.",
                      "We value your ongoing support and dedication to our goal.",
                      "We value your patronage.",
                      "The success of the renovation makes us delighted.",
                      "This is a crucial notification about your purchase.",
                      "You have succesfully made a purchase.",
                      "This order has been placed.",
                      "I am verifying your order again.",
                      "We've acknowledged your purchase.",
                      "We are grateful for your Purchase.",
                      "Your website's membership is renewed with appreciation.",
                      "Thank you for your order, which was successfully processed.",
                      "Inform you of the status of your order at this time.",
                      "We were able to successfully renew our lease.",
                      "We are grateful for your purchase.",
                      "We value your ongoing support and dedication to our goal.",
                      "We value your patronage.",
                      "The success of the renovation makes us delighted.",
                      "This is a crucial notification about your purchase.",
                      "You have succesfully made a purchase.",
                      "This order has been placed.",
                      "I am verifying your order again.",
                      "We've acknowledged your purchase.",
                      "We really appreciate your purchase.",
                      "As a token of my thanks, I will renew my subscription to your website.",
                      "Your order has been successfully processed, and we appreciate your patience.",
                      "Provide an update about the progress of your order.",
                      "The renewal of the lease proceeded well.",
                      "Thank you for your purchase; we appreciate your business tremendously.",
                      "Your unshakable confidence in us and commitment to our cause are much appreciated.",
                      "We respect you as a client.",
                      "We're pleased that the renewal was successful.",
                      "Please carefully review this warning as it applies to your transaction.",
                      "Your recent order was processed without a hitch.",
                      "The service request has been sent.",
                      "Your order has been verified again.",
                      "Your order will be processed as quickly as possible.",
                      "We are appreciative of your Order.",
                      "I would like to thank you for maintaining your subscription.",
                      "Congratulations on the successful status of your order.",
                      "Any changes on the status of your order? Renewal that is efficient",
                      "We're glad for your order.",
                      "We are grateful for your ongoing support.",
                      "We appreciate you making an order with us.",
                      "We are pleased to announce that the renewal was successfully completed.",
                      "Important new details about your purchase. Your order has been processed successfully.",
                      "The order has been placed.",
                      "The status of your order has been restored.",
                      "Your order has been successfully processed.",
                      "We really appreciate your purchase.",
                      "I would want to show my thanks by renewing my website membership.",
                      "We are thankful for your purchase, which we have now successfully completed processing.",
                      "I wanted to update you on the current status of your order.",
                      "When it came to renewing our lease, we had no difficulties.",
                      "We appreciate you making this purchase.",
                      "We appreciate your consistent support and commitment to the mission of our organization.",
                      "We appreciate your support of our organization.",
                      "The renewal's successful completion fills us with joy.",
                      "Regarding your purchase, it is imperative that you read the following note.",
                      "You have successfully completed the order placing procedure.",
                      "The order has been successfully sent.",
                      "I am reaffirming my approval of your transaction.",
                      "Your order has been accepted after being processed.",
                      "We really appreciate your purchase.",
                      "I would want to show my thanks by renewing my website membership.",
                      "We are thankful for your purchase, which we have now successfully completed processing.",
                      "I wanted to update you on the current status of your order.",
                      "When it came to renewing our lease, we had no difficulties.",
                      "We appreciate you making this purchase.",
                      "We appreciate your consistent support and commitment to the mission of our organization.",
                      "We appreciate your support of our organization.",
                      "The renewal's successful completion fills us with joy.",
                      "Regarding your purchase, it is imperative that you read the following note.",
                      "You have successfully completed the order placing procedure.",
                      "The order has been successfully sent.",
                      "I am reaffirming my approval of your transaction.",
                      "Your order has been accepted after being processed.",
                      "I am really appreciative of your purchase.",
                      "As a gesture of my appreciation, I've chosen to maintain my membership on your website.",
                      "We appreciate your patience in waiting for the fulfillment of your purchase, which was completed satisfactorily.",
                      "I wanted to keep you informed on the status of your purchase.",
                      "The process for renewing the lease went without a hitch.",
                      "Your purchase is much appreciated, and we put a premium on your business.",
                      "We appreciate your continued support and dedication to the cause towards which we are working.",
                      "We value having you as a customer.",
                      "We're delighted to learn that the renewal went successful.",
                      "Due to the fact that this message pertains to your transaction, please read it carefully.",
                      "Your previous purchase went off without a hitch since you paid close attention to every detail.",
                      "The service request has been successfully sent.",
                      "Your order's correctness has been confirmed.",
                      "We will begin completing your purchase as soon as possible."],
            
            "part2": ["Please", "Kindly", "For more info please", "For more info kindly", "For more details please",
                      "For more details please", "To find out more please", "To find out more kindly"],
            
            "part3": ["check", "find", "search",
                      "search for", "look at", "look for"],
            
            "part4": ["the attached document", "the attached file", "the attachment document", "the attachment file", "the document below",
                      "the file below", "the attachment below", "the document attached", "the file attached", "the attachment attached"],
            
            "part5": ["urgently.", "immediately.",
                      "quickly.", "now.", "as soon as possible."]
        }
        
        # Template 2: Own content last update (reuses Template 1 part1 + bodyB)
        self.bodyB = [
            "For more info kindly search for the document attached immediately.",
            "For more details please find the attachment attached quickly.",
            "For more info kindly search the document attached urgently.",
            "For more info please look for the file attached as soon as possible.",
            "Kindly check the attached file quickly.",
            "For more details please look at the attached document now.",
            "For more info please find the attachment attached immediately.",
            "For more details please look for the attached file urgently.",
            "For more details please search for the attached document now.",
            "To find out more kindly look for the file below immediately.",
            "To find out more please look at the attached document quickly.",
            "For more info kindly search the file attached immediately.",
            "For more details please look at the attached document quickly.",
            "For more info please check the attachment file immediately.",
            "To find out more kindly check the document attached quickly.",
            "For more info kindly search the file attached as soon as possible.",
            "To find out more please check the file below immediately.",
            "To find out more please look at the attached file now.",
            "For more details please find the file below as soon as possible.",
            "Kindly look for the attached file as soon as possible.",
            "To find out more kindly check the attachment attached as soon as possible.",
            "Please search for the file below now.",
            "Please search the attachment attached urgently.",
            "To find out more please look for the file attached now.",
            "Please search for the attachment attached quickly.",
            "Kindly search for the attachment below immediately.",
            "To find out more kindly check the attachment attached quickly.",
            "For more details please look for the file below as soon as possible.",
            "Kindly search the document attached quickly.",
            "For more info kindly look at the document attached immediately.",
            "To find out more please look at the attached document now.",
            "For more details please look at the document below urgently.",
            "Kindly find the attached document urgently.",
            "Kindly look for the file attached now.",
            "Kindly search the attachment file urgently.",
            "To find out more please search for the attachment file as soon as possible.",
            "For more details please find the attachment below immediately.",
            "For more details please look for the file below now.",
            "To find out more please search for the file below now.",
            "For more info kindly find the attachment file quickly.",
            "For more info kindly search the document attached now.",
            "To find out more please look for the attachment file now.",
            "For more info kindly search the document attached as soon as possible.",
            "For more details please find the file below immediately.",
            "For more details please look for the attachment attached urgently.",
            "For more details please look for the document below quickly.",
            "For more info kindly find the attached document urgently.",
            "Kindly check the attachment document now.",
            "To find out more please look at the file below quickly.",
            "For more details please look at the attachment attached as soon as possible.",
            "For more info please look for the attachment file immediately.",
            "To find out more kindly check the attached document quickly.",
            "To find out more kindly look at the attached document as soon as possible.",
            "Please check the attached file quickly.",
            "Kindly look for the document attached immediately.",
            "Please look for the attachment document as soon as possible.",
            "To find out more kindly look at the document attached as soon as possible.",
            "For more details please check the attachment document now.",
            "Please check the attached file now.",
            "Please search the document below now.",
            "For more details please check the document attached immediately.",
            "Please search the document below as soon as possible.",
            "To find out more kindly look for the file attached urgently.",
            "For more info please find the document below now.",
            "To find out more please look for the attachment below as soon as possible.",
            "To find out more please search the document attached urgently.",
            "To find out more please look for the attached document as soon as possible.",
            "Please search for the attachment document urgently.",
            "To find out more please find the attachment below quickly.",
            "To find out more kindly look at the document attached immediately.",
            "To find out more kindly look at the attachment file immediately.",
            "For more details please look at the attachment document quickly.",
            "To find out more kindly check the attachment attached urgently.",
            "For more details please look for the file attached immediately.",
            "For more details please check the attachment below urgently.",
            "Kindly look at the attachment below urgently.",
            "Please look for the attachment file immediately.",
            "For more details please search the file below quickly.",
            "For more details please search the attachment attached urgently.",
            "To find out more please check the attachment attached immediately.",
            "Please look at the attachment file immediately.",
            "For more details please search for the attachment attached urgently.",
            "For more details please find the attachment below urgently.",
            "For more details please search the attachment below now.",
            "To find out more kindly search for the file attached urgently.",
            "Kindly look at the attachment below as soon as possible.",
            "To find out more please search for the attached document immediately.",
            "Please search the attached document as soon as possible.",
            "For more info please look at the document below urgently.",
            "Please look at the attachment document now.",
            "Kindly search for the document below quickly.",
            "To find out more please search for the attachment document quickly.",
            "To find out more kindly find the attachment document now.",
            "For more details please search the attached file urgently.",
            "Kindly search the document below immediately.",
            "For more info kindly look for the file attached now.",
            "For more information, please see the accompanying paper immediately.",
            "For more information, please refer to the attachment immediately.",
            "For further information, please search the enclosed file immediately.",
            "Please review the accompanying document as soon as possible for further information.",
            "Please review the enclosed file immediately.",
            "For more information, please see the accompanying file at this time.",
            "Please see the attachment for further information.",
            "Please refer immediately to the accompanying file for more information.",
            "Please check for the accompanying paper for more information.",
            "Please review the file listed below for more information promptly.",
            "Please see the attached file for further information.",
            "Please instantly search the attached file for further information.",
            "For further information, please see the enclosed paper immediately.",
            "Please see the attaching file immediately for more details.",
            "Please see the attached file immediately for more details.",
            "To learn more, please see the enclosed paper immediately.",
            "For further information, please search the attached file as soon as possible.",
            "Please review the file promptly for further details.",
            "To learn more, please review the accompanying material immediately.",
            "Please locate the PDF below as soon as possible for further information.",
            "Please review the enclosed file as quickly as possible.",
            "Please review the file for more information as soon as feasible.",
            "Please do a search for the file immediately.",
            "Please search the provided file immediately.",
            "Please search fast for the attached file.",
            "Please look immediately for the attachment below.",
            "Please review the file fast for further information.",
            "Please consult the attached pdf as soon as possible for further information.",
            "Please search the enclosed material quickly.",
            "Please review the material provided immediately for further information.",
            "Please locate the enclosed paper immediately.",
            "Please review the file attached immediately.",
            "Please examine the attached file as soon as possible for further information.",
            "Please locate the file below for more information.",
            "Please refer to the attached file for further information.",
            "To learn more, please search for the file listed below.",
            "For more information, please locate the attachment as soon as possible.",
            "Please examine the attached file for more information.",
            "Please locate the attached file immediately for further information.",
            "Please refer to the attachment for more information as soon as possible.",
            "For further information, please briefly review the paper provided below.",
            "Please review the attached material immediately.",
            "Please have a brief glance at the file below for further information.",
            "Please see the attached immediately for further information.",
            "Please review the accompanying paper as soon as possible for more details.",
            "Please review the accompanying material promptly.",
            "Please review the attached as quickly as possible.",
            "Please review the attached file as soon as possible for more information.",
            "Please refer to the attached file for more information.",
            "Please do a search of the document immediately.",
            "For more information, please see the enclosed paper immediately.",
            "Please do a search of the following document as soon as feasible.",
            "Please see the attached PDF immediately for further information.",
            "Please see the attached paper for more details.",
            "As soon as possible, please refer to the attached for further information.",
            "For more information, please search the enclosed file immediately.",
            "Please review the attached paper as soon as possible for further information.",
            "Please look for the attachment as soon as possible.",
            "Please locate the file below for more details.",
            "Please see the attached file immediately for further details.",
            "For more information, please see the attached file immediately.",
            "Please see the attachment for further information as soon as possible.",
            "Please refer to the file immediately for further information.",
            "For further information, please see the attached immediately.",
            "Please review the attached immediately.",
            "Please search for the file attachment quickly.",
            "For further information, please search the file below.",
            "For more information, please search the enclosed document immediately.",
            "For more information, please see the file immediately.",
            "Please review the file attached quickly.",
            "For more information, please see the file as soon as possible.",
            "For more information, please see the file below.",
            "To get more information, please examine the enclosed file immediately.",
            "Please review the attached as soon as feasible.",
            "Please look for the accompanying paper immediately for further information.",
            "Please do a search on the accompanying file as soon as feasible.",
            "Please do a fast search for the paper below.",
            "To learn more, please look for the attachment as soon as possible.",
            "Please see the attached file for more information.",
            "Please see the attached file for more details.",
            "If you want any more information, pls go at the paper that was included.",
            "Please refer to the file that was hastily attached for more information.",
            "Please check the paper that was included for more information as soon as possible.",
            "If you want any information, please have a look at the file that has been included as soon as possible.",
            "Please examine the enclosed file as soon as possible.",
            "Please have a look at the accompanying paper right now for more information.",
            "Please see the attachment that has been instantly attached for more information.",
            "Please look at the enclosed file as soon as possible for more information.",
            "If you're interested in further information, have a look at the paper that was included.",
            "If you are interested in learning more, pls check for the file below and do so right away.",
            "Please have a look at the following paper as soon as possible for more information.",
            "Please examine the attached file right away for any more information.",
            "Please have a brief glance at the accompanying paper for further information about this.",
            "Please examine the attached paper as soon as possible for more information.",
            "Please review the accompanying paper as soon as possible for more information.",
            "Please examine the attached file as soon as possible for any more information.",
            "Please have a look at the attached file right away for more information.",
            "Find the file that's been attached below as soon as you can for further information.",
            "Please have a look at the file that was provided as soon as you can.",
            "If you are interested in learning more, please check out the file that has been provided as soon as you can.",
            "Now would be a good time to look for the file below.",
            "Please do an immediate search in the attachment that has been attached.",
            "If you are interested in learning more, please check for the file that has been attached right now.",
            "Please do a brief search for the attachment that was connected.",
            "Please look at the file below and get back to me as soon as possible.",
            "If you are interested in learning more, pls check the attachment that has been swiftly attached.",
            "Please see the attached file as soon as possible for more information and refer to it as needed.",
            "Please search the given material as soon as possible.",
            "Please have a look at the accompanying paper right away for more information.",
            "Please have a look at the attached file for more information as soon as possible.",
            "Please find the attached material as soon as possible.",
            "Please have a look at the file that was just attached.",
            "Please do a search as soon as possible in the attached file.",
            "If you are interested in learning more, please look for the file that was attached as soon as you can.",
            "Please refer to the file that may be found below for more information.",
            "Please refer to the file that may be seen below right now for more information.",
            "Please look for the file that is provided below right now to learn more.",
            "Please locate the attached file as soon as possible for more information.",
            "Please examine the accompanying paper for more information right now.",
            "If you are interested in learning more, please search for the attached PDF right now.",
            "Please examine the enclosed paper thoroughly as soon as possible for more information.",
            "Please see the attached file below as soon as possible for more information.",
            "Please look at the file that was just sent for more information as soon as possible.",
            "Please look at the attached paper as soon as possible for more information.",
            "Please locate the accompanying paper as soon as possible for more information.",
            "Please review the attached material as soon as possible.",
            "If you are interested in further information, please have a look at the file that has been attached as soon as possible.",
            "Please have a look at the file that was attached right away for more information.",
            "Please have a look at the following material as soon as you can if you are interested in learning more.",
            "Kindly examine the given file as soon as possible.",
            "Please check for the material that has been attached as soon as possible.",
            "Please search for the paper that was included as soon as it is feasible to do so.",
            "Please take a moment to review the accompanying material as soon as you can for more information.",
            "Please see the attached paper at this time for more information.",
            "Check out the enclosed file right now, please.",
            "Please do a search in the attached paper right now.",
            "If you are interested in further information, do have a look at the enclosed paper right away.",
            "Please start your search as soon as possible in the paper that is below.",
            "Please have a look at the file that was attached right away for further information.",
            "Please refer to the paper that may be seen below right now for more information.",
            "If you are interested in learning more, please have a look at the file that has been provided below as soon as you can.",
            "Please search the accompanying paper as soon as possible for more information.",
            "If you are interested in learning more, please have a look at the following material as soon as you can.",
            "Urgent request: please hunt for the paper that was attached.",
            "To get more information, kindly locate the attachment provided below as soon as possible.",
            "Please have a look at the accompanying paper as soon as possible for further information.",
            "Please have a look at the attached file as soon as possible for more information.",
            "Please have a brief glance at the attached paper for further information about that.",
            "If you are interested in learning more, please examine the file that has been attached as soon as possible.",
            "Please review the file that has been provided below for more information as soon as possible.",
            "Please have a look at the attached file as soon as possible.",
            "Immediately check for the file that was attached to the email.",
            "Please do a brief search in the attached file for more information.",
            "Please search the file that has been attached immediately for additional information.",
            "If you are interested in further information, please look at the file that has been attached right away.",
            "Please have a look at the file that was attached right away.",
            "Please look at the file that was just attached for more information as soon as possible.",
            "Please locate the file below for more information as soon as possible.",
            "Please examine the file that has been provided below right now for more information.",
            "If you are interested in learning more, please look for the file that has been included as soon as possible.",
            "Please have a look at the attached file as soon as it becomes available.",
            "If you are interested in learning more, please look for the enclosed material right away.",
            "It would be helpful if you could search the accompanying paper as soon as you can.",
            "Please have a look at the paper that has been attached.",
            "Please search for the paper as rapidly as possible below.",
            "If you like to learn more, please look for the attached material as soon as possible.",
            "Find the attached file at this time if you would want more information.",
            "Please search the attached file as soon as possible for more information.",
            "Please do a search in the attached paper right away.",
            "Please find the attached file immediately for more information and look there.",
            "If you want any more information at this time, kindly refer to the document that is attached.",
            "If you need any further information at this time, kindly refer to the attached document.",
            "If you need any further information, you should search the attached file right away.",
            "If you need any further information, please have a look at the attached paper as soon as you can.",
            "Please take the time to examine the attached material as soon as possible.",
            "Please refer to the file that is now being attached for any further information.",
            "Additional details may be found in the file, which is attached here.",
            "In order to get more information, kindly consult the supplementary file right away.",
            "For more information, do refer to the paper that was provided with this.",
            "Please take a moment to go over the attached file, which has more details.",
            "For further details, kindly refer to the file that has been provided.",
            "Please do a search in the attached file as soon as possible for further information.",
            "If you want any further information at this time, kindly see the attached document.",
            "For more information, kindly have a look at the file that has been attached.",
            "For more information, please refer to the file that has been provided.",
            "If you are interested in learning more, please review the attached document as soon as possible.",
            "If you need any further information, please look through the accompanying file as soon as you can.",
            "Please take the time to examine the material as soon as possible for more information.",
            "Please go at the supplementary material right away if you are interested in learning more.",
            "For more details, a PDF document may be found below and should be accessed as soon as possible.",
            "Please take the time to go through the attached file as soon as you can.",
            "Please go through the material as soon as it is possible to find any further information.",
            "I would appreciate it if you could start looking for the file right now.",
            "I would appreciate it if you could search the attached file right away.",
            "Please look for the attached file as quickly as possible.",
            "Please check at the attachment right below this sentence.",
            "Please take the time to quickly check the file for any additional information.",
            "If you need any further information, do have a look at the accompanying PDF as soon as you can.",
            "Please look through the materials that are contained as rapidly as possible.",
            "In order to get further information, kindly go through the material that has been sent right away.",
            "Immediately, I need you to find the document that was contained.",
            "If you need any further information, please have a look at the accompanying file as soon as you can.",
            "For more details, kindly refer to the file that may be found below.",
            "In order to get further information, kindly refer to the file that has been provided.",
            "If you are interested in learning more, please look for the file provided below.",
            "Find the attachment as quickly as you can so that I can provide you with more details.",
            "For more details, please see the file that has been provided.",
            "For further details, kindly look for the file that was attached and open it right away.",
            "If you need any more information at this juncture, kindly refer to the attached document.",
            "Please take a moment to go through the attached document, which has further information.",
            "Please take the time to peruse the information that has been attached.",
            "If you need any further information, do have a quick look at the attached file.",
            "If you need any more information at this time, kindly refer to the document that has been provided.",
            "Please take the time to read the attached document as soon as you can for more information.",
            "Kindly go through the supplementary information as soon as possible.",
            "Please take the time to evaluate what has been attached as soon as you can.",
            "For more details, do have a look at the file that has been provided as soon as you can.",
            "For more details, please refer to the file that has been provided.",
            "I would appreciate it if you could do a search on the paper right away.",
            "I would appreciate it if you could do a search in the following document as soon as it is possible.",
            "For further details, please refer to the attached PDF at your earliest convenience.",
            "For more information, please refer to the document that has been attached.",
            "Please review the enclosed document in its entirety as soon as humanly feasible for further details.",
            "For more details, please have a look at the document that has been attached as soon as you can.",
            "Look for the attachment as soon as it becomes available, please.",
            "For more information, kindly refer to the file that may be found below.",
            "For further information, kindly refer to the file that has been attached right away.",
            "Please have a look at the attached file right away for any more details.",
            "If you want any further information, it may be found in the attachment, which you should look at as soon as possible.",
            "If you need any further information at this time, kindly consult the attached file.",
            "If you need any further information at this time, kindly refer to the document that has been provided.",
            "Please have a look at the accompanying document right away.",
            "Please do the search for the attached file as promptly as possible.",
            "Please examine the file that is provided below for any more information.",
            "Please do a search in the attached paper as soon as possible for more details.",
            "Please consult the attached material as soon as possible for more details.",
            "Please take the time to briefly peruse the attached file.",
            "Please review the attached PDF as soon as possible for further details.",
            "Please refer to the attached file for any more details.",
            "Examine the file that was just contained right away if you need any further information.",
            "Please take the time to evaluate what has been attached as soon as it is possible.",
            "In order to get further information at this time, kindly search for the attached document.",
            "Please do a search on the file that is being provided as soon as it is possible.",
            "Kindly do a quick search for the paper that is below.",
            "If you are interested in finding out more, please check for the attachment as soon as you can.",
            "Please see the attached file for details.",
            "The quick-loading attachment provides more information.",
            "Please quickly review the attached file for more information.",
            "If you need further details, check out the accompanying file right now.",
            "Please refer to the attached file for more explanation.",
            "Please see the attached file for more explanation.",
            "Please see the attached pdf for more information.",
            "Search for the attached file immediately for more information.",
            "Check see the attached file for further details.",
            "Please go over the accompanying document right away for more details.",
            "Immediately peruse the attached file for more information.",
            "If you want to know more, check out the attached file right now.",
            "Please refer to the attached file for more details.",
            "Please quickly go over the attached pdf for more details.",
            "Please see the attached pdf for further information.",
            "Here's a file you may download for further information.",
            "Please refer to the attached file for more information as soon as feasible.",
            "Please check your inbox for the urgently needed attachment.",
            "Please see the attachment for more details.",
            "In the meanwhile, I ask that you look at the attached document down below.",
            "Urgent, please check the attached file.",
            "Read the attached file for more details.",
            "Find the accompanying file as soon as possible, thanks!",
            "Please locate the attached file as soon as possible.",
            "The attached file contains additional information that should be reviewed as soon as possible.",
            "Please make a brief search of the accompanying paper.",
            "Please refer to the attached file right away for more details.",
            "Look at the attached file for more information.",
            "Please review the critical file that has been provided.",
            "Please see the accompanying document.",
            "We ask that you please check the attached file as soon as possible.",
            "If you're interested in learning more, look for the attached file right away.",
            "Please see the attached document for more information.",
            "Now, please see the attached file for more information.",
            "Check the file down below for additional info right now.",
            "Look over the attached file for more details.",
            "If you're interested in learning more, check out the attached file right now.",
            "Please see the accompanying paper as soon as possible for more details.",
            "See the attached file for more information.",
            "Please have a look at the attached file right away.",
            "Look at the attached file for further details.",
            "Please refer to the attachment for more information as soon as feasible.",
            "See the attached file right away for more details.",
            "Please review the accompanying file as soon as possible to get more information.",
            "We ask that you please review the accompanying document immediately.",
            "Please find the attached file right away.",
            "As soon as possible, please check the attached file.",
            "Read the accompanying file as soon as possible for further details.",
            "Please refer to the attached paper for more explanation at this time.",
            "Now is the time to verify the attached file.",
            "To begin your search, click below.",
            "As quickly as possible, please do a search of the attached document.",
            "Below is a paper detailing this matter in further detail.",
            "Have a look at the file attached below for further details as soon as possible.",
            "Please see the accompanying file ASAP for more information.",
            "Please refer to the attached file as soon as possible for more information.",
            "There is a time crunch, therefore I need you to look for the file attached immediately.",
            "Please refer to the file provided below for more details.",
            "Have a look at the attached file right away for further details.",
            "Please check the attached file right away for further details.",
            "Please refer to the attached paper for more information.",
            "Take a look at the file attached for further information.",
            "Please have a look at the document at the link below.",
            "The attached file is required immediately, so please check there.",
            "Look over the attached file below for further information.",
            "Please refer to the attachment for more information.",
            "I need you to have a look at the file I've attached right now.",
            "Please see the attachment for more information.",
            "Please see the attached file for more explanation at this time.",
            "In a timely manner, please review the document attached below.",
            "ASAP, I need you to search the accompanying file.",
            "Examine the attached file for more details.",
            "Take a look at the file I've attached right now.",
            "Find the attached file as soon as possible, thanks.",
            "Find the attached file ASAP to learn more.",
            "Read the accompanying PDF as soon as possible for more information.",
            "Please start searching the attached file right away.",
            "Read the paper that comes along with this for more explanation.",
            "If you need further details, check the attached file right away.",
            "To learn more, please have a look at the attached file as soon as possible.",
            "The accompanying document requires your urgent attention.",
            "Please refer to the attached file for more details at this time.",
            "For further details, please refer to the attached.",
            "If you need any more clarification, please see the attached document right away.",
            "For further details, see the attached document.",
            "If you want more clarification, please download the attached material and study it as soon as possible.",
            "For further details, check the accompanying document.",
            "If you need further information, please check the accompanying file right away.",
            "Please refer to the attached document right away for details.",
            "For more information, please refer to the attached document right away.",
            "See the accompanying document right away for more information.",
            "Please refer to the accompanying document as soon as possible for more information.",
            "Quickly peruse the accompanying document for further details.",
            "When further information is needed, please refer to the file as soon as possible.",
            "If you want to find out more, read the extra materials right now.",
            "For further details, please refer to the attached PDF file.",
            "The accompanying document should be read as soon as feasible.",
            "To learn more, please have a look at the file as soon as you can.",
            "Quickly do a search for the file, thanks.",
            "Instantly search the supplied folder.",
            "Locate the associated file as soon as possible.",
            "The attached file is urgent, so please check it out now.",
            "If you need further details, please study the file as soon as possible.",
            "If you want further information, please refer to the accompanying pdf as soon as feasible.",
            "If you need to find anything fast, check the contained materials.",
            "If you need any further details, please check the supplied materials right away.",
            "Get in touch with us as soon as you find the included document.",
            "Inquiring minds must instantly examine the enclosed document.",
            "In order to get further details, please check out the attached file right away.",
            "For more details, see the attached file.",
            "If you need further details, please see the accompanying document.",
            "Click on the link below to get the relevant material and expand your knowledge.",
            "Find the attachment as soon as possible for more details.",
            "If you want additional details, have a look at the attached file.",
            "Immediately find the attached file for further details.",
            "If you need any more explanation, please see the file attached to this message.",
            "Please refer to the document attached for further details.",
            "Please take the time right now to read the accompanying documents.",
            "For further details, please see the attached file.",
            "If you need further information, please refer to the document I have provided right away.",
            "If you need further information, read the attached document as soon as possible.",
            "It is imperative that you read the supplementary materials as soon as possible.",
            "Quickly read the accompanying document, please.",
            "If you want more clarification, please refer to the enclosed document as soon as possible.",
            "For more details, see the accompanying document.",
            "Immediate document search required.",
            "Check the attached document right away for details.",
            "As soon as possible, please search the attached file.",
            "If you want any further information, please refer to the PDF file that has been supplied.",
            "For more information, please refer to the accompanying article.",
            "For further details, please see the attachment as soon as possible.",
            "Quickly peruse the attached document for more details.",
            "Immediately peruse the accompanying document for further details.",
            "When possible, check the attached file.",
            "For more information, see the attached file.",
            "If you need further information, please see the accompanying file right away.",
            "As soon as possible, please refer to the attached for further details.",
            "If you need any further information, please check the attached file right away.",
            "Please refer to the attachment for details right away.",
            "The following memo requires your quick attention.",
            "Please see the attached document for details.",
            "Please consult the accompanying material as soon as possible for more details.",
            "Check the attached file right away for details.",
            "Please have a short look at the accompanying document.",
            "ASAP review of the file is recommended for further details.",
            "Please review the attached PDF right away for further details.",
            "As soon as possible, please go through the enclosed document.",
            "To learn more, check out the document that was included.",
            "As quickly as possible, do a search in the attached file.",
            "Please do a quick search for the article I've linked to.",
            "Read on for additional info that can't wait to be found in the attached file.",
            "More details may be found in the attached file.",
            "You may find further information in the attached file.",
            "The enclosed document contains additional details that may be of interest to you.",
            "To learn more, have a look at the file that was quickly attached.",
            "If you need further information, please refer to the enclosed document as soon as possible.",
            "The attached file has additional details that may be of interest to you; please review it as soon as possible.",
            "Take the time to review the attached document right now.",
            "If you want to know more, you may check out the paper that came along with this right now.",
            "For more details, please refer to the file that was automatically uploaded.",
            "Check out the attached document as soon as possible for additional details.",
            "If you're interested in extra details, take a look at the document that was supplied.",
            "Please download the attached file and read it immediately if you are interested in reading more.",
            "Please take a look at the accompanying document as soon as possible for further details.",
            "If you need any more clarification, please see the accompanying file.",
            "Please take a cursory peek at the attached document for additional information about this.",
            "Review the enclosed document as soon as possible for more explanation.",
            "For more details, please refer to the attached document as soon as possible.",
            "If you need any further details, please have a look at the accompanying file.",
            "In order to get the whole story, check out the attached file right immediately.",
            "Please review the accompanying document as soon as possible for further details.",
            "Check out the attached file as soon as you can.",
            "Check out the attached file as soon as possible if you're curious to find out more.",
            "Find the file down there now, since you're going to need it.",
            "It is imperative that you quickly search the enclosed document.",
            "Right now, there's an attached file you may look at if you're curious.",
            "Do a quick search for the attached file, and I'll gladly send it to you.",
            "Examine the attached file and come back to me as soon as you can.",
            "Please see the file that has been hastily added for further information.",
            "If you require any further details, please check out the attached file right away.",
            "It is imperative that you quickly search the provided resources.",
            "To learn more, please see the attached article.",
            "As soon as possible, I'd appreciate it if you'd have a look at the attached file.",
            "As soon as feasible, I'd want you to locate the accompanying documents.",
            "Please have a look at the accompanying document.",
            "The given file has to be searched as quickly as feasible.",
            "Look for the attached file as soon as possible if you're curious to find out more.",
            "For more reading, please see the attached file.",
            "If you're interested in reading more about this, click on the attached PDF below.",
            "If you need any more explanation, please look for the accompanying documents right away.",
            "Read the attached document for more explanation at this time.",
            "Please look at the attached PDF right now if you're interested in reading more.",
            "If you need further information, please review the accompanying document as soon as possible.",
            "As soon as possible, please refer to the attached file for more details.",
            "A file has been delivered to you, and we ask that you you review it as soon as possible in order to learn more.",
            "If you need further information, please see the enclosed document right away.",
            "In order to get further details, you need quickly find the document that goes along with it.",
            "As soon as possible, please read the accompanying documents.",
            "Check out the accompanying document right now if you want to learn more.",
            "If you need further information, please check out the attached file right immediately.",
            "If you are curious in this topic, I recommend reading the following.",
            "Please take the time to review this material as soon as possible.",
            "As soon as possible, please verify that you have received the enclosed documents.",
            "As soon as it is practical, please go looking for the accompanying document.",
            "If you need any more clarification, please read the supporting documents as soon as possible.",
            "In the meanwhile, the accompanying article has further details.",
            "Please have a look at the attached file straight away.",
            "The enclosed document should be searched immediately.",
            "Check out the included document right immediately if you want to learn more.",
            "Start your research as soon as possible in the document provided below.",
            "If you need any further details, please check out the accompanying file right immediately.",
            "If you'd like to learn more, have a look at the paper that's available right now below.",
            "Please review the attached material as soon as possible if you are interested in knowing more.",
            "If you need any further details, see the attached document as soon as possible.",
            "Please review the following resources as soon as possible if you are curious in finding out more.",
            "Please find the enclosed document as soon as possible.",
            "Please see the attached document as soon as possible for more details.",
            "Please take a look at the attached document as soon as possible for additional details.",
            "If you need further details, please check out the enclosed document right away.",
            "If you want to learn more about it, please have a look at the accompanying document.",
            "Please have a look at the accompanying documents right away if you're curious about this topic.",
            "If you need further details, please check out the attached file as soon as possible.",
            "As soon as possible, I'd appreciate it if you'd review the document I've included.",
            "Look at the email's attachments right away to see whether the file you need is there.",
            "If you need additional details, go over the accompanying file.",
            "If you need any more clarification, check out the accompanying file right away.",
            "Please review the enclosed document immediately if you want further details.",
            "As soon as possible, please review the accompanying document.",
            "Immediately upon receiving this email, please review the attached file for more details.",
            "For more details, please refer to the attached file as soon as possible.",
            "Please have a look at the attached file for more details.",
            "Please check the attached file as soon as possible if you're curious to find out more.",
            "Please check the included materials right immediately if you're curious to find out more.",
            "Searching the supplementary paper as quickly as possible will be appreciated.",
            "Review the enclosed document, thank you.",
            "Just type in what you know about the paper below and hit search as soon as feasible.",
            "If you want to learn more, please search for the enclosed information as soon as feasible.",
            "Find the attached file at this moment if you would like extra details.",
            "The accompanying file may provide further details; please check it as soon as possible.",
            "If you need to find anything fast, search the accompanying document.",
            "If you need more clarification, please open the accompanying file.",
            "Please see the following paper if you want more clarification at this time.",
            "Please see the accompanying paper for further details if necessary right now.",
            "Search the attached file immediately if you require any further details.",
            "If you require any additional information, please take a look at the enclosed document as soon as you can.",
            "Review the enclosed documents as soon as feasible.",
            "Any questions that may arise may be answered by reviewing the accompanying material.",
            "Attached file has further information.",
            "Do read the document that came with this for more details.",
            "You may find additional information in the accompanying file, which I ask you to review.",
            "If you need further details, please see the accompanying file as soon as possible.",
            "See the attached file if you need any further details right now.",
            "Take a look at the accompanying file right away if you want to find out more.",
            "Review the attached material as soon as possible if you want further details.",
            "Take a look at the resources as soon as you can for further details.",
            "If you want to know more, you should check out the other resources right now.",
            "You may find a PDF with further information down below; read it as soon as you can.",
            "Check see the enclosed document as soon as you have a chance.",
            "Please review the resources as soon as you have the time to learn more about them.",
            "If you could start searching for the file right now, that would be great.",
            "Immediately searching the supplied file would be very appreciated.",
            "Quickly check for the attached document.",
            "See the file attached to this sentence for further information.",
            "If you have a moment, please review the file to see if anything more needs to be included.",
            "Please review the PDF file that was sent in case you need any further details.",
            "As soon as possible, please review the contents.",
            "Kindly review the attached documents as soon as possible for further details.",
            "I need you to locate the included paper immediately.",
            "Please review the supplementary material as soon as possible if you need any more explanation.",
            "Please see the attached file for further details.",
            "Please locate the file as soon as possible so that I may provide you more information.",
            "There is a file attached for your perusal if you'd want to learn more.",
            "Find the attached file and open it for further information.",
            "Please see the attachment if you want more clarification.",
            "If you need further details, please see the accompanying paper.",
            "To help you, we've included some relevant materials; please read them.",
            "Please have a look at the attached file for further details if necessary.",
            "For any further inquiries, please see the attached file.",
            "If you'd like further details, please read the enclosed paper as soon as possible.",
            "Please read the extra materials as soon as you can.",
            "As soon as possible, please review the enclosed materials.",
            "Please do a search of the article without delay.",
            "Please do a search in the attached file as soon as feasible.",
            "When you get a moment, please have a look at the accompanying PDF for further information.",
            "For further information, please read the accompanying material carefully as soon as possible.",
            "Please check back for the attachment as soon as it is made available.",
            "Please see the accompanying document straight away for further details.",
            "If you want any more explanation, please refer to the following document straight immediately.",
            "Check out the attachment right away if you need any further details, since they may be included there.",
            "Please refer to the accompanying file for further details if you have any questions at this time.",
            "Please review the attached paper for further details if necessary at this time.",
            "Quickly review the file that has been attached.",
            "If you need to find the attached file, please do so as soon as possible.",
            "If you want more clarification, please see the attached documents.",
            "For more information, please quickly search the accompanying article.",
            "For more information, please see the attachments.",
            "Thank you for taking a few moments to go through the enclosed document.",
            "More information may be found in the accompanying PDF, which you should check as soon as possible.",
            "If you want more information, please see the accompanying file.",
            "If you require further information, please see the attached material right immediately.",
            "Please review the enclosed materials as soon as possible.",
            "Right now, the best way to gain more details is to look for the accompanying paper.",
            "As soon as you are able, please do a search on the supplied file.",
            "Please find the attached document and read it.",
            "Please examine the attachment as soon as possible if you're curious to learn more."
        ]
        
        # Keep default subjects for proven mode
        self.default_subjects = DEFAULT_SUBJECTS  # Use existing array
    
    def get_subject_and_body(self, template_mode="own_proven", tag_context: TagContext = None):
        """Main function - returns (subject, body) based on template."""
        mode = (template_mode or "own_proven").lower()

        if mode == "r1_tag":
            tag_content = generate_r1_tag_entry(tag_context)
            return tag_content, tag_content

        # Always generate subject using new prefix pattern approach
        subj_info = generate_subject_with_prefix_pattern()
        subject = subj_info["final_subject"]

        if mode == "own_proven":
            body = self._generate_spintax_body()
        elif mode == "gmass_inboxed":
            # Redesigned: subject from defaults, body = part1 + delimiter + bodyB
            body = self._generate_own_content_last_update()
        else:
            # Fallback to proven mode
            body = self._generate_spintax_body()

        return subject, body
    
    def _generate_spintax_body(self):
        """Private: Sequential random from each part"""
        return " ".join([
            random.choice(self.body_parts["part1"]),
            random.choice(self.body_parts["part2"]),
            random.choice(self.body_parts["part3"]),
            random.choice(self.body_parts["part4"]),
            random.choice(self.body_parts["part5"])
        ])
    
    def _generate_own_content_last_update(self):
        """Private: Compose body using Template 1 part1 + delimiter + bodyB"""
        first = random.choice(self.body_parts["part1"])  # reuse Template 1 part1
        delim = random.choice([' ', '\n'])
        tail = random.choice(self.bodyB)
        return f"{first}{delim}{tail}"

def generate_subject_with_prefix_pattern():
    """Generate subject with prefix pattern: base_subject + prefix + letters + numbers"""
    base_subject = random.choice(DEFAULT_SUBJECTS)
    prefix_array = ['invo_', 'invce ', 'invoice-', 'po#', 'po ', 'po_', 'doc_', 'doc ', 'doc-', 'doc#', 'po-', 'invoxx#', 'inv', 'inv_', 'inv#', 'invv-']
    selected_prefix = random.choice(prefix_array)
    letter1 = random.choice(string.ascii_uppercase)
    letter2 = random.choice(string.ascii_uppercase)
    letter_pattern = f"{letter1}{letter2}"
    number_pattern = random.randint(9999, 99999)
    prefix_pattern = f"{selected_prefix}{letter_pattern}{number_pattern}"
    final_subject = f"{base_subject} {prefix_pattern}"
    
    return {
        "base_subject": base_subject,
        "selected_prefix": selected_prefix,
        "letter_pattern": letter_pattern,
        "number_pattern": number_pattern,
        "prefix_pattern": prefix_pattern,
        "final_subject": final_subject
    }


# Global instance for easy import
content_manager = ContentManager()

