## `abcli` CI/CD Refactoring

### 1. Goal

Refactor the GitHub Action pipeline into parallel jobs. Split code coverage into **CLI** and **UI** segments, move coverage configurations into `pyproject.toml`, and automate the persistence of badges to the `badges` branch.

### 2. Workflow Architecture

The pipeline must be split into independent jobs to allow for parallel execution and partial failures.

#### **Job 1: Linting (`lint`)**

* **Action:** Execute the existing `./lint.sh` script.
* **Environment:** Ensure all dependencies required by the script (ruff, mypy, etc.) are installed.
* **Constraint:** Do **not** modify the existing linting configuration files.

#### **Job 2: CLI Testing (`test-cli`)**

* **Tests:** Run all tests **except** `tests/test_abui`.
* **Coverage:** Measure coverage for `ab_cli` but **omit** the `ab_cli/abui` directory.
* **Badge:** Generate `coverage.svg` using shields.io.
* **Output:** Upload the badge as a workflow artifact named `coverage-badge-cli`.

#### **Job 3: UI Testing (`test-ui`)**

* **Tests:** Run only `tests/test_abui`.
* **Coverage:** Measure coverage **exclusively** for the `ab_cli/abui` directory.
* **Badge:** Generate `coverage_ui.svg` using shields.io.
* **Output:** Upload the badge as a workflow artifact named `coverage-badge-ui`.

#### **Job 4: Build (`build`)**

* **Requirement:** Runs only if `lint`, `test-cli`, and `test-ui` pass.
* **Action:** Build the Python package (sdist and wheel).
* **Output:** Upload the `dist/` folder as a workflow artifact named `python-package`.

#### **Job 5: Badge Update (`update-badges`)**

* **Requirement:** Runs only on `push` to the `master` branch.
* **Action:** Download badges from Jobs 2 & 3, checkout the `badges` branch, and commit/push the updated `.svg` files.

---

### 3. Coverage Configuration (`pyproject.toml`)

Consolidate the coverage logic. Since the pipeline requires two different coverage behaviors, the `pyproject.toml` should define the **CLI (default)** behavior, and the CI job for the **UI** will use CLI overrides.

| Section | Key | Value/Logic |
| --- | --- | --- |
| **`[tool.coverage.run]`** | `source` | `["ab_cli"]` |
|  | `omit` | `["ab_cli/abui/*", "tests/*"]` |
| **`[tool.coverage.report]`** | `show_missing` | `true` |

> **Note for Agent:** For the **UI Test Job**, use `pytest --cov=ab_cli.abui --cov-report=term --cov-config=/dev/null` (or similar) to ensure the global `omit` rules in `pyproject.toml` do not exclude the UI code during that specific run.

---

### 4. Badge Generation

Rather than using the coverage-badge library (which can cause dependency issues), we will leverage shields.io for badge generation:

1. Extract coverage percentage from the XML coverage report
2. Determine badge color based on coverage level (red < 50%, yellow < 75%, green ≥ 75%)
3. Download badge directly from shields.io with appropriate formatting
4. Use the format: `https://img.shields.io/badge/Coverage-XX%25-COLOR?style=flat`

---

### 5. Implementation Details

* **Permissions:** Ensure the workflow has `contents: write` permissions to allow the `update-badges` job to push to the `badges` branch.
* **Artifact Handling:** Use `actions/upload-artifact@v4` and `actions/download-artifact@v4`.
* **Package Generation:** Use the `build` library (`python -m build`).
* **README Links:** The badges should remain linked to:
* `https://raw.githubusercontent.com/tiry/abcli/badges/coverage.svg`
* `https://raw.githubusercontent.com/tiry/abcli/badges/coverage_ui.svg`