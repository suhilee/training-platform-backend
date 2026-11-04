from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.certificates.pdf import generate_certificate_pdf
from app.certificates.schemas import CertificateDataResponse

certificate_data = CertificateDataResponse(
    registration_id=uuid4(),
    certificate_id=uuid4(),
    participant_first_name="Abdel-Moumene",
    participant_last_name="KHALDI",
    session_title="Introduction to Python: Theory and Practice",
    session_date=date(2026, 10, 17),
    issued_at=datetime(2026, 10, 26, 12, 0, tzinfo=timezone.utc),
)

pdf_bytes = generate_certificate_pdf(certificate_data)

output_path = Path("sample_certificate.pdf")
output_path.write_bytes(pdf_bytes)

print(f"PDF saved to: {output_path.resolve()}")