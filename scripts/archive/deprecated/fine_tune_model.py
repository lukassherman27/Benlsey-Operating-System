#!/usr/bin/env python3
"""
Fine-Tune Local Model with Bensley Training Data
Uses LoRA (Low-Rank Adaptation) for efficient training
"""

import json
import os
from datetime import datetime

TRAINING_DATA_DIR = "/Users/lukassherman/Desktop/BDS_SYSTEM/TRAINING_DATA"
MODEL_OUTPUT_DIR = "/Users/lukassherman/Desktop/BDS_SYSTEM/LOCAL_MODELS"

def load_training_data():
    """Load all training data"""
    print("="*80)
    print("LOADING TRAINING DATA")
    print("="*80)

    # Load business context
    with open(f"{TRAINING_DATA_DIR}/business_context.json", "r") as f:
        business_context = json.load(f)
    print(f"✓ Loaded business context: {len(business_context['projects'])} projects")

    # Load human-verified examples (HIGHEST QUALITY)
    with open(f"{TRAINING_DATA_DIR}/human_verified_examples.json", "r") as f:
        human_examples = json.load(f)
    print(f"✓ Loaded {len(human_examples)} human-verified examples")

    # Load high-quality AI examples
    with open(f"{TRAINING_DATA_DIR}/high_quality_ai_examples.json", "r") as f:
        ai_examples = json.load(f)
    print(f"✓ Loaded {len(ai_examples)} high-quality AI examples")

    # Load prompt templates
    with open(f"{TRAINING_DATA_DIR}/training_prompts.json", "r") as f:
        prompt_templates = json.load(f)
    print(f"✓ Loaded {len(prompt_templates)} prompt templates")

    return business_context, human_examples, ai_examples, prompt_templates

def create_system_prompt(business_context):
    """Create comprehensive system prompt with business knowledge"""
    projects_str = ", ".join([f"{p['code']} ({p['client']})" for p in business_context['projects'][:10]])
    if len(business_context['projects']) > 10:
        projects_str += f" ...and {len(business_context['projects'])-10} more"

    system_prompt = f"""You are an intelligent email assistant for {business_context['company']['name']}.

COMPANY CONTEXT:
- Business: {business_context['company']['business_type']}
- Focus: {business_context['company']['focus']}
- Key People: {', '.join(business_context['company']['key_people'])}
- Locations: {', '.join(business_context['company']['locations'])}

ACTIVE PROJECTS ({len(business_context['projects'])} total):
{projects_str}

YOUR TASKS:
1. Categorize emails into: proposal, meeting, contract, project_update, schedule, design, rfi, invoice, general
2. Extract subcategories and key information
3. Provide importance score (0.0-1.0)
4. Write concise summaries focused on action items

CATEGORIZATION GUIDELINES:
- "proposal": New business opportunities, RFPs, fee proposals
- "meeting": Scheduled meetings, recaps, action items
- "contract": Legal documents, SOWs, amendments
- "project_update": Progress reports, milestones, delays
- "schedule": Deadlines, timelines, delivery dates
- "design": Design reviews, drawings, specifications
- "rfi": Requests for information from clients
- "invoice": Billing, payment, financial matters
- "general": Everything else (use sparingly)

Return JSON format:
{{
  "category": "category_name",
  "subcategory": "subcategory_name",
  "importance_score": 0.85,
  "summary": "Brief 2-3 sentence summary with action items",
  "project_code": "XXX-XX-XX" (if applicable),
  "people_mentioned": ["names"],
  "action_required": true/false
}}"""

    return system_prompt

def format_training_examples(business_context, human_examples, ai_examples):
    """Format training data for model fine-tuning"""
    print("\n" + "="*80)
    print("FORMATTING TRAINING DATA")
    print("="*80)

    system_prompt = create_system_prompt(business_context)
    formatted_examples = []

    # PRIORITY 1: Human-verified examples (highest quality)
    print(f"\nProcessing {len(human_examples)} human-verified examples...")
    for example in human_examples:
        if example['task'] == 'classify':
            user_message = f"""Categorize this email:

Subject: {example['input'].get('subject', '')}
From: {example['input'].get('sender', '')}
Preview: {example['input'].get('preview', '')}"""

            assistant_message = json.dumps(example['output'], indent=2)

            formatted_examples.append({
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": assistant_message}
                ],
                "quality": "human_verified",
                "weight": 3.0  # Triple weight for human examples
            })

    print(f"  ✓ Formatted {len(formatted_examples)} human-verified examples")

    # PRIORITY 2: High-confidence AI examples (supplement)
    print(f"\nProcessing {len(ai_examples)} high-quality AI examples...")
    for example in ai_examples[:100]:  # Limit to avoid overwhelming with AI data
        user_message = f"""Categorize this email:

Subject: {example['input'].get('subject', '')}
From: {example['input'].get('sender', '')}
Preview: {example['input'].get('preview', '')}"""

        assistant_message = json.dumps(example['output'], indent=2)

        formatted_examples.append({
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_message}
            ],
            "quality": "high_confidence_ai",
            "weight": 1.0
        })

    print(f"  ✓ Formatted {len(formatted_examples) - len(human_examples)} AI examples")
    print(f"\n  TOTAL: {len(formatted_examples)} training examples")

    return formatted_examples, system_prompt

def save_for_fine_tuning(formatted_examples, system_prompt):
    """Save training data in format for various fine-tuning tools"""
    os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)

    print("\n" + "="*80)
    print("SAVING FINE-TUNING DATASETS")
    print("="*80)

    # 1. OpenAI/HuggingFace JSONL format
    jsonl_path = f"{MODEL_OUTPUT_DIR}/training_data.jsonl"
    with open(jsonl_path, "w") as f:
        for example in formatted_examples:
            f.write(json.dumps(example['messages']) + "\n")
    print(f"✓ Saved JSONL format: {jsonl_path}")

    # 2. Axolotl YAML config
    axolotl_config = f"""base_model: mistralai/Mistral-7B-Instruct-v0.2
model_type: MistralForCausalLM
tokenizer_type: LlamaTokenizer

load_in_8bit: false
load_in_4bit: true
strict: false

datasets:
  - path: {jsonl_path}
    type: chat_template

dataset_prepared_path:
val_set_size: 0.05
output_dir: {MODEL_OUTPUT_DIR}/bensley-email-assistant

adapter: lora
lora_r: 32
lora_alpha: 16
lora_dropout: 0.05
lora_target_linear: true

sequence_len: 2048
sample_packing: true
pad_to_sequence_len: true

wandb_project:
wandb_entity:
wandb_watch:
wandb_name:
wandb_log_model:

gradient_accumulation_steps: 4
micro_batch_size: 2
num_epochs: 3
optimizer: adamw_8bit
lr_scheduler: cosine
learning_rate: 0.0002

train_on_inputs: false
group_by_length: false
bf16: auto
fp16:
tf32: false

gradient_checkpointing: true
early_stopping_patience:
resume_from_checkpoint:
local_rank:
logging_steps: 1
xformers_attention:
flash_attention: true

warmup_steps: 10
evals_per_epoch: 4
eval_table_size:
saves_per_epoch: 1
debug:
deepspeed:
weight_decay: 0.0
fsdp:
fsdp_config:
special_tokens:
"""

    axolotl_path = f"{MODEL_OUTPUT_DIR}/axolotl_config.yml"
    with open(axolotl_path, "w") as f:
        f.write(axolotl_config)
    print(f"✓ Saved Axolotl config: {axolotl_path}")

    # 3. System prompt for inference
    system_prompt_path = f"{MODEL_OUTPUT_DIR}/system_prompt.txt"
    with open(system_prompt_path, "w") as f:
        f.write(system_prompt)
    print(f"✓ Saved system prompt: {system_prompt_path}")

    # 4. README with instructions
    readme = f"""# Bensley Email Assistant - Fine-Tuned Model
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Training Data Summary
- Total examples: {len(formatted_examples)}
- Human-verified: {sum(1 for e in formatted_examples if e['quality'] == 'human_verified')}
- High-quality AI: {sum(1 for e in formatted_examples if e['quality'] == 'high_confidence_ai')}

## Files
1. `training_data.jsonl` - Training dataset in JSONL format
2. `axolotl_config.yml` - Configuration for Axolotl fine-tuning
3. `system_prompt.txt` - System prompt for inference
4. `bensley-email-assistant/` - Output directory for trained model (after training)

## Quick Start - Option 1: Ollama (Easiest)

```bash
# Install Ollama
brew install ollama

# Download base model
ollama pull mistral

# Create Modelfile
cat > Modelfile <<EOF
FROM mistral
SYSTEM "$(cat system_prompt.txt)"
EOF

# Create custom model
ollama create bensley-email-assistant -f Modelfile

# Test it
ollama run bensley-email-assistant "Categorize this email: Subject: Fee proposal for Maldives resort project..."
```

## Quick Start - Option 2: Fine-Tuning with Axolotl

```bash
# Install Axolotl
pip install axolotl

# Run fine-tuning (2-4 hours)
accelerate launch -m axolotl.cli.train axolotl_config.yml

# After training, model will be in: bensley-email-assistant/
```

## Quick Start - Option 3: LM Studio (GUI)

1. Download LM Studio: https://lmstudio.ai/
2. Load base model: Mistral-7B-Instruct
3. Import training_data.jsonl
4. Click "Fine-tune"
5. Wait 2-4 hours
6. Export model

## Using the Fine-Tuned Model

```python
import json
import requests

# Using Ollama
def categorize_email(subject, sender, preview):
    response = requests.post('http://localhost:11434/api/generate', json={{
        "model": "bensley-email-assistant",
        "prompt": f"Categorize this email:\\n\\nSubject: {{subject}}\\nFrom: {{sender}}\\nPreview: {{preview}}",
        "stream": False
    }})
    return json.loads(response.json()['response'])

# Test
result = categorize_email(
    "Re: Fee proposal for XXX-24-05",
    "client@hotel.com",
    "Thanks for the proposal. Can we schedule a call to discuss..."
)
print(result)
```

## Integration with Backend

Replace Claude API calls in `backend/services/ai_service.py`:

```python
class AIService:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "bensley-email-assistant"

    async def categorize_email(self, subject, sender, body):
        # Use local model instead of Claude
        response = requests.post(self.ollama_url, json={{
            "model": self.model,
            "prompt": f"Categorize this email:\\n\\nSubject: {{subject}}\\nFrom: {{sender}}\\nPreview: {{body[:500]}}",
            "stream": False
        }})
        return json.loads(response.json()['response'])
```

## Performance Expectations

- **Speed**: 2-5 seconds per email (vs 0.5s for Claude API)
- **Cost**: $0 (vs ~$0.01 per email with Claude)
- **Accuracy**: Should match Claude after 200+ human-verified examples
- **Privacy**: All data stays local, no external API calls

## Next Steps

1. Add more human-verified examples (run `manual_training_feedback.py`)
2. Re-export training data (run `export_training_data.py`)
3. Re-train model with improved data
4. Evaluate accuracy (run `test_model.py`)
5. Deploy to production once accuracy > 90%
"""

    readme_path = f"{MODEL_OUTPUT_DIR}/README.md"
    with open(readme_path, "w") as f:
        f.write(readme)
    print(f"✓ Saved README: {readme_path}")

    return {
        "jsonl": jsonl_path,
        "axolotl": axolotl_path,
        "system_prompt": system_prompt_path,
        "readme": readme_path
    }

def main():
    print("="*80)
    print("BENSLEY INTELLIGENCE - MODEL FINE-TUNING PREPARATION")
    print("="*80)
    print("\nThis script prepares your training data for local model fine-tuning.")
    print("It creates datasets compatible with Ollama, Axolotl, and LM Studio.\n")

    # Load training data
    business_context, human_examples, ai_examples, prompt_templates = load_training_data()

    # Check if we have enough data
    if len(human_examples) == 0:
        print("\n" + "="*80)
        print("⚠️  WARNING: NO HUMAN-VERIFIED EXAMPLES FOUND")
        print("="*80)
        print("\nYour model will train on AI-generated data only.")
        print("This may result in lower accuracy and reinforcement of AI mistakes.\n")
        print("RECOMMENDATION:")
        print("1. Run manual_training_feedback.py to add human examples")
        print("2. Verify 50-100 emails (takes 10-15 minutes)")
        print("3. Re-run export_training_data.py")
        print("4. Then run this script again\n")

        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Aborted. Please add human examples first.")
            return

    # Format training data
    formatted_examples, system_prompt = format_training_examples(
        business_context, human_examples, ai_examples
    )

    # Save for fine-tuning
    output_files = save_for_fine_tuning(formatted_examples, system_prompt)

    # Summary
    print("\n" + "="*80)
    print("PREPARATION COMPLETE")
    print("="*80)
    print(f"\nTraining files created in: {MODEL_OUTPUT_DIR}")
    print("\nQuick Start Options:")
    print("\n1. EASIEST - Ollama with custom system prompt (no training needed):")
    print("   brew install ollama")
    print("   ollama pull mistral")
    print("   # See README.md for Modelfile setup")

    print("\n2. BEST QUALITY - Fine-tune with Axolotl:")
    print("   pip install axolotl")
    print(f"   accelerate launch -m axolotl.cli.train {output_files['axolotl']}")

    print("\n3. GUI OPTION - Use LM Studio:")
    print("   Download from https://lmstudio.ai/")
    print(f"   Import {output_files['jsonl']}")

    print("\n📖 Full instructions: " + output_files['readme'])
    print("\n")

if __name__ == "__main__":
    main()
