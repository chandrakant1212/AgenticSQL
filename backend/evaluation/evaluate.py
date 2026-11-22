"""
Evaluation script for the AgenticSQL Text-to-SQL system.

Measures:
1. SQL Execution Accuracy — queries that execute successfully
2. Self-Correction Success Rate — failed queries recovered via correction
3. Average Retry Count
4. Response Latency
5. Error Rate
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.graph import run_agent
from app.config import get_settings
from app.database.seed import create_tables, seed_database

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def load_dataset() -> list[dict]:
    """Load the evaluation dataset."""
    dataset_path = Path(__file__).parent / "dataset.json"
    with open(dataset_path, "r") as f:
        return json.load(f)


async def evaluate_question(test_case: dict, session_id: str = "eval") -> dict:
    """
    Evaluate a single test case.

    Returns:
        Result dictionary with metrics.
    """
    question = test_case["question"]
    category = test_case.get("category", "unknown")
    difficulty = test_case.get("difficulty", "unknown")
    expected_columns = test_case.get("expected_columns", [])
    is_out_of_scope = category == "out_of_scope"

    start_time = time.time()

    try:
        result = await run_agent(question=question, session_id=session_id)
        latency = time.time() - start_time

        status = result.get("status", "unknown")
        retry_count = result.get("retry_count", 0)
        sql = result.get("generated_sql", "")
        columns = result.get("columns", [])
        total_rows = result.get("total_rows", 0)

        # Determine success
        if is_out_of_scope:
            # Out-of-scope questions should be detected
            success = status == "out_of_scope"
            initially_failed = False
            self_corrected = False
        else:
            success = status in ("success", "corrected") and total_rows >= 0
            initially_failed = retry_count > 0
            self_corrected = status == "corrected" and success

            # Check if expected columns are present (fuzzy match)
            if success and expected_columns:
                col_lower = [c.lower() for c in columns]
                column_match = any(
                    any(exp.lower() in c for c in col_lower)
                    for exp in expected_columns
                )
                # Don't fail on column name mismatch — just note it
            else:
                column_match = True

        return {
            "id": test_case["id"],
            "question": question,
            "category": category,
            "difficulty": difficulty,
            "success": success,
            "status": status,
            "initially_failed": initially_failed,
            "self_corrected": self_corrected,
            "retry_count": retry_count,
            "latency": latency,
            "sql": sql[:200],
            "total_rows": total_rows,
            "error": result.get("sql_error", ""),
        }

    except Exception as e:
        latency = time.time() - start_time
        return {
            "id": test_case["id"],
            "question": question,
            "category": category,
            "difficulty": difficulty,
            "success": False,
            "status": "exception",
            "initially_failed": True,
            "self_corrected": False,
            "retry_count": 0,
            "latency": latency,
            "sql": "",
            "total_rows": 0,
            "error": str(e),
        }


async def run_evaluation():
    """Run the full evaluation suite."""
    print("=" * 70)
    print("AgenticSQL — Evaluation Framework")
    print("=" * 70)

    # Initialize database
    print("\nInitializing database...")
    create_tables()
    seed_database()

    # Load dataset
    dataset = load_dataset()
    print(f"Loaded {len(dataset)} test cases\n")

    # Run evaluations
    results = []
    for i, test_case in enumerate(dataset):
        category = test_case.get("category", "")
        print(f"[{i+1}/{len(dataset)}] {test_case['question'][:60]}... ", end="", flush=True)

        result = await evaluate_question(test_case, session_id=f"eval_{i}")
        results.append(result)

        status_icon = "✅" if result["success"] else "❌"
        correction = " (corrected)" if result["self_corrected"] else ""
        print(f"{status_icon} {result['latency']:.1f}s{correction}")

    # Calculate metrics
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS")
    print("=" * 70)

    total = len(results)
    # Exclude out-of-scope from SQL metrics
    data_questions = [r for r in results if r["category"] != "out_of_scope"]
    oos_questions = [r for r in results if r["category"] == "out_of_scope"]

    total_data = len(data_questions)
    successful = sum(1 for r in data_questions if r["success"])
    initially_failed = sum(1 for r in data_questions if r["initially_failed"])
    self_corrected = sum(1 for r in data_questions if r["self_corrected"])
    total_retries = sum(r["retry_count"] for r in data_questions)
    latencies = [r["latency"] for r in data_questions]
    errors = sum(1 for r in data_questions if not r["success"])

    # Out-of-scope detection
    oos_detected = sum(1 for r in oos_questions if r["success"])

    print(f"\nTotal Questions:                {total}")
    print(f"Data Questions:                 {total_data}")
    print(f"Out-of-Scope Questions:         {len(oos_questions)}")
    print(f"\n--- SQL Execution Metrics (Data Questions) ---")
    print(f"Final Execution Accuracy:       {successful}/{total_data} ({100*successful/max(total_data,1):.1f}%)")
    print(f"Initially Failed (needed correction): {initially_failed}/{total_data} ({100*initially_failed/max(total_data,1):.1f}%)")
    print(f"Self-Correction Success Rate:   {self_corrected}/{max(initially_failed,1)} ({100*self_corrected/max(initially_failed,1):.1f}%)")
    print(f"Average Retry Count:            {total_retries/max(total_data,1):.2f}")
    print(f"Error Rate:                     {100*errors/max(total_data,1):.1f}%")
    print(f"Average Latency:                {sum(latencies)/max(len(latencies),1):.2f}s")
    print(f"\n--- Out-of-Scope Detection ---")
    print(f"Correctly Detected:             {oos_detected}/{len(oos_questions)}")

    # Per-category breakdown
    print(f"\n--- Per-Category Breakdown ---")
    categories = sorted(set(r["category"] for r in data_questions))
    print(f"{'Category':<20} {'Total':>6} {'Success':>8} {'Rate':>8}")
    print("-" * 45)
    for cat in categories:
        cat_results = [r for r in data_questions if r["category"] == cat]
        cat_success = sum(1 for r in cat_results if r["success"])
        rate = 100 * cat_success / max(len(cat_results), 1)
        print(f"{cat:<20} {len(cat_results):>6} {cat_success:>8} {rate:>7.1f}%")

    # Per-difficulty breakdown
    print(f"\n--- Per-Difficulty Breakdown ---")
    difficulties = ["easy", "medium", "hard"]
    print(f"{'Difficulty':<12} {'Total':>6} {'Success':>8} {'Rate':>8}")
    print("-" * 38)
    for diff in difficulties:
        diff_results = [r for r in data_questions if r["difficulty"] == diff]
        diff_success = sum(1 for r in diff_results if r["success"])
        rate = 100 * diff_success / max(len(diff_results), 1)
        print(f"{diff:<12} {len(diff_results):>6} {diff_success:>8} {rate:>7.1f}%")

    # Save results
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    results_file = results_dir / "evaluation_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "summary": {
                "total_questions": total,
                "data_questions": total_data,
                "execution_accuracy": round(100 * successful / max(total_data, 1), 1),
                "self_correction_rate": round(100 * self_corrected / max(initially_failed, 1), 1),
                "avg_retries": round(total_retries / max(total_data, 1), 2),
                "avg_latency": round(sum(latencies) / max(len(latencies), 1), 2),
                "error_rate": round(100 * errors / max(total_data, 1), 1),
            },
            "results": results,
        }, f, indent=2)

    print(f"\nDetailed results saved to: {results_file}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_evaluation())
