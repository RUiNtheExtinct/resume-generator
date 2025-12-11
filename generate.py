#!/usr/bin/env python3
"""
Resume Generator - Async bulk PDF resume generation with cost tracking.
"""

import argparse
import asyncio
import json
import os
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from faker import Faker
from jinja2 import Environment, FileSystemLoader
from openai import AsyncOpenAI
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from weasyprint import HTML

from models.prompts import build_prompt

# Initialize
console = Console()
fake = Faker()

# Configuration
MODEL = "gpt-5-nano"
TEMPLATES = ["minimal.html", "modern.html", "classic.html", "corporate.html"]
OUTPUT_DIR = Path("output")
MAX_CONCURRENT = 15  # Concurrent API requests

# Pricing per 1M tokens for gpt-5-nano
PRICE_INPUT_PER_1M = 0.05   # $0.05 per 1M input tokens
PRICE_OUTPUT_PER_1M = 0.40  # $0.40 per 1M output tokens

# Load role mapping
with open("data/role_mapping.json") as f:
    ROLE_MAPPING = json.load(f)

INDUSTRIES = list(ROLE_MAPPING.keys())


@dataclass
class CostTracker:
    """Track token usage and costs."""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    resume_costs: list = field(default_factory=list)

    def add_usage(self, input_tokens: int, output_tokens: int) -> float:
        """Add token usage and return cost for this request."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        cost = (
            (input_tokens / 1_000_000) * PRICE_INPUT_PER_1M +
            (output_tokens / 1_000_000) * PRICE_OUTPUT_PER_1M
        )
        self.resume_costs.append(cost)
        return cost

    @property
    def total_cost(self) -> float:
        return sum(self.resume_costs)

    @property
    def avg_cost(self) -> float:
        return self.total_cost / len(self.resume_costs) if self.resume_costs else 0


def select_role(industry: str) -> str:
    """Select a role based on industry with weighted probabilities."""
    mapping = ROLE_MAPPING[industry]
    weights = mapping["weights"]

    # Choose between primary (index 0) and secondary (index 1) based on weights
    tier_index = random.choices(range(len(weights)), weights=weights)[0]

    if tier_index == 0:
        return random.choice(mapping["primary"])
    else:
        return random.choice(mapping["secondary"])


async def generate_resume_data(
    client: AsyncOpenAI,
    industry: str,
    role: str,
    seniority: int,
    cost_tracker: CostTracker
) -> tuple[dict, float]:
    """Generate structured resume data from LLM."""
    system_prompt, user_prompt = build_prompt(industry, role, seniority)

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )

    # Track tokens and cost
    usage = response.usage
    cost = cost_tracker.add_usage(usage.prompt_tokens, usage.completion_tokens)

    return json.loads(response.choices[0].message.content), cost


def render_pdf(resume_data: dict, index: int, template_name: str) -> Path:
    """Render resume data to PDF with ATS-friendly metadata."""
    # Add contact info from Faker
    name = fake.name()
    resume_data["name"] = name
    resume_data["email"] = fake.email()
    resume_data["phone"] = fake.phone_number()
    resume_data["location"] = f"{fake.city()}, {fake.state_abbr()}"

    # Render template
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template(template_name)
    html_out = template.render(**resume_data)

    # Write PDF with metadata for ATS parsing
    pdf_path = OUTPUT_DIR / f"resume_{index:04d}.pdf"

    # PDF metadata helps ATS systems identify document type and content
    metadata = {
        "title": f"Resume - {name}",
        "author": name,
        "subject": "Professional Resume",
        "keywords": ", ".join(resume_data.get("skills", [])[:10]),
        "creator": "Resume Generator",
    }

    HTML(string=html_out).write_pdf(
        str(pdf_path),
        metadata=metadata
    )

    return pdf_path


async def generate_single_resume(
    client: AsyncOpenAI,
    index: int,
    semaphore: asyncio.Semaphore,
    cost_tracker: CostTracker,
    progress: Progress,
    task_id: int
) -> tuple[int, float]:
    """Generate a single resume with semaphore for rate limiting."""
    async with semaphore:
        # Select industry and correlated role
        industry = random.choice(INDUSTRIES)
        role = select_role(industry)
        seniority = random.randint(1, 18)
        template_name = random.choice(TEMPLATES)

        # Generate resume data
        resume_data, cost = await generate_resume_data(
            client, industry, role, seniority, cost_tracker
        )

        # Render PDF (sync operation, but fast)
        render_pdf(resume_data, index, template_name)

        progress.advance(task_id)
        return index, cost


def create_summary_table(
    total: int,
    elapsed: float,
    cost_tracker: CostTracker
) -> Table:
    """Create a summary table for the generation results."""
    table = Table(title="Generation Summary", show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Resumes Generated", str(total))
    table.add_row("Total Time", f"{elapsed:.1f}s")
    table.add_row("Speed", f"{total / elapsed:.1f} resumes/sec")
    table.add_row("", "")
    table.add_row("Input Tokens", f"{cost_tracker.total_input_tokens:,}")
    table.add_row("Output Tokens", f"{cost_tracker.total_output_tokens:,}")
    table.add_row("", "")
    table.add_row("Avg Cost/Resume", f"${cost_tracker.avg_cost:.6f}")
    table.add_row("Total Cost", f"${cost_tracker.total_cost:.4f}")

    return table


async def main_async(total: int, save_costs: bool, concurrency: int = MAX_CONCURRENT):
    """Main async generation loop."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    cost_tracker = CostTracker()
    semaphore = asyncio.Semaphore(concurrency)

    # Rich progress display
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console
    )

    start_time = time.time()

    with progress:
        task_id = progress.add_task("Generating resumes", total=total)

        # Create all tasks
        tasks = [
            generate_single_resume(
                client, i, semaphore, cost_tracker, progress, task_id
            )
            for i in range(1, total + 1)
        ]

        # Run all tasks concurrently
        await asyncio.gather(*tasks)

    elapsed = time.time() - start_time

    # Display summary
    console.print()
    console.print(create_summary_table(total, elapsed, cost_tracker))
    console.print()
    console.print(f"[green]PDFs saved to:[/green] {OUTPUT_DIR.absolute()}/")

    # Optionally save cost log
    if save_costs:
        cost_log = {
            "total_resumes": total,
            "total_time_seconds": elapsed,
            "total_input_tokens": cost_tracker.total_input_tokens,
            "total_output_tokens": cost_tracker.total_output_tokens,
            "total_cost_usd": cost_tracker.total_cost,
            "avg_cost_per_resume_usd": cost_tracker.avg_cost,
            "per_resume_costs_usd": cost_tracker.resume_costs
        }
        cost_file = OUTPUT_DIR / "cost_log.json"
        with open(cost_file, "w") as f:
            json.dump(cost_log, f, indent=2)
        console.print(f"[dim]Cost log saved to: {cost_file}[/dim]")


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic PDF resumes for ATS testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate.py                  # Generate 800 resumes (default)
  python generate.py -n 100           # Generate 100 resumes
  python generate.py -n 50 --save-costs  # Generate 50 and save cost log
        """
    )
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=800,
        help="Number of resumes to generate (default: 800)"
    )
    parser.add_argument(
        "--save-costs",
        action="store_true",
        help="Save detailed cost log to output/cost_log.json"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=MAX_CONCURRENT,
        help=f"Max concurrent API requests (default: {MAX_CONCURRENT})"
    )

    args = parser.parse_args()

    # Use concurrency from args
    concurrency = args.concurrency

    # Header
    console.print(Panel.fit(
        f"[bold]Resume Generator[/bold]\n"
        f"Model: {MODEL} | Concurrency: {concurrency} | Target: {args.count} resumes",
        border_style="blue"
    ))
    console.print()

    # Run async main
    asyncio.run(main_async(args.count, args.save_costs, concurrency))


if __name__ == "__main__":
    main()
