from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
import os

def generer_pdf(template_name, context):

    html_string = render_to_string(template_name, context)
    html = HTML(string=html_string)

    with tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.pdf',
            dir='/tmp'
    ) as f:
        html.write_pdf(f.name)
        return f.name