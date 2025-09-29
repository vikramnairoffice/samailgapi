"""Helpers for the manual sending mode (tag rendering & attachment conversions)."""

from __future__ import annotations

import base64
import os
import random
import contextlib
import shutil
import tempfile
import textwrap
import uuid
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageChops
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

try:
    from docx import Document  # type: ignore
    DOCX_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    DOCX_AVAILABLE = False
    Document = None  # type: ignore

from content import expand_spintax, render_tagged_content, generate_sender_name

from html_randomizer import randomize_html
from html_renderer import html_renderer, PlaywrightUnavailable


_TEXT_EXTENSIONS = {'.txt', '.csv', '.md', '.json', '.html', '.htm'}
_HTML_EXTENSIONS = {'.html', '.htm'}
_ATTACHMENT_ROOT = Path(tempfile.gettempdir()) / "simple_mailer_manual"
_ATTACHMENT_ROOT.mkdir(parents=True, exist_ok=True)

class _HTMLTextExtractor(HTMLParser):
    """Basic HTML to text converter preserving simple block breaks."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: List[str] = []

    def handle_data(self, data: str) -> None:  # pragma: no cover - builtin
        if data:
            self._parts.append(data)

    def handle_starttag(self, tag: str, attrs):  # pragma: no cover - builtin
        if tag.lower() == 'br':
            self._parts.append('\n')


    def handle_endtag(self, tag: str) -> None:  # pragma: no cover - builtin
        if tag.lower() in {'p', 'div', 'section', 'li', 'br'}:
            self._parts.append('\n')


    def get_text(self) -> str:
        return ''.join(self._parts)


def _html_to_text(html: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(html)
    return parser.get_text()


def _random_suffix() -> str:
    return uuid.uuid4().hex[:8]


def _finalize_html_payload(raw_html: str, *, enable_random: bool, seed: Optional[int]) -> str:
    if not raw_html:
        return raw_html
    needs_snapshot = '<script' in raw_html.lower() if isinstance(raw_html, str) else False
    rendered = raw_html
    if needs_snapshot or enable_random:
        try:
            rendered = html_renderer.render_html_snapshot(rendered, seed=seed)
        except PlaywrightUnavailable as exc:
            if needs_snapshot:
                raise RuntimeError(str(exc)) from exc
    if enable_random:
        rendered = randomize_html(rendered, enabled=True, seed=seed)
    return rendered


def _wrap_lines(text: str, width: int = 90) -> List[str]:
    lines: List[str] = []
    for raw_line in text.splitlines() or [""]:
        stripped = raw_line.rstrip()
        if not stripped:
            lines.append("")
            continue
        wrapped = textwrap.wrap(stripped, width=width)
        lines.extend(wrapped or [""])
    return lines or [""]


def _text_to_pdf(text: str, destination: Path) -> None:
    dest_parent = destination.parent
    dest_parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(destination), pagesize=letter)
    width, height = letter
    lines = _wrap_lines(text)
    y = height - 72
    for line in lines:
        if y < 72:
            pdf.showPage()
            y = height - 72
        pdf.drawString(72, y, line)
        y -= 14
    pdf.save()


def _ensure_heif_plugin() -> None:
    try:
        import pillow_heif  # type: ignore  # noqa: F401 - registers HEIF plugin
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Install 'pillow-heif' to enable HEIF conversion.") from exc


def _save_image(image: Image.Image, destination: Path, image_format: str = 'PNG') -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fmt = (image_format or 'PNG').upper()
    if fmt == 'HEIF':
        _ensure_heif_plugin()
    image.convert('RGB').save(destination, format=fmt)


def _text_to_image(text: str, destination: Path, image_format: str = 'PNG') -> None:
    font = ImageFont.load_default()
    lines = _wrap_lines(text, width=60)
    max_width = max((font.getbbox(line)[2] for line in lines), default=0)
    line_height = font.getbbox('Ag')[3] + 6
    img_width = max(300, max_width + 40)
    img_height = max(200, line_height * len(lines) + 40)
    image = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(image)
    y = 20
    for line in lines:
        draw.text((20, y), line, fill='black', font=font)
        y += line_height
    _save_image(image, destination, image_format)


def _image_to_pdf(image_path: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(destination), pagesize=letter)
    width, height = letter
    with Image.open(image_path) as img:
        img_width, img_height = img.size
    aspect = img_width / max(img_height, 1)
    max_width = width - 144
    render_width = min(max_width, img_width)
    render_height = render_width / max(aspect, 1)
    if render_height > height - 144:
        render_height = height - 144
        render_width = render_height * aspect
    x = (width - render_width) / 2
    y = (height - render_height) / 2
    pdf.drawImage(ImageReader(str(image_path)), x, y, width=render_width, height=render_height, preserveAspectRatio=True)
    pdf.showPage()
    pdf.save()



def _trim_rendered_image(image: Image.Image, padding: int = 12) -> Image.Image:
    """Crop extra page whitespace after rendering HTML."""
    rgb = image.convert('RGB')
    background_color = rgb.getpixel((0, 0)) if rgb.size != (0, 0) else (255, 255, 255)
    background = Image.new('RGB', rgb.size, background_color)
    diff = ImageChops.difference(rgb, background)
    bbox = diff.getbbox()
    if not bbox:
        return rgb.copy()
    left, top, right, bottom = bbox
    left = max(left - padding, 0)
    top = max(top - padding, 0)
    right = min(right + padding, rgb.width)
    bottom = min(bottom + padding, rgb.height)
    return rgb.crop((left, top, right, bottom))



def _html_to_pdf_rendered(html: str, destination: Path) -> None:
    try:
        html_renderer.render_pdf(html, destination)
    except PlaywrightUnavailable as exc:
        raise RuntimeError(str(exc)) from exc



def _html_to_image(html: str, destination: Path, image_format: str = 'PNG', zoom: float = 2.0) -> None:
    try:
        rendered = html_renderer.render_image(html)
    except PlaywrightUnavailable as exc:
        raise RuntimeError(str(exc)) from exc
    trimmed = _trim_rendered_image(rendered)
    _save_image(trimmed, destination, image_format)



def _text_to_docx(text: str, destination: Path) -> None:
    if not DOCX_AVAILABLE:
        raise RuntimeError("python-docx is required for DOCX conversion. Install with `pip install python-docx`.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    document = Document()
    for line in text.splitlines() or [text]:
        document.add_paragraph(line)
    document.save(str(destination))


@dataclass
class ManualAttachmentSpec:
    path: str = ''
    name: str = ''
    orig_name: Optional[str] = None
    inline_content: Optional[str] = None

    @property
    def display_name(self) -> str:
        if self.orig_name:
            return self.orig_name
        if self.name:
            return self.name
        if self.path:
            return os.path.basename(self.path)
        return 'attachment'

    def suffix(self) -> str:
        display = self.display_name
        suffix = Path(display).suffix.lower()
        if suffix:
            return suffix
        if self.inline_content is not None:
            return '.html'
        if self.path:
            return Path(self.path).suffix.lower()
        return ''

@dataclass
class ManualConfig:
    enabled: bool
    subject: str
    body: str
    body_is_html: bool
    tfn: str
    body_image_enabled: bool = False
    randomize_html: bool = False
    extra_tags: Dict[str, str] = field(default_factory=dict)
    attachments: List[ManualAttachmentSpec] = field(default_factory=list)
    attachment_mode: str = 'original'
    attachments_enabled: bool = False
    sender_name: str = ''
    change_name_every_time: bool = False
    sender_name_type: str = 'business'

    def build_context(self, lead_email: str) -> Dict[str, str]:
        context: Dict[str, str] = {'email': lead_email}
        if self.body:
            context['content'] = self.body
        if self.tfn:
            context['tfn'] = self.tfn
        for key, value in self.extra_tags.items():
            if not key:
                continue
            if value is None:
                continue
            context[key] = value
        if self.randomize_html and '_style_seed' not in context:
            context['_style_seed'] = random.randint(0, 2**31 - 1)
        return context

    def render_subject(self, context: Dict[str, str]) -> str:
        return render_tagged_content(self.subject or '', context)

    def render_body(self, context: Dict[str, str]) -> Tuple[str, str]:
        rendered = render_tagged_content(self.body or '', context)
        if self.body_is_html:
            cleaned = rendered.strip()
            if cleaned and not cleaned.lower().startswith('<'):
                rendered = f'<p>{rendered}</p>'
            seed = context.get('_style_seed')
            finalized = _finalize_html_payload(rendered, enable_random=self.randomize_html, seed=seed)
            finalized = expand_spintax(finalized)
            if self.body_image_enabled and finalized.strip():
                image_path = _ATTACHMENT_ROOT / f"body_{_random_suffix()}.png"
                _html_to_image(finalized, image_path, image_format="PNG")
                try:
                    payload = image_path.read_bytes()
                finally:
                    with contextlib.suppress(FileNotFoundError):
                        image_path.unlink()
                encoded = base64.b64encode(payload).decode("ascii")
                img_tag = f'<img src="data:image/png;base64,{encoded}" alt="Email body image" />'
                return img_tag, 'html'
            return finalized, 'html'
        return expand_spintax(rendered), 'plain'
    def resolve_sender_name(self, fallback_type: str = 'business') -> str:
        if self.change_name_every_time or not (self.sender_name or '').strip():
            return generate_sender_name(self.sender_name_type or fallback_type)
        return self.sender_name.strip()

    def build_attachments(self, context: Dict[str, str]) -> Dict[str, str]:
        if not self.attachments_enabled or not self.attachments:
            return {}
        conversion = (self.attachment_mode or 'original').lower()
        results: Dict[str, str] = {}
        style_seed = context.get('_style_seed')
        for spec in self.attachments:
            name, path = _render_attachment(spec, context, conversion, self.randomize_html, style_seed)
            results[name] = path
        return results



def _render_attachment(
    spec: ManualAttachmentSpec,
    context: Dict[str, str],
    conversion: str,
    randomize: bool,
    seed: Optional[int],
) -> Tuple[str, str]:
    inline_payload = spec.inline_content
    suffix = spec.suffix()
    base_name = Path(spec.display_name).stem or 'attachment'

    text_payload: Optional[str] = None
    html_payload: Optional[str] = None

    if inline_payload is not None:
        rendered_text = render_tagged_content(inline_payload, context)
        html_payload = rendered_text
        text_payload = _html_to_text(rendered_text)
    else:
        source_path = Path(spec.path)
        if not source_path.exists():
            raise RuntimeError(f"Attachment not found: {source_path}")
        if suffix in _TEXT_EXTENSIONS:
            try:
                raw_text = source_path.read_text(encoding='utf-8', errors='ignore')
            except Exception as exc:  # pragma: no cover - defensive
                raise RuntimeError(f"Failed to read attachment {spec.display_name}: {exc}") from exc
            rendered_text = render_tagged_content(raw_text, context)
            if suffix in _HTML_EXTENSIONS:
                html_payload = rendered_text
                text_payload = _html_to_text(html_payload)
            else:
                text_payload = rendered_text
        elif conversion != 'original':
            raise RuntimeError(f"Attachment {spec.display_name} is not a text/HTML file; conversion to {conversion} is unsupported.")

    if html_payload is not None:
        html_payload = _finalize_html_payload(html_payload, enable_random=randomize, seed=seed)
        text_payload = _html_to_text(html_payload)

    conversion = (conversion or 'original').lower()
    if conversion == 'original':
        if html_payload is not None:
            extension = suffix or '.html'
            target = _ATTACHMENT_ROOT / f"{base_name}_{_random_suffix()}{extension}"
            target.write_text(html_payload, encoding='utf-8')
        elif text_payload is not None:
            extension = suffix or '.txt'
            target = _ATTACHMENT_ROOT / f"{base_name}_{_random_suffix()}{extension}"
            target.write_text(text_payload, encoding='utf-8')
        else:
            source_path = Path(spec.path)
            target = _ATTACHMENT_ROOT / f"{base_name}_{_random_suffix()}{suffix or source_path.suffix}"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target)
        return target.name, str(target)

    if not text_payload:
        raise RuntimeError(f"Attachment {spec.display_name} cannot be converted to {conversion} because no text content was detected.")

    if conversion == 'pdf':
        target = _ATTACHMENT_ROOT / f"{base_name}_{_random_suffix()}.pdf"
        if html_payload is not None:
            _html_to_pdf_rendered(html_payload, target)
        else:
            _text_to_pdf(text_payload, target)
        return target.name, str(target)
    if conversion == 'flat_pdf':
        temp_image = _ATTACHMENT_ROOT / f"{base_name}_{_random_suffix()}.png"
        if html_payload is not None:
            _html_to_image(html_payload, temp_image)
        else:
            _text_to_image(text_payload, temp_image)
        target = _ATTACHMENT_ROOT / f"{base_name}_{_random_suffix()}.pdf"
        try:
            _image_to_pdf(temp_image, target)
        finally:
            with contextlib.suppress(FileNotFoundError):
                temp_image.unlink()
        return target.name, str(target)
    if conversion in {'image', 'png', 'png_image'}:
        target = _ATTACHMENT_ROOT / f"{base_name}_{_random_suffix()}.png"
        if html_payload is not None:
            _html_to_image(html_payload, target)
        else:
            _text_to_image(text_payload, target)
        return target.name, str(target)
    if conversion == 'heif':
        target = _ATTACHMENT_ROOT / f"{base_name}_{_random_suffix()}.heif"
        if html_payload is not None:
            _html_to_image(html_payload, target, image_format='HEIF')
        else:
            _text_to_image(text_payload, target, image_format='HEIF')
        return target.name, str(target)
    if conversion in {'docx', 'doc'}:
        target = _ATTACHMENT_ROOT / f"{base_name}_{_random_suffix()}.docx"
        _text_to_docx(text_payload, target)
        return target.name, str(target)

    raise RuntimeError(f"Unknown manual attachment conversion: {conversion}")


def parse_extra_tags(rows: Optional[Sequence[Sequence[str]]]) -> Dict[str, str]:
    tags: Dict[str, str] = {}
    if not rows:
        return tags
    for row in rows:
        if not row:
            continue
        if len(row) == 1:
            key, value = row[0], ''
        else:
            key, value = row[0], row[1]
        key = (key or '').strip()
        if not key:
            continue
        tags[key] = (value or '').strip()
    return tags


def to_attachment_specs(files: Optional[Iterable[object]], inline_html: str = '', inline_name: str = '') -> List[ManualAttachmentSpec]:
    specs: List[ManualAttachmentSpec] = []
    for file_obj in files or []:
        path = getattr(file_obj, 'name', None) or str(file_obj)
        orig = getattr(file_obj, 'orig_name', None)
        specs.append(ManualAttachmentSpec(path=path, name=os.path.basename(path), orig_name=orig))

    inline_text = (inline_html or '').strip()
    if inline_text:
        name = (inline_name or '').strip() or 'inline.html'
        specs.insert(0, ManualAttachmentSpec(name=name, orig_name=name, inline_content=inline_text))
    return specs


def preview_attachment(spec: ManualAttachmentSpec) -> Tuple[str, str]:
    if spec.inline_content is not None:
        return 'html', spec.inline_content

    path = Path(spec.path)
    if not path.exists():
        raise RuntimeError(f"Attachment not found: {path}")
    suffix = spec.suffix()
    if suffix in _HTML_EXTENSIONS:
        return 'html', path.read_text(encoding='utf-8', errors='ignore')
    if suffix in _TEXT_EXTENSIONS:
        return 'text', path.read_text(encoding='utf-8', errors='ignore')
    return 'binary', f"Preview not supported for {spec.display_name}."

