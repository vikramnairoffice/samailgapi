# Module Interfaces (Contracts)

Adapters expose the legacy implementations behind the new modular interfaces. Until native v2 modules land, these contracts are fulfilled by forwarding to the existing code paths.

## Leads
```
# core/leads_csv.py
def read(path: str) -> list[dict]:  # keys: email,fname,lname (adapter wraps legacy reader)

# core/leads_txt.py
def read(path: str) -> list[str]     # legacy emails only (adapter maintains behaviour)
```

## Spintax & Rendering
```
# core/spintax.py
def render_tags(html: str, data: dict) -> str  # {{FNAME}}/{{LNAME}} from CSV/TXT adapters, {{TFN}} from UI input, {{LOGO}} from remote logo list, {{Product}} from product_bundles.json
def expand_spintax(html: str, rng: random.Random | None = None) -> str  # resolves {option|sets}

def expand(html: str, data: dict, rng: random.Random | None = None) -> str  # render tags first, then spintax

# core/html_randomizer.py
def randomize(html: str, seed: int | None = None) -> str  # wraps existing randomizer

# core/html_renderer.py
def to_pdf(html: str, out_path: str) -> str
def to_png(html: str, out_path: str) -> str
def to_heif(html: str, out_path: str) -> str
```

## Attachments & Invoices
```
# core/attachments.py
def choose_static(include_pdfs: bool, include_images: bool, *, seed: int | None = None) -> list[str]
def build(config: dict, lead: dict, *, seed: int | None = None) -> dict[str, str]

# core/invoice.py (adapter over existing generator)
class InvoiceGenerator:
    def generate_for_recipient(email: str, phone_numbers: list[str], fmt: str) -> str
```

## Credentials
```
# credentials/token_json.py
def load(path: str) -> tuple[str, Credentials]

# credentials/app_password.py
def load(path: str) -> list[dict]  # email, app_password, optional cap

def fetch_mailbox_totals(email: str, password: str) -> dict  # optional metrics

# credentials/oauth_json.py
def initialize(client_json: str) -> Credentials  # in-memory tokens; returns Gmail+Drive scope credentials
```

## Sending & Execution
```
# senders/gmail_rest.py
def send(email: str, to_email: str, subject: str, body: str, *, attachments: dict[str, str], headers: dict[str, str]) -> dict

# senders/gmail_smtp.py
def send(email: str, password: str, message: email.message.Message) -> dict

# exec/threadpool.py
class ThreadPoolExecutor:
    def submit(fn, *args, **kwargs) -> Future

# exec/serial.py
class SerialExecutor:
    def run(tasks: Iterable[Callable[[], Any]]) -> list[Any]
```

## Orchestrator & Modes
```
# orchestrator/ui_shell.py
def build(app: gr.Blocks, *, adapters: UIAdapters) -> None  # mounts shared components

# orchestrator/modes.py
def register(name: str, runner: Callable) -> None
def get(name: str) -> Callable
```

Contracts must remain backward-compatible until adapters are swapped for native v2 modules. Any signature change requires updated guard tests and documentation.
