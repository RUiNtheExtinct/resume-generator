# Resume Generator

Generate 500-1000+ synthetic, high-quality PDF resumes for ATS testing.

A fully automated async pipeline that produces realistic, fictional PDF resumes for testing ATS systems, resume parsers, NLP models, and document extraction pipelines.

---

## Features

- **Async bulk generation** - 5-10x faster with concurrent API calls
- **Cost tracking** - Per-resume and total cost displayed in real-time
- **26 industries** with IT/tech focus - Software, Cloud, AI/ML, Cybersecurity, DevOps, Fintech, and more
- **Industry-role correlation** - Realistic role matching per industry
- **Seniority-aware content** - Junior/Mid/Senior resume patterns
- **4 professional templates** - Modern, Minimal, Classic, Corporate
- **JSON structured output** - Token-efficient LLM responses
- **Rich CLI** - Progress bars, stats, and summaries

---

## Project Structure

```
resume-generator/
├── generate.py              # Main async generation script
├── models/
│   └── prompts.py           # LLM prompts with JSON schema
├── templates/               # HTML templates (Jinja2)
│   ├── minimal.html
│   ├── modern.html
│   ├── classic.html
│   └── corporate.html
├── data/
│   └── role_mapping.json    # Industry-role correlations
├── output/                  # Generated PDFs
└── requirements.txt
```

---

## Installation

### 1. Install Python dependencies

```sh
pip install -r requirements.txt
```

**Note:** Ensure these packages are in requirements.txt:
```
faker
jinja2
openai
tqdm
weasyprint
rich
```

### 2. Install system packages for WeasyPrint

**Ubuntu/Debian:**
```sh
sudo apt install libpango-1.0-0 libcairo2 libffi-dev gdk-pixbuf2.0-0
```

**macOS (Homebrew):**
```sh
brew install cairo pango gdk-pixbuf libffi
```

---

## Environment Variables

```sh
export OPENAI_API_KEY="your-key-here"
```

---

## Usage

### Basic Usage

```sh
python generate.py                    # Generate 800 resumes (default)
python generate.py -n 100             # Generate 100 resumes
python generate.py -n 50 --save-costs # Generate 50 + save cost log
```

### CLI Options

| Option | Description |
|--------|-------------|
| `-n, --count` | Number of resumes to generate (default: 800) |
| `--save-costs` | Save detailed cost log to `output/cost_log.json` |
| `--concurrency` | Max concurrent API requests (default: 15) |

### Example Output

```
╭─────────────────────────────────────────────────────────╮
│ Resume Generator                                        │
│ Model: gpt-5-nano | Concurrency: 15 | Target: 100       │
╰─────────────────────────────────────────────────────────╯

⠋ Generating resumes ━━━━━━━━━━━━━━━━━━━━ 100% 100/100 0:01:23 0:00:00

        Generation Summary
Resumes Generated    100
Total Time           83.2s
Speed                1.2 resumes/sec

Input Tokens         45,230
Output Tokens        52,100

Avg Cost/Resume      $0.000234
Total Cost           $0.0234

PDFs saved to: /path/to/output/
```

---

## How It Works

1. **Industry Selection** - Random industry from 26 options (IT-focused)
2. **Role Correlation** - Weighted role selection per industry
3. **Seniority Tier** - Junior (1-4yr), Mid (5-10yr), Senior (11-18yr)
4. **LLM Generation** - JSON structured resume via gpt-5-nano
5. **Contact Info** - Faker generates name, email, phone, location
6. **Template Rendering** - Jinja2 HTML with structured data
7. **PDF Output** - WeasyPrint renders HTML to PDF

---

## Industries (26)

**IT/Tech Focus:**
- Software Engineering, DevOps & SRE, Cloud Computing
- Data Science & AI, Data Engineering, Cybersecurity
- IT Support & Operations, Game Development, QA & Testing
- Product Management, UI/UX Design

**Specialized Tech:**
- Fintech, EdTech, HealthTech

**Traditional:**
- Finance, Accounting, Healthcare, Marketing, Sales
- HR & Recruiting, Manufacturing, Construction
- Retail, Logistics, Energy, Banking

---

## Customization

### Add New Templates

Add `.html` files in `templates/` using Jinja2 syntax:

```html
<h1>{{ name }}</h1>
<p>{{ summary }}</p>
{% for job in experience %}
  <div>{{ job.title }} at {{ job.company }}</div>
{% endfor %}
```

Update `TEMPLATES` list in `generate.py`.

### Modify Industry-Role Mapping

Edit `data/role_mapping.json`:

```json
{
  "New Industry": {
    "primary": ["Role 1", "Role 2"],
    "secondary": ["Senior Role 1"],
    "weights": [0.7, 0.3]
  }
}
```

### Adjust Pricing

Update pricing constants in `generate.py`:

```python
PRICE_INPUT_PER_1M = 0.10   # $/1M input tokens
PRICE_OUTPUT_PER_1M = 0.40  # $/1M output tokens
```

---

## Performance

| Metric | Sequential | Async (15 concurrent) |
|--------|------------|----------------------|
| 100 resumes | ~10 min | ~1.5 min |
| 800 resumes | ~80 min | ~12 min |

---

## Cost Log Format

When using `--save-costs`, creates `output/cost_log.json`:

```json
{
  "total_resumes": 100,
  "total_time_seconds": 83.2,
  "total_input_tokens": 45230,
  "total_output_tokens": 52100,
  "total_cost_usd": 0.0234,
  "avg_cost_per_resume_usd": 0.000234,
  "per_resume_costs_usd": [0.00023, 0.00024, ...]
}
```

---

## Troubleshooting

### WeasyPrint fails to load fonts/libraries
Install required system packages (see Installation).

### Rate limiting errors
Reduce concurrency: `python generate.py --concurrency 5`

### JSON parsing errors
The LLM occasionally returns malformed JSON. Errors are logged and that resume is skipped.

---

## License

All resumes produced are synthetic and generated purely for testing and development.
Free to use in organizational or research environments.
