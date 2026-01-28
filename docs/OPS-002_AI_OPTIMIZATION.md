# ⚙️ OPS-002: AI Persona Optimization Protocol
[**Home**](Home) > **Operations** > **OPS-002**

**Doc ID:** `OPS-002`
**Status:** Active
**Toolchain:** DSPy, Ollama, Python
**Owner:** DevOps / Research Lead

---

## 1. Objective
To systematically reduce the **Latency** and **Verbosity** of the Autonomous Ground Control System (AGCS) personas without sacrificing **Factuality**.

> **The Problem:** "Raw" LLMs are too chatty. They treat tactical alerts like a customer service conversation.
> **The Goal:** Reduce Pilot output from ~100 words (Chat) to <20 words (Tactical Alert).

---

## 2. The Optimization Pipeline

We utilize **DSPy (Declarative Self-improving Language Programs)** to "compile" our prompts rather than manually engineering them.

### A. The "Golden Dataset"
Optimization requires Ground Truth. We use historical mission logs to teach the AI what "Good" looks like.
* **Source:** `golden_datasets/mission_*.jsonl`
* **Format:** Raw Telemetry + Expected Output (The "Right Answer").

### B. The Training Script (`labs/train.py`)
This script loads the dataset and runs a **BootstrapFewShot** optimizer. It iteratively tests different prompts against a metric function to find the most efficient one.

```python
# The "Metric" (What we value)
def validate_pilot(example, pred, trace=None):
    factuality = check_facts(pred, example)
    brevity = len(pred.split()) <= 20  # Strict Word Limit
    return factuality and brevity
```

---

## 3. Execution Procedure

### Step 1: Prepare the Environment
Ensure the local inference engine is running with GPU acceleration.
```bash
export OLLAMA_NUM_GPU=99
ollama serve
```

### Step 2: Run the Optimizer
Execute the training script targeting a specific persona (e.g., Pilot).
```bash
# Syntax: python3 labs/train.py --persona <role> --log <dataset>
python3 labs/train.py --persona pilot --log golden_datasets/mission_20260127_172522.jsonl
```

### Step 3: Deployment
The script outputs a JSON artifact containing the optimized prompt weights.
* **Output:** `config/optimized_pilot.json`
* **Action:** The main system (`main.py`) automatically detects this file. If it exists, it loads the Optimized Persona. If not, it falls back to the generic `personas.json`.

---

## 4. Performance Standards (Pass/Fail)

| Metric | Threshold | Current Status (v1.2.3) |
| :--- | :--- | :--- |
| **Factuality** | 100% Match | ✅ 100% |
| **Verbosity** | < 20 Words | ✅ 19 Words (Avg) |
| **Hallucination** | 0 occurrences | ✅ 0% |
| **Tone** | "Military/Concise" | ✅ Verified |

---

## 5. Troubleshooting

**Issue:** "Optimization takes forever."
* **Cause:** Using a large model (e.g., Llama 3 70B) or CPU inference.
* **Fix:** Switch to `llama3.1:8b` and ensure `OLLAMA_NUM_GPU=99`.

**Issue:** "The AI is too quiet."
* **Cause:** The brevity penalty in the metric might be too harsh (<5 words).
* **Fix:** Adjust `labs/train.py` metric function to allow slightly more nuance.
