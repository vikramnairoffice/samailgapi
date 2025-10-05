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
- Legacy `content.render_tagged_content` and `content.expand_spintax` proxy to these adapters so existing flows stay untouched.
- Adapter unit coverage lives in `tests/test_core_spintax.py` (context overrides + RNG injection).

## Attachments & Invoices
```
# core/attachments.py
def choose_static(include_pdfs: bool, include_images: bool, *, seed: int | None = None) -> dict[str, str]
def choose_from_folder(folder_path: str | os.PathLike[str], *, seed: int | None = None) -> dict[str, str]
def build(config: dict, lead: str | dict, invoice_factory: Callable[[], InvoiceGenerator] | None = None, *, seed: int | None = None) -> dict[str, str]

# core/invoice.py (adapter over existing generator)
class InvoiceGenerator:
    def generate_for_recipient(email: str, phone_numbers: str, fmt: str) -> str
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
def send(*, email: str, password: str, to_email: str, subject: str, body: str, from_header: str | None = None, attachments: dict[str, str] | None = None, headers: dict[str, object] | None = None) -> None

def mailbox_totals(email: str, password: str) -> dict[str, int]

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
## Manual Mode
```
# manual/manual_config_adapter.py
def create_config(data: dict | ManualConfig | None = None, **overrides) -> ManualConfig

def build_context(config: ManualConfig, lead_email: str) -> dict[str, str]

def render_subject(config: ManualConfig, context: dict[str, str]) -> str

def render_body(config: ManualConfig, context: dict[str, str]) -> tuple[str, str]

def build_attachments(config: ManualConfig, context: dict[str, str]) -> dict[str, str]

def resolve_sender_name(config: ManualConfig, fallback_type: str = 'business') -> str

def render_email(config: ManualConfig, lead_email: str) -> dict[str, Any]

def parse_extra_tags(rows: Sequence[Sequence[str]] | None) -> dict[str, str]

def to_attachment_specs(files: Iterable[object] | None = None, *, inline_html: str = '', inline_name: str = '') -> Sequence[ManualAttachmentSpec]

def preview_attachment(spec: ManualAttachmentSpec) -> tuple[str, str]

# manual/manual_preview_adapter.py
def build_snapshot(config: ManualConfig, *, preview_email: str, selected_attachment_name: str | None = None) -> tuple[list[str], str, dict[str, str], dict[str, bool]]

def attachment_listing(specs: Sequence[ManualAttachmentSpec]) -> tuple[list[str], str | None, str, str]

def attachment_preview(specs: Sequence[ManualAttachmentSpec], selected_name: str) -> tuple[str, str]
```

Adapters keep the Gradio manual preview outputs stable while the orchestrator is decomposed.
