from jinja2 import Template
from io import BytesIO
from weasyprint import HTML
import subprocess
import os


def render_cv_pdf_html(profile, template, output_path="output/cv_output.pdf", output_filename=None):
    """
    Render CV to PDF using HTML template
    
    Args:
        profile: Profile data dictionary
        template: Template name ('tech', 'business', or 'modern')
        output_path: Output PDF file path (default: output/cv_output.pdf)
        output_filename: Optional filename to use (overrides output_path)
    """
    
    # If output_filename provided, use it
    if output_filename:
        output_path = os.path.join("output", output_filename)
    
    if template == "tech":
        template_path = "templates/cv_template_tech.html"
    elif template == "business":
        template_path = "templates/cv_template_business.html"
    elif template == "modern":
        template_path = "templates/cv_template_modern.html"
    else:
        raise ValueError("Invalid template type. Choose 'tech', 'business', or 'modern'.")

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    jinja_template = Template(template_content)
    rendered_html = jinja_template.render(**profile)

    # Write HTML for debugging
    # html_file = output_path.replace(".pdf", ".html")
    # with open(html_file, "w", encoding="utf-8") as f:
    #     f.write(rendered_html)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    # Convert to PDF
    HTML(string=rendered_html).write_pdf(output_path)
    print(f"CV generated: {output_path}")



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
