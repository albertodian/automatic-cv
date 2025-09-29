from jinja2 import Template
import subprocess
import os

def render_cv_pdf(profile: dict, 
                  template_path: str = "templates/cv_template.tex", 
                  output_pdf: str = "output/cv_output.pdf"):
    """
    Render the CV LaTeX template with the optimized profile and compile to PDF.
    """
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    template = Template(template_content)
    rendered_tex = template.render(
        **profile.get("personal_info", {}),
        summary=profile.get("summary", ""),
        skills=profile.get("skills", []),
        experience=profile.get("experience", []),
        education=profile.get("education", [])
    )

    tex_file = os.path.splitext(output_pdf)[0] + ".tex"
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(rendered_tex)

    # compile PDF
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
