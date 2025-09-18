from pathlib import Path
from setuptools import setup

ROOT = Path(__file__).parent


def parse_requirements():
    """Parse install requirements from requirements.txt if it is present."""
    req_file = ROOT / 'requirements.txt'
    if req_file.exists():
        lines = req_file.read_text(encoding='utf-8').splitlines()
        return [line.strip() for line in lines if line.strip() and not line.lstrip().startswith('#')]
    return [
        'gradio>=3.0.0',
        'reportlab>=3.6.0',
        'pymupdf>=1.20.0',
        'faker>=15.0.0',
        'google-auth>=2.0.0',
        'requests>=2.25.0',
        'Pillow>=8.0.0',
        'pillow-heif>=0.9.0',
    ]


def read_readme():
    """Return the README contents for PyPI."""
    readme = ROOT / 'README.md'
    return readme.read_text(encoding='utf-8') if readme.exists() else (
        "Token-based Gmail REST mailer with Gradio UI and invoice generation."
    )


setup(
    name='simple-gmail-rest-mailer',
    version='1.1.0',
    author='Vikram Nair',
    author_email='vikramnairoffice@gmail.com',
    description='Token-based Gmail REST mailer with personalized invoices and Colab support.',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/vikramnairoffice/simple-gmail-rest-mailer',
    py_modules=[
        'ui',
        'mailer',
        'invoice',
        'content',
        'ui_token_helpers',
        'colab_setup',
        'colab_form_cell',
    ],
    install_requires=parse_requirements(),
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'pytest-cov>=2.10.0',
            'black>=21.0.0',
            'flake8>=3.8.0',
        ],
        'colab': [
            'ipython>=7.0.0',
            'jupyter>=1.0.0',
            'google-auth-oauthlib>=0.8.0',
            'google-api-python-client>=2.70.0',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Communications :: Email',
        'Topic :: Office/Business :: Financial :: Accounting',
    ],
    python_requires='>=3.7',
    include_package_data=True,
    package_data={'': ['*.md', '*.txt', '*.json']},
    entry_points={'console_scripts': ['simple-mailer=ui:main']},
    project_urls={
        'Bug Reports': 'https://github.com/vikramnairoffice/simple-gmail-rest-mailer/issues',
        'Source': 'https://github.com/vikramnairoffice/simple-gmail-rest-mailer',
        'Documentation': 'https://github.com/vikramnairoffice/simple-gmail-rest-mailer/blob/main/README.md',
    },
)
