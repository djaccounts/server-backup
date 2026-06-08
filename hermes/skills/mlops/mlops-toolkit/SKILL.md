---
name: mlops-toolkit
description: "MLOps toolkit: model evaluation (lm-eval-harness), experiment tracking (Weights & Biases), prompt optimization (DSPy), local inference (llama.cpp/GGUF), model surgery (OBLITERATUS). Use for ML experiment lifecycle: evaluating LLMs, tracking runs, optimizing prompts with DSPy, running local GGUF models, or ablating LLM refusals."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mlops, evaluation, wandb, dspy, llama-cpp, obliteratus, gguf, experiment-tracking, prompt-optimization, local-inference, abliteration]
    related_skills: [mlops-toolkit]
---

# MLOps Toolkit

Machine Learning Operations: evaluation, experiment tracking, prompt optimization, local inference, and model surgery.

---

## 1. Model Evaluation (lm-evaluation-harness)

**Use when:** Benchmarking LLMs on standard tasks (MMLU, GSM8K, HumanEval, etc.)

```bash
pip install lm-eval

# Run benchmark:
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-3.1-8B-Instruct \
  --tasks mmlu,gsm8k \
  --batch_size auto \
  --output_path results/

# List available tasks:
lm_eval --tasks list
```

Supported benchmarks: MMLU, GSM8K, HumanEval, ARC, HellaSwag, TruthfulQA, Winogrande, and 100+ more.

---

## 2. Experiment Tracking (Weights & Biases)

**Use when:** Tracking ML experiments, comparing runs, hyperparameter sweeps, model registry.

```bash
pip install wandb
wandb login
```

### Basic Tracking

```python
import wandb

run = wandb.init(project="my-project", config={
    "lr": 0.001, "epochs": 10, "batch_size": 32
})

for epoch in range(config.epochs):
    train_loss = train_epoch()
    wandb.log({"train/loss": train_loss, "val/loss": val_loss, "epoch": epoch})

wandb.finish()
```

### Hyperparameter Sweeps

```python
sweep_config = {
    'method': 'bayes',
    'metric': {'name': 'val/accuracy', 'goal': 'maximize'},
    'parameters': {
        'lr': {'distribution': 'log_uniform', 'min': 1e-5, 'max': 1e-1},
        'batch_size': {'values': [16, 32, 64]}
    }
}
sweep_id = wandb.sweep(sweep_config, project="my-project")
wandb.agent(sweep_id, function=train, count=20)
```

### Framework Integrations

- **PyTorch Lightning:** `WandbLogger(project="...")`
- **HuggingFace Trainer:** `TrainingArguments(report_to="wandb")`
- **Keras:** `WandbCallback()`

---

## 3. Prompt Optimization (DSPy)

**Use when:** Building multi-component AI systems, optimizing prompts automatically, building RAG pipelines.

```bash
pip install dspy
```

### Quick Start

```python
import dspy

lm = dspy.Claude(model="claude-sonnet-4-5-20250929")
dspy.settings.configure(lm=lm)

# Define signature:
class QA(dspy.Signature):
    question = dspy.InputField()
    answer = dspy.OutputField(desc="1-5 words")

# Use:
qa = dspy.ChainOfThought(QA)
result = qa(question="What is the capital of France?")
print(result.answer)  # "Paris"
```

### Optimizers

- **BootstrapFewShot:** Learns from examples
- **MIPRO:** Iteratively improves prompts (best quality)
- **BootstrapFinetune:** Creates datasets for model fine-tuning

---

## 4. Local GGUF Inference (llama.cpp)

**Use when:** Running local models on CPU/GPU, finding GGUF quantizations, private inference.

```bash
# Install:
brew install llama.cpp  # macOS/Linux
# or build from source:
cmake -B build && cmake --build build --config Release

# Run directly from HuggingFace Hub:
llama-server -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0

# OpenAI-compatible API:
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role":"user","content":"Hello"}]}'
```

### Model Discovery Workflow

1. Search Hub: `https://huggingface.co/models?apps=llama.cpp&sort=trending`
2. Check local-app view: `https://huggingface.co/<repo>?local-app=llama.cpp`
3. Tree API for file listing: `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`
4. Copy recommended quant command from the Hub page

### Choosing a Quant

- General chat: `Q4_K_M`
- Code/technical: `Q5_K_M` or `Q6_K`
- Tight RAM: `Q3_K_M` or `IQ` variants
- Repo-native labels: use exact label from HF page (e.g., `UD-Q4_K_M`)

### Python Bindings

```python
from llama_cpp import Llama

llm = Llama(model_path="./model-q4_k_m.gguf", n_ctx=4096, n_gpu_layers=35)
out = llm("What is machine learning?", max_tokens=256)
print(out["choices"][0]["text"])
```

---

## 5. Model Surgery (OBLITERATUS)

**Use when:** Removing refusal behaviors from open-weight LLMs without retraining.

> **License warning:** OBLITERATUS is AGPL-3.0. Always invoke via CLI. Never `import obliteratus` in MIT projects.

```bash
# Install:
git clone https://github.com/elder-plinius/OBLITERATUS.git
cd OBLITERATUS && pip install -e .

# Check hardware:
python3 -c "import torch; print(torch.cuda.get_device_name(0), torch.cuda.get_device_properties(0).total_memory/1024**3, 'GB')"

# Get recommendations:
obliteratus recommend <model_name>

# Run abliteration:
obliteratus obliterate <model_name> --method advanced --quantization 4bit --output-dir ./abliterated-models

# Verify:
# Refusal rate < 5%, Perplexity change < 10%
```

### Method Selection

| Situation | Method |
|-----------|--------|
| Default / most models | `advanced` |
| Quick test | `basic` |
| MoE models (DeepSeek, Mixtral) | `nuclear` |
| Reasoning models (R1) | `surgical` |
| Stubborn refusals | `aggressive` (risk of coherence damage) |

### VRAM Requirements (4-bit)

| VRAM | Max Model Size |
|------|---------------|
| 4-8 GB | ~4B params |
| 8-16 GB | ~9B params |
| 24 GB | ~32B params |
| 48 GB+ | ~72B+ params |

### Common Pitfalls

1. **Models under ~1B respond poorly** — expect partial results (20-40% remaining refusal)
2. **`aggressive` can damage coherence** — only if `advanced` leaves >10% refusals on 3B+
3. **Always check perplexity** — if spikes >15%, reduce aggressiveness
4. **Spectral certification RED is common** — check actual refusal rate, not spectral certification
