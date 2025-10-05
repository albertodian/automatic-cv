from jinja2 import Template
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

def render_cv_pdf_latex(profile: dict,
                  template: str,
                  output_pdf: str = "output/cv_output.pdf"):
    
    
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    template = Template(template_content)

    rendered_tex = template.render(
        personal_info=profile.get("personal_info", {}),
        summary=profile.get("summary", ""),
        experience=profile.get("experience", []),
        education=profile.get("education", []),
        projects=profile.get("projects", []),
        skills=profile.get("skills", [])  
    )

    tex_file = os.path.splitext(output_pdf)[0] + ".tex"
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(rendered_tex)

    subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_file], check=True)
    print(f"CV generated: {output_pdf}")


def render_cover_letter_pdf(cover_letter_text: str, profile: dict, job_data: dict,
                            template_path: str = "templates/cover_letter_template.tex",
                            output_pdf: str = "output/cover_letter.pdf"):
    from jinja2 import Template
    import os
    import subprocess

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    template = Template(template_content)
    rendered_tex = template.render(
        cover_letter=cover_letter_text,
        name=profile.get("personal_info", {}).get("name", ""),
        date="",
        company_name=job_data.get("title", "Hiring Team"),
        company_address=""
    )

    tex_file = os.path.splitext(output_pdf)[0] + ".tex"
    os.makedirs(os.path.dirname(tex_file) or ".", exist_ok=True)
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(rendered_tex)

    subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_file], check=True)
    print(f"Cover letter generated: {output_pdf}")
