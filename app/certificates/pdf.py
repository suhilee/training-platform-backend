from io import BytesIO
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.certificates.schemas import CertificateDataResponse

TEMPLATE_DIR = Path(__file__).parent / "templates"

environment = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
)


def generate_certificate_pdf(
    certificate_data: CertificateDataResponse,
) -> bytes:
    template = environment.get_template("certificate.html")

    rendered_html = template.render(
        participant_first_name=certificate_data.participant_first_name,
        participant_last_name=certificate_data.participant_last_name,
        session_title=certificate_data.session_title,
        session_date=certificate_data.session_date.isoformat(),
        issued_at=certificate_data.issued_at.date().isoformat(),
    )

    pdf_file = BytesIO()

    HTML(string=rendered_html).write_pdf(pdf_file)

    return pdf_file.getvalue()