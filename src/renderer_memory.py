"""In-memory PDF renderer - no disk storage needed."""

from jinja2 import Template
from weasyprint import HTML
from io import BytesIO
import os


def render_cv_pdf_memory(profile: dict, template: str = "tech") -> BytesIO:
    """Generate PDF in memory, return BytesIO buffer ready to stream."""
    
    # Select template
    template_map = {
        "tech": "templates/cv_template_tech.html",
        "business": "templates/cv_template_business.html",
        "modern": "templates/cv_template_modern.html"
    }
    
    template_path = template_map.get(template)
    if not template_path:
        raise ValueError(f"Invalid template: {template}")
    
    # Load and render HTML
    with open(template_path, "r", encoding="utf-8") as f:
        jinja_template = Template(f.read())
    
    rendered_html = jinja_template.render(**profile)
    
    # Generate PDF to memory
    pdf_buffer = BytesIO()
    HTML(string=rendered_html).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    
    return pdf_buffer
