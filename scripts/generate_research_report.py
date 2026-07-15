#!/usr/bin/env python3
"""Generate the static day-0-to-current research report after robust analysis."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import statistics


CAPABILITIES = ("attribute", "counting", "object", "ocr", "spatial")
ROBUST_ROOT = Path("results/robust-route-search-qwen25-vl-3b")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def pp(value: float) -> str:
    return f"{value:+.2f} pp"


def esc(value: object) -> str:
    return html.escape(str(value))


def table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{esc(cell)}</th>" for cell in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    return f"<div class=\"table-wrap\"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def metric_card(label: str, value: str, note: str) -> str:
    return (
        "<article class=\"metric\">"
        f"<p>{esc(label)}</p><strong>{esc(value)}</strong><span>{esc(note)}</span>"
        "</article>"
    )


def external_table(external: dict) -> str:
    rows = []
    for name in ("full", "generic-k8", "task-k8", "task-k4"):
        condition = external["conditions"][name]
        overall = condition["overall"]
        rows.append([
            esc(name),
            pct(overall["candidate_accuracy"]),
            pp(overall["accuracy_drop_pp"]),
            *[pp(condition["capabilities"][capability]["accuracy_drop_pp"]) for capability in CAPABILITIES],
        ])
    return table(["Condition", "Accuracy", "Full-model drop", *CAPABILITIES], rows)


def robust_summary(robust: dict) -> tuple[str, str, str]:
    full = robust["full"]["overall"]["accuracy"]
    summary_rows = []
    capability_sections = []
    interpretations = []
    for raw_k in ("4", "6", "8"):
        result = robust["budgets"][raw_k]
        conditions = result["conditions"]
        random_values = [conditions[f"random-{index}"]["overall"]["accuracy"] for index in range(3)]
        comparison = result["comparisons"]["evolved_task_minus_evolved_generic"]["overall"]
        summary_rows.append([
            f"K{raw_k}",
            pct(full),
            pct(conditions["evolved-generic"]["overall"]["accuracy"]),
            pct(conditions["evolved-task"]["overall"]["accuracy"]),
            pp(comparison["mean_pp"]),
            f"[{comparison['ci95_low_pp']:.2f}, {comparison['ci95_high_pp']:.2f}] pp",
            pct(conditions["generic-independent"]["overall"]["accuracy"]),
            pct(conditions["task-independent"]["overall"]["accuracy"]),
            pct(conditions["contiguous"]["overall"]["accuracy"]),
            pct(statistics.fmean(random_values)),
        ])
        capability_rows = []
        for capability in CAPABILITIES:
            task = conditions["evolved-task"]["capabilities"][capability]["accuracy"]
            generic = conditions["evolved-generic"]["capabilities"][capability]["accuracy"]
            advantage = result["comparisons"]["evolved_task_minus_evolved_generic"]["capabilities"][capability]
            capability_rows.append([
                capability,
                pct(task),
                pct(generic),
                pp(advantage["mean_pp"]),
                f"[{advantage['ci95_low_pp']:.2f}, {advantage['ci95_high_pp']:.2f}] pp",
            ])
        capability_sections.append(
            f"<h3>K{raw_k}: capability comparison</h3>" +
            table(["Capability", "Evolved task", "Evolved generic", "Task minus generic", "Paired 95% interval"], capability_rows)
        )
        if comparison["ci95_low_pp"] > 0:
            interpretations.append(f"K{raw_k} has a positive overall task-policy advantage on this method-selection split.")
        elif comparison["ci95_high_pp"] < 0:
            interpretations.append(f"K{raw_k} favors the generic route on this method-selection split.")
        else:
            interpretations.append(f"K{raw_k} has no clear overall advantage between evolved task and generic routes.")
    return (
        table(
            ["Budget", "Full", "Evolved generic", "Evolved task policy", "Task minus generic", "Paired 95% interval", "Generic independent", "Task independent", "Contiguous", "Random mean"],
            summary_rows,
        ),
        "".join(capability_sections),
        " ".join(interpretations),
    )


def render() -> str:
    baseline = load(Path("results/baseline-qwen25-vl-3b/summary.json"))
    ablation = load(Path("results/ablation-qwen25-vl-3b/analysis.json"))
    locked_latency = load(Path("results/task-route-latency-locked-qwen25-vl-3b/summary.json"))
    external = load(Path("results/external-frozen-qwen25-vl-3b/analysis.json"))
    phase2 = load(Path("results/phase2-feature-gap-qwen25-vl-3b/analysis/analysis.json"))
    phase3 = load(Path("results/phase3-interaction-search-qwen25-vl-3b/validation_summary.json"))
    robust = load(ROBUST_ROOT / "analysis" / "analysis.json")

    baseline_overall = baseline["overall"]
    safe_block = ablation["screening_candidates"][0]
    slow_block = max(ablation["blocks"], key=lambda item: item["overall"]["accuracy_drop"])
    external_k8 = external["task_vs_generic"]["task-k8"]["overall"]
    robust_table, robust_capabilities, robust_interpretation = robust_summary(robust)

    feature_rows = []
    for name, values in phase2["feature_validation"].items():
        feature_rows.append([
            name,
            f"{values['identity_relative_l2_mean']:.4f}",
            f"{values['ranks']['8']['relative_l2_mean']:.4f}",
            f"{values['ranks']['32']['relative_l2_mean']:.4f}",
        ])
    phase3_rows = []
    for capability in CAPABILITIES:
        route = phase3["beam_routes"][capability][0]
        validation = route["validation_metrics"]
        phase3_rows.append([
            capability,
            esc(route["blocks"]),
            pp(route["search_metrics"]["accuracy_drop_pp"]),
            pp(validation["capabilities"][capability]["accuracy_drop_pp"]),
            pp(validation["macro_drop_pp"]),
        ])

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>VLM Bench | Vision Encoder Pruning Research Log</title>
  <style>
    :root {{ --ink:#17302c; --paper:#f4efe4; --cream:#fbf8ef; --acid:#d7e36e; --orange:#ec6b3e; --mist:#b7c8c1; --line:#c6c4b7; --muted:#5c6a64; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:radial-gradient(circle at 82% 0,#dfe8be 0,transparent 27rem),linear-gradient(135deg,#f8f2e7,#eee9dc); color:var(--ink); font-family:Arial Narrow,Avenir Next Condensed,Helvetica Neue,sans-serif; line-height:1.45; }}
    .shell {{ width:min(1180px,calc(100% - 32px)); margin:auto; }}
    header {{ padding:34px 0 72px; border-bottom:2px solid var(--ink); }} .eyebrow {{ display:flex; justify-content:space-between; font:700 .72rem/1 ui-monospace,SFMono-Regular,monospace; letter-spacing:.09em; text-transform:uppercase; }}
    h1,h2,h3 {{ font-family:Iowan Old Style,Palatino Linotype,Book Antiqua,serif; line-height:.98; margin:0; letter-spacing:-.045em; }} h1 {{ max-width:900px; font-size:clamp(3.4rem,9vw,8.2rem); margin-top:26px; }} h2 {{ font-size:clamp(2.3rem,4vw,4.2rem); margin-bottom:18px; }} h3 {{ font-size:1.8rem; margin:36px 0 14px; }}
    .lede {{ max-width:800px; font-size:1.25rem; margin:28px 0 0; color:var(--muted); }} .stamp {{ display:inline-block; padding:5px 9px; background:var(--acid); border:1px solid var(--ink); transform:rotate(-2deg); }}
    nav {{ position:sticky; top:0; z-index:5; background:rgba(244,239,228,.94); border-bottom:1px solid var(--line); backdrop-filter:blur(10px); }} nav .shell {{ display:flex; gap:17px; overflow:auto; padding:11px 0; }} nav a {{ color:var(--ink); text-decoration:none; font:700 .72rem/1 ui-monospace,SFMono-Regular,monospace; text-transform:uppercase; white-space:nowrap; }}
    section {{ padding:74px 0; border-bottom:1px solid var(--line); }} .section-label {{ color:var(--orange); font:700 .78rem/1 ui-monospace,SFMono-Regular,monospace; letter-spacing:.1em; text-transform:uppercase; margin-bottom:18px; }}
    .metrics {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:28px; }} .metric {{ background:var(--cream); border:1px solid var(--ink); padding:17px; min-height:145px; box-shadow:4px 4px 0 var(--ink); }} .metric p,.metric span {{ display:block; margin:0; font-size:.76rem; text-transform:uppercase; letter-spacing:.06em; }} .metric strong {{ display:block; font:700 clamp(1.9rem,3vw,3.1rem)/1 Iowan Old Style,Palatino Linotype,serif; margin:22px 0 8px; }}
    .split {{ display:grid; grid-template-columns:1.15fr .85fr; gap:34px; align-items:start; }} .callout {{ background:var(--ink); color:var(--paper); padding:28px; border-radius:3px; }} .callout strong {{ color:var(--acid); font:700 1.6rem/1.1 Iowan Old Style,Palatino Linotype,serif; display:block; margin-bottom:10px; }}
    .timeline {{ display:grid; grid-template-columns:repeat(5,1fr); gap:0; border:1px solid var(--ink); margin-top:32px; }} .event {{ min-height:205px; padding:18px; border-right:1px solid var(--ink); background:var(--cream); }} .event:last-child {{ border-right:0; }} .event b {{ display:block; color:var(--orange); font:.72rem/1 ui-monospace,SFMono-Regular,monospace; text-transform:uppercase; margin-bottom:23px; }}
    .table-wrap {{ overflow-x:auto; border:1px solid var(--ink); background:var(--cream); }} table {{ width:100%; border-collapse:collapse; font-size:.9rem; }} th {{ text-align:left; background:var(--ink); color:var(--paper); padding:10px 12px; white-space:nowrap; font:700 .68rem/1.15 ui-monospace,SFMono-Regular,monospace; text-transform:uppercase; letter-spacing:.035em; }} td {{ padding:10px 12px; border-bottom:1px solid var(--line); white-space:nowrap; }} tr:last-child td {{ border:0; }}
    .figure-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-top:28px; }} figure {{ margin:0; border:1px solid var(--ink); padding:12px; background:var(--cream); }} figure img {{ display:block; width:100%; background:#fff; }} figcaption {{ margin-top:9px; font-size:.82rem; color:var(--muted); }}
    .ledger {{ display:grid; grid-template-columns:repeat(3,1fr); gap:1px; border:1px solid var(--ink); background:var(--ink); }} .ledger article {{ padding:21px; background:var(--cream); }} .ledger h3 {{ font-size:1.35rem; margin:0 0 10px; }} .ledger .bad {{ color:#9d2d1d; }} .ledger .good {{ color:#2f5a40; }}
    .note {{ font-size:.93rem; color:var(--muted); max-width:880px; }} a {{ color:#9d3b21; }} footer {{ padding:55px 0; font-size:.85rem; color:var(--muted); }}
    @media(max-width:760px) {{ header {{ padding-bottom:45px; }} .metrics,.ledger {{ grid-template-columns:1fr 1fr; }} .split,.figure-grid {{ grid-template-columns:1fr; }} .timeline {{ grid-template-columns:1fr; }} .event {{ min-height:auto; border-right:0; border-bottom:1px solid var(--ink); }} .event:last-child {{ border-bottom:0; }} section {{ padding:52px 0; }} }}
  </style>
</head>
<body>
  <header><div class=\"shell\"><div class=\"eyebrow\"><span>VLM Bench / Research Log</span><span class=\"stamp\">Qwen2.5-VL-3B</span></div><h1>Can a VLM skip vision blocks without losing the image?</h1><p class=\"lede\">A complete research record from first baseline through source-aware route search. It includes the wins, the negative results, the consumed external evaluation, and the live final matched-K comparison.</p></div></header>
  <nav><div class=\"shell\"><a href=\"#question\">Question</a><a href=\"#baseline\">Baseline</a><a href=\"#ablation\">Ablations</a><a href=\"#failures\">Failures</a><a href=\"#external\">External test</a><a href=\"#robust\">Final search</a><a href=\"#research\">Research context</a></div></nav>
  <main>
    <section id=\"question\"><div class=\"shell\"><p class=\"section-label\">Research question</p><div class=\"split\"><div><h2>Not “which block stores OCR?”</h2><p>The causal claim is deliberately narrower: when the image encoder bypasses a whole transformer block, which visual capabilities lose accuracy, and can a route chosen for one capability beat a generic route at the same number of removed blocks?</p><p>The project separates screening evidence, method-selection evidence, and sealed external evidence. A block sensitivity map alone is never treated as proof that a capability lives in one block.</p></div><aside class=\"callout\"><strong>Evidence rule</strong>Every reported route is paired against the full model on identical examples. The original external set is consumed and excluded from all later selection.</aside></div><div class=\"timeline\"><article class=\"event\"><b>Day 0</b><strong>Protocol and data</strong><p>Five visual capabilities, controlled plus natural sources, deterministic scoring.</p></article><article class=\"event\"><b>Day 1</b><strong>Single blocks</strong><p>All 32 vision-block identity interventions and a capability heatmap.</p></article><article class=\"event\"><b>Day 2</b><strong>Combined routes</strong><p>K4/K8/K12/K16 controls, locked-clock latency, and activation rescue.</p></article><article class=\"event\"><b>Day 3</b><strong>Repair and search</strong><p>Low-rank feature repair and interaction-aware K8 selection.</p></article><article class=\"event\"><b>Current</b><strong>Robust route search</strong><p>Source-balanced K4/K6/K8 generic and capability routes with matched controls.</p></article></div></div></section>
    <section id=\"baseline\"><div class=\"shell\"><p class=\"section-label\">Starting point</p><h2>One model, one stable baseline</h2><div class=\"metrics\">{metric_card('Baseline accuracy', pct(baseline_overall['accuracy']), f"{baseline_overall['examples']:,} discovery examples")}{metric_card('Vision latency', f"{baseline_overall['latency_ms']['vision_encoder']['median']:.1f} ms", 'median, batch size one')}{metric_card('End-to-end latency', f"{baseline_overall['latency_ms']['total']['median']:.1f} ms", 'median, greedy decoding')}{metric_card('Peak VRAM', f"{baseline_overall['peak_reserved_mib']:,.0f} MiB", 'dynamic resolution pinned')}</div><p class=\"note\">Model: Qwen/Qwen2.5-VL-3B-Instruct. Vision tower: 32 blocks, approximately 668.7M parameters; full model: approximately 3.755B parameters.</p></div></section>
    <section id=\"ablation\"><div class=\"shell\"><p class=\"section-label\">Day 1: causal screen</p><h2>Some blocks are catastrophic. “Safe” blocks do not compose.</h2><div class=\"split\"><div><p>Block {slow_block['block']} caused the largest overall isolated drop: <b>{pp(100 * slow_block['overall']['accuracy_drop'])}</b>. The conservative screen found only block {safe_block['block']} below the pre-registered per-capability threshold, with an overall drop of {pp(100 * safe_block['overall']['accuracy_drop'])}.</p><p>The next experiment showed why this is only a screen: independently low-impact blocks become harmful together, especially for OCR.</p></div><aside class=\"callout\"><strong>Key correction</strong>The heatmap ranks single interventions. It cannot be used as an additive recipe for aggressive pruning.</aside></div><div class=\"figure-grid\"><figure><img src=\"../../ablation-qwen25-vl-3b/capability_layer_heatmap.png\" alt=\"Per-capability layer sensitivity heatmap\"><figcaption>Every vision block bypassed once, scored by capability.</figcaption></figure><figure><img src=\"../../ablation-qwen25-vl-3b/capability_accuracy_drop_heatmap.png\" alt=\"Capability accuracy drop heatmap\"><figcaption>Accuracy damage is highly non-uniform across capability and block.</figcaption></figure></div></div></section>
    <section id=\"failures\"><div class=\"shell\"><p class=\"section-label\">What failed and why it matters</p><h2>Negative results narrowed the real question.</h2><div class=\"ledger\"><article><h3 class=\"bad\">Independent K8 ranking</h3><p>Task routes lost 10.18-37.30 points at K8. One-block effects are non-additive.</p></article><article><h3 class=\"bad\">Final-boundary SVD repair</h3><p>Feature L2 error fell, but answers did not reliably recover. Boundary similarity is not behavioral recovery.</p></article><article><h3 class=\"bad\">Target-only beam search</h3><p>Search accuracy looked good, then image-disjoint validation collapsed for object, OCR, and spatial routes.</p></article><article><h3 class=\"good\">Locked-clock K4</h3><p>Four skipped blocks delivered 6.47-7.28% vision speedup but only 1.39-4.41% end-to-end speedup.</p></article><article><h3 class=\"good\">Activation rescue</h3><p>Restoring a full hidden state after early skipped blocks partly recovered accuracy, supporting cumulative refinement over simple localization.</p></article><article><h3 class=\"good\">Evidence discipline</h3><p>Failed ideas remain in the record, rather than being silently optimized away using the external test.</p></article></div><h3>Feature repair diagnostic</h3>{table(['Route', 'Identity relative L2', 'Rank-8 bridge', 'Rank-32 bridge'], feature_rows)}<h3>Interaction-aware K8 validation</h3>{table(['Target capability', 'Search-selected blocks', 'Search drop', 'Target validation drop', 'Macro validation drop'], phase3_rows)}</div></section>
    <section id=\"external\"><div class=\"shell\"><p class=\"section-label\">Sealed external evaluation</p><h2>Capability effects exist. Universal task routing did not win.</h2><p>The 1,250-example external suite used unseen source families and was frozen before inference. It is now consumed and is not used by the current route search.</p>{external_table(external)}<div class=\"split\" style=\"margin-top:28px\"><div><p>At matched K8, the old conditional policy trailed generic pruning by <b>{pp(external_k8['mean_pp'])}</b>, with paired 95% interval [{external_k8['ci95_low_pp']:.2f}, {external_k8['ci95_high_pp']:.2f}] pp.</p><p>Spatial was the clear exception: conditional K8 beat generic K8 by +6.40 pp. Counting was the strongest failure at -11.20 pp.</p></div><aside class=\"callout\"><strong>Important boundary</strong>Task K4 versus generic K8 is not matched compute. It cannot establish a K4 route advantage.</aside></div></div></section>
    <section id=\"robust\"><div class=\"shell\"><p class=\"section-label\">Current final stage</p><h2>Source-balanced route search and matched-K controls</h2><p>The final search freezes the data manifests, optimizer budget, route priors, and objectives before inference. It uses separate generic and capability-specific families at K4, K6, and K8, then compares them with independent ranking, contiguous deletion, and three random controls.</p>{robust_table}<p class=\"note\"><b>Interpretation:</b> {esc(robust_interpretation)} This is image-disjoint method-selection evidence, not a replacement for an untouched external source-transfer evaluation.</p>{robust_capabilities}</div></section>
    <section id=\"research\"><div class=\"shell\"><p class=\"section-label\">Research context and next decision</p><h2>The novelty bar changed while the experiments ran.</h2><div class=\"split\"><div><p><a href=\"https://arxiv.org/abs/2507.23362\">Short-LVLM</a> already studies generic training-free VLM layer localization and feature-gap compensation. <a href=\"https://arxiv.org/abs/2511.19676\">INTERLACE</a> already studies structure-aware layer pruning with efficient adaptation. A March 2026 <a href=\"https://arxiv.org/abs/2603.20275\">domain-aware decoder-pruning study</a> reports that low budgets are ranking-sensitive while higher budgets become structure-limited.</p><p>This project therefore does not claim generic task-aware pruning as new. Its useful question is whether a separate <b>vision encoder</b> has source-stable capability routes under no fine-tuning, matched block budgets, and explicit collateral-damage controls.</p></div><aside class=\"callout\"><strong>Next credible paper step</strong>Replicate a frozen route-selection rule on a second VLM and a newly sealed source family. If the effect is unstable, report that as the result rather than tuning against it.</aside></div><p class=\"note\">Full protocols, configs, manifests, decision logs, and compact results are linked from the repository README. Raw predictions and images are intentionally excluded from Git because they are large and/or licensed datasets.</p></div></section>
  </main>
  <footer><div class=\"shell\">Generated from committed compact summaries plus frozen robust-route analysis. Accuracy drops are percentage points relative to the paired full-model condition; negative drops indicate improvement. This report distinguishes exploratory, method-selection, and consumed external evidence.</div></footer>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROBUST_ROOT / "site")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    source = render()
    (args.output_dir / "index.html").write_text(source, encoding="utf-8")
    (args.output_dir / "report-data.json").write_text(
        json.dumps(
            {
                "robust_analysis": str(ROBUST_ROOT / "analysis" / "analysis.json"),
                "external_analysis": "results/external-frozen-qwen25-vl-3b/analysis.json",
                "baseline": "results/baseline-qwen25-vl-3b/summary.json",
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    print(args.output_dir / "index.html")


if __name__ == "__main__":
    main()
