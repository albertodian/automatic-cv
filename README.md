# automatic-cv  

Auto-CV is a Python tool that automatically generates a **customized CV** (and optionally a cover letter) tailored to any job posting.  
It pulls your personal information from a JSON file, extracts the job posting text from a URL, and uses a local **Ollama** LLM (like LLaMA 3) to rewrite and optimize your CV with the right keywords.  
Finally, it renders the result into a clean, ATS-friendly **PDF** using LaTeX templates.

---

## Features
- **Automatic job parsing** – paste the job posting URL and Auto-CV extracts the content.
- **LLM-based optimization** – selects the most relevant skills, experience, and rewrites your summary to include key terms.
- **LaTeX PDF generation** – fills a minimalistic template with your data for a professional output.
- **ATS-friendly** – simple structure, keyword-rich content.

---

## Project Structure

auto-cv/
│
├── src/ # main Python code
│ ├── auto_cv.py # CLI entry point
│ ├── data_loader.py # load profile JSON
│ ├── job_parser.py # fetch job text from URL
│ ├── llm_agent.py # call Ollama model
│ ├── renderer.py # fill template and compile PDF
│
├── data/
│ └── profile.json # your personal info
│
├── templates/
│ ├── cv_template.tex # LaTeX template for CV
│ └── cover_letter.tex # (optional) template for cover letter
│
├── output/ # generated PDFs
│
├── .gitignore
├── README.md
└── LICENSE

## Requirements
- Ollama installed and a model available locally (e.g. `llama3.2`). See Ollama docs. 
- `pdflatex` available (TeX Live / MacTeX).
- Python 3.9+

## Setup
```bash
git clone <repo>
cd auto-cv
pip install -r requirements.txt
```