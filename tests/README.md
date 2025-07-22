# NFL Stats Agent Test Suite

This directory contains the automated test suites for the NFL Stats Agent project. The tests are designed to ensure the reliability, accuracy, and robustness of the agent across its core components.

## Test Suite Overview

### 1. `test_filtering_fix.py`
- **Purpose:** Validates the question validation filter.
- **What it tests:**
  - Ensures NFL/statistics questions are NOT incorrectly filtered out.
  - Ensures irrelevant/non-NFL questions (e.g., weather, NBA, cooking) ARE filtered out.
  - Prints clear pass/fail results and filter reasoning for each case.

### 2. `test_scoring.py`
- **Purpose:** Compares database vs. web answers and tests the LLM scoring agent.
- **What it tests:**
  - Ensures the LLM scoring agent selects the best answer (DB or web) for a variety of queries.
  - Includes both web-favored (recent news, injuries, trades) and DB-favored (historical stats, season stats) queries.
  - Prints both answers, scores, LLM choice, and rationale for each test.

### 3. `test_sql_agent.py`
- **Purpose:** Tests the SQL agent's ability to generate and execute correct SQL for NFL stats queries.
- **What it tests:**
  - SQL generation for basic and complex queries.
  - Execution accuracy (DB results vs. expected results).
  - Edge cases and performance.
  - Detailed progress, pass/fail, and reasons are printed for each test.

### 4. `run_tests.py`
- **Purpose:** Orchestrates running all test suites from a single command.
- **How to use:**
  - Run all tests: `python run_tests.py`
  - Run a specific suite: `python run_tests.py --test filtering|scoring|sql`
  - Prints section headers and summaries for each suite.

## How to Run All Tests

From the `tests/` directory (or project root):

```bash
python tests/run_tests.py
```

## Adding New Tests
- Add new test files in this directory following the structure of the existing suites.
- Update `run_tests.py` to import and run your new suite.

## Notes
- All tests use clear debug output and pass/fail reporting.
- The LLM scoring agent is now the primary selector for answer quality.
- Filtering and SQL agent logic are tested independently for clarity and maintainability.

---

**Maintained by:** NFL Stats Agent project contributors 