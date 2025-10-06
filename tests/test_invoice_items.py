import random

from simple_mailer.invoice import InvoiceGenerator

BRAND_POOLS = {
    "Microsoft Office": {
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
    "Zoom": {
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
    "Windows Defender": {
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
    "Oracle Office": {
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
}

SECONDARY_SUFFIXES = [
    "Complimentary Plus",
    "Premium Package",
    "Package 2023",
    "Combo",
    "Premium Support",
]

PRIMARY_NAME_TO_BRAND = {
    name: brand
    for brand, pools in BRAND_POOLS.items()
    for name in pools["primary"]
}
SECONDARY_NAME_TO_BRAND = {}
for brand, pools in BRAND_POOLS.items():
    for raw_name in pools["secondary"]:
        SECONDARY_NAME_TO_BRAND[raw_name.strip()] = brand
    for suffix in SECONDARY_SUFFIXES:
        combined_name = f"{brand} {suffix}".strip()
        SECONDARY_NAME_TO_BRAND[combined_name] = brand
DESCRIPTION_POOL = {
    "Complimentary Plus",
    "Premium Package",
    "Package 2023",
    "Combo",
    "Premium Support",
    "2 Years 5 Devices",
    "1 Year 10 Devices",
    "5 Years Subscription",
    "3 Years 4 Devices",
    "1 Year 1 Device",
    "5 Years 5 Devices",
    "All Premium Features Included",
    "Premium Activation",
    "Premium Features",
    "Instant Activation",
}


def test_generate_invoice_data_uses_product_pools():
    invoice_generator = InvoiceGenerator()
    random.seed(1234)

    data = invoice_generator.generate_invoice_data()

    assert "items" in data
    assert len(data["items"]) == 2

    primary, secondary = data["items"]

    assert primary["name"] in PRIMARY_NAME_TO_BRAND
    assert secondary["name"].strip() in SECONDARY_NAME_TO_BRAND
    assert (
        PRIMARY_NAME_TO_BRAND[primary["name"]]
        == SECONDARY_NAME_TO_BRAND[secondary["name"].strip()]
    )

    assert primary["desc"] in DESCRIPTION_POOL
    assert secondary["desc"] in DESCRIPTION_POOL


def test_generate_invoice_data_varies_item_selection():
    invoice_generator = InvoiceGenerator()

    unique_item_pairs = set()
    for seed in range(10):
        random.seed(seed)
        data = invoice_generator.generate_invoice_data()
        pair = tuple(item["name"] for item in data["items"])
        unique_item_pairs.add(pair)

    assert len(unique_item_pairs) > 1
