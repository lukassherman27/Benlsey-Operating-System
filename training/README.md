# Bensley Operations System - LLM Training Data

## Overview

This directory contains exported conversation data from Claude Code sessions focused on building the Bensley Operations Platform. The data captures architectural decisions, code patterns, business logic, and technical problem-solving discussions.

## Export Statistics

- **Total conversation files processed**: 49
- **Total entries parsed**: 3,580
- **Total messages extracted**: 2,119 (686 cleaned conversation pairs)
- **Export date**: November 23, 2025

## File Formats

### 1. `bensley_conversations_sharegpt.jsonl` (468 KB)
**Best for**: Multi-turn conversational models

Format:
```json
{
  "conversations": [
    {"from": "human", "value": "user message here"},
    {"from": "gpt", "value": "assistant response here"}
  ],
  "session_id": "..."
}
```

**Use with**:
- Llama-Factory
- FastChat
- OpenAI-style chat fine-tuning

### 2. `bensley_conversations_raw.jsonl` (524 KB)
**Best for**: Custom training pipelines

Format:
```json
{
  "role": "user" or "assistant",
  "content": "message text",
  "session_id": "...",
  "agent_id": "..."
}
```

**Use with**:
- Custom preprocessing scripts
- Preserves all metadata for filtering/grouping

### 3. `bensley_conversations_combined.json` (1.2 MB)
**Best for**: Inspection and analysis

Contains all conversations with full metadata in a single JSON file with:
- Export metadata (date, counts, etc.)
- Complete conversation history
- Session and agent IDs

## Training Recommendations

### Option 1: Fine-tune a Local Model with Llama-Factory

1. Install Llama-Factory:
```bash
git clone https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory
pip install -e .
```

2. Copy the ShareGPT file:
```bash
cp bensley_conversations_sharegpt.jsonl LLaMA-Factory/data/bensley.jsonl
```

3. Update `LLaMA-Factory/data/dataset_info.json`:
```json
"bensley": {
  "file_name": "bensley.jsonl",
  "formatting": "sharegpt",
  "columns": {
    "messages": "conversations"
  }
}
```

4. Train with Llama 3 or similar:
```bash
llamafactory-cli train \
  --stage sft \
  --model_name_or_path meta-llama/Llama-3-8B \
  --dataset bensley \
  --template llama3 \
  --finetuning_type lora \
  --output_dir ./bensley_model \
  --per_device_train_batch_size 4 \
  --gradient_accumulation_steps 4 \
  --num_train_epochs 3 \
  --learning_rate 5e-5
```

### Option 2: Use with Ollama + Unsloth

1. Install Unsloth:
```bash
pip install unsloth
```

2. Fine-tune locally:
```python
from unsloth import FastLanguageModel
import json

# Load model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3-8b-bnb-4bit",
    max_seq_length=2048,
    load_in_4bit=True,
)

# Load dataset
with open('bensley_conversations_sharegpt.jsonl') as f:
    data = [json.loads(line) for line in f]

# Train...
```

3. Export to Ollama:
```bash
unsloth.save_model_for_ollama(model, tokenizer, "bensley-ai")
```

### Option 3: Use with Axolotl

1. Install Axolotl:
```bash
pip install axolotl
```

2. Create config file `bensley_config.yml`:
```yaml
base_model: meta-llama/Llama-3-8B
datasets:
  - path: bensley_conversations_sharegpt.jsonl
    type: sharegpt
    conversation: conversations

sequence_len: 2048
micro_batch_size: 4
gradient_accumulation_steps: 4
num_epochs: 3
learning_rate: 0.00005
```

3. Train:
```bash
accelerate launch -m axolotl.cli.train bensley_config.yml
```

## What This Data Contains

The exported conversations cover:

### Technical Topics
- React/Next.js frontend architecture
- FastAPI backend design
- SQLite database schema design
- TypeScript/Python best practices
- State management patterns
- API design and error handling

### Business Logic
- Proposal tracking workflows
- Contract management
- Financial calculations
- Email categorization
- Document intelligence
- Project health monitoring

### Domain Knowledge
- Bensley's project structure
- Client interaction patterns
- Proposal lifecycle management
- Financial tracking requirements
- Reporting needs
- Dashboard design

## Training Tips

1. **Start Small**: Begin with a 7B or 8B parameter model (Llama 3, Mistral, etc.)
2. **Use LoRA/QLoRA**: For efficient fine-tuning on consumer hardware
3. **Monitor Overfitting**: With ~700 conversation pairs, don't overtrain
4. **Augment Data**: Consider combining with general coding datasets
5. **Test Thoroughly**: Validate on real Bensley queries before deployment

## Hardware Requirements

### Minimum (LoRA/QLoRA)
- 16GB RAM
- NVIDIA GPU with 8GB VRAM (RTX 3060 or better)
- 50GB storage

### Recommended
- 32GB RAM
- NVIDIA GPU with 16GB+ VRAM (RTX 4090, A100)
- 100GB SSD storage

## Re-exporting Data

To re-run the export (e.g., after more conversations):

```bash
python3 export_conversations.py
```

The script will:
- Find all agent conversation files in `~/.claude/projects/`
- Parse messages and tool calls
- Export in multiple formats
- Create this directory with all files

## Next Steps

1. Review the exported conversations in `bensley_conversations_combined.json`
2. Choose a training framework based on your hardware
3. Start with a small model (7B/8B) and LoRA fine-tuning
4. Test with queries about Bensley's architecture
5. Iterate based on performance

## Questions?

The export script is at: `../export_conversations.py`

You can modify it to:
- Filter by date range
- Include/exclude tool calls
- Change output formats
- Add custom preprocessing
