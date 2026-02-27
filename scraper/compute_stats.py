"""
scraper/compute_stats.py
Reads raw-scores.json, computes per-style mean/std, writes style-averages.json.
Run: python compute_stats.py
"""
import json
import statistics
from datetime import date
from pathlib import Path


def compute_style_stats(scores: list[float]) -> dict:
    return {
        'mean':   round(statistics.mean(scores), 4),
        'std':    round(statistics.stdev(scores), 4),
        'sample': len(scores),
    }


def compute_global_stats(raw: dict[str, list[float]]) -> dict:
    all_scores = [s for scores in raw.values() for s in scores]
    return {
        'mean': round(statistics.mean(all_scores), 4),
        'std':  round(statistics.stdev(all_scores), 4),
    }


def build_output(raw: dict[str, list[float]], updated_at: str = None) -> dict:
    return {
        'updated_at': updated_at or str(date.today()),
        'global':     compute_global_stats(raw),
        'styles':     {style: compute_style_stats(scores)
                       for style, scores in raw.items()},
    }


if __name__ == '__main__':
    raw_path = Path(__file__).parent.parent / 'data' / 'raw-scores.json'
    out_path = Path(__file__).parent.parent / 'data' / 'style-averages.json'

    with open(raw_path) as f:
        raw = json.load(f)

    output = build_output(raw)

    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Done. {len(output['styles'])} styles written to {out_path}")
    print(f"Global mean: {output['global']['mean']}, std: {output['global']['std']}")
