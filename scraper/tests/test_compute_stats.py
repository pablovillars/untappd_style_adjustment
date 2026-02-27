import pytest
import statistics
from compute_stats import compute_style_stats, compute_global_stats, build_output

RAW = {
    'American Adjunct Lager': [3.0, 3.2, 3.4, 3.6, 3.8],
    'Imperial Stout':         [3.8, 4.0, 4.2, 4.4, 4.6],
}


def test_compute_style_stats_returns_mean_std_sample():
    stats = compute_style_stats(RAW['American Adjunct Lager'])
    assert stats['mean'] == pytest.approx(3.4, abs=0.01)
    assert stats['std']  == pytest.approx(0.3162, abs=0.01)  # sample stdev (N-1)
    assert stats['sample'] == 5


def test_compute_global_stats_uses_all_scores():
    stats = compute_global_stats(RAW)
    all_scores = [3.0, 3.2, 3.4, 3.6, 3.8, 3.8, 4.0, 4.2, 4.4, 4.6]
    assert stats['mean'] == pytest.approx(statistics.mean(all_scores), abs=0.01)
    assert stats['std']  == pytest.approx(statistics.stdev(all_scores), abs=0.01)


def test_build_output_structure():
    output = build_output(RAW, updated_at='2026-02-27')
    assert output['updated_at'] == '2026-02-27'
    assert 'global' in output
    assert 'styles' in output
    assert 'American Adjunct Lager' in output['styles']
    assert output['styles']['American Adjunct Lager']['sample'] == 5


def test_build_output_global_has_mean_and_std():
    output = build_output(RAW)
    assert 'mean' in output['global']
    assert 'std' in output['global']


def test_style_stats_rounded_to_4dp():
    stats = compute_style_stats([3.123456789, 3.987654321])
    assert len(str(stats['mean']).split('.')[-1]) <= 4
    assert len(str(stats['std']).split('.')[-1]) <= 4
