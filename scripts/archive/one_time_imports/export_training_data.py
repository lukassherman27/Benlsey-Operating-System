#!/usr/bin/env python3
"""
Export Training Data for Local Model
Creates comprehensive training dataset with business context
"""

import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
OUTPUT_DIR = "/Users/lukassherman/Desktop/BDS_SYSTEM/TRAINING_DATA"

def export_business_context():
    """Export business knowledge for model training"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    context = {
        "company": {
            "name": "Bensley Design Studios",
            "business_type": "Luxury hospitality design and architecture",
            "focus": "High-end resorts, hotels, branded residences in Asia-Pacific",
            "key_people": ["Bill Bensley", "Brian", "Lukas"],
            "locations": ["Bali", "China", "India", "Singapore", "Maldives", "Thailand"]
        },
        "projects": [],
        "clients": [],
        "email_patterns": [],
        "common_terms": []
    }

    # Get active projects
    cursor.execute("""
        SELECT project_code, project_name, client_company, total_fee_usd, status
        FROM proposals
        WHERE is_active_project = 1
        ORDER BY project_code
    """)

    for row in cursor.fetchall():
        context["projects"].append({
            "code": row[0],
            "name": row[1],
            "client": row[2],
            "value": row[3],
            "status": row[4]
        })

    # Get unique clients
    cursor.execute("""
        SELECT DISTINCT client_company
        FROM proposals
        WHERE client_company IS NOT NULL
        ORDER BY client_company
    """)
    context["clients"] = [row[0] for row in cursor.fetchall()]

    # Get email patterns
    cursor.execute("""
        SELECT category, subcategory, COUNT(*) as count,
               GROUP_CONCAT(DISTINCT sender_email) as senders
        FROM email_content ec
        JOIN emails e ON ec.email_id = e.email_id
        WHERE category IS NOT NULL
        GROUP BY category, subcategory
        ORDER BY count DESC
    """)

    for row in cursor.fetchall():
        context["email_patterns"].append({
            "category": row[0],
            "subcategory": row[1],
            "count": row[2],
            "common_senders": row[3].split(',')[:5] if row[3] else []
        })

    # Common terms/keywords
    cursor.execute("""
        SELECT DISTINCT
            LOWER(SUBSTR(subject, 1, 50)) as subject_start
        FROM emails
        WHERE subject IS NOT NULL
        LIMIT 100
    """)
    context["common_terms"] = [row[0] for row in cursor.fetchall()]

    conn.close()
    return context

def export_human_verified_examples():
    """Export all human-verified training examples"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT task_type, input_data, output_data, feedback, created_at
        FROM training_data
        WHERE human_verified = 1
        ORDER BY created_at DESC
    """)

    examples = []
    for row in cursor.fetchall():
        try:
            input_data = json.loads(row[1]) if row[1] else {}
            output_data = json.loads(row[2]) if row[2] else {}
            examples.append({
                "task": row[0],
                "input": input_data,
                "output": output_data,
                "feedback": row[3],
                "date": row[4]
            })
        except json.JSONDecodeError:
            # Skip invalid JSON
            continue

    conn.close()
    return examples

def export_high_quality_ai_examples():
    """Export AI examples with high confidence"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            e.subject,
            e.sender_email,
            e.body_preview,
            ec.category,
            ec.subcategory,
            ec.ai_summary,
            ec.importance_score
        FROM emails e
        JOIN email_content ec ON e.email_id = ec.email_id
        WHERE ec.importance_score >= 0.85
          AND ec.category IS NOT NULL
        ORDER BY ec.importance_score DESC
        LIMIT 500
    """)

    examples = []
    for row in cursor.fetchall():
        if not row[2]:  # Skip if no body preview
            continue
        examples.append({
            "input": {
                "subject": row[0] or "",
                "sender": row[1] or "",
                "preview": row[2][:500] if row[2] else ""
            },
            "output": {
                "category": row[3],
                "subcategory": row[4],
                "summary": row[5] or ""
            },
            "confidence": row[6]
        })

    conn.close()
    return examples

def create_training_prompts():
    """Create example prompts for local model training"""
    return [
        {
            "prompt": "You are an email classification assistant for Bensley Design Studios, a luxury hospitality design firm. Categorize the following email:",
            "categories": ["proposal", "meeting", "contract", "project_update", "schedule", "design", "rfi", "invoice", "general"],
            "instructions": "Analyze the email subject, sender, and content. Return the category, subcategory, importance (0-1), and a brief summary."
        },
        {
            "prompt": "Extract key information from this project email for Bensley Design Studios:",
            "extract": ["project_code", "client_name", "deadline", "action_items", "people_mentioned", "financial_info"],
            "instructions": "Identify and extract structured data from the email content."
        },
        {
            "prompt": "Summarize this email in the context of ongoing Bensley projects:",
            "context": "Include: who sent it, what they want, urgency level, and recommended action",
            "instructions": "Create a concise 2-3 sentence summary suitable for an executive briefing."
        }
    ]

def main():
    print("="*80)
    print("EXPORTING TRAINING DATA FOR LOCAL MODEL")
    print("="*80)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Export business context
    print("\n1. Exporting business context...")
    context = export_business_context()
    with open(f"{OUTPUT_DIR}/business_context.json", "w") as f:
        json.dump(context, f, indent=2)
    print(f"   ✓ Saved {len(context['projects'])} projects, {len(context['clients'])} clients")

    # Export human-verified examples
    print("\n2. Exporting human-verified examples...")
    human_examples = export_human_verified_examples()
    with open(f"{OUTPUT_DIR}/human_verified_examples.json", "w") as f:
        json.dump(human_examples, f, indent=2)
    print(f"   ✓ Saved {len(human_examples)} human-verified examples")

    # Export high-quality AI examples
    print("\n3. Exporting high-confidence AI examples...")
    ai_examples = export_high_quality_ai_examples()
    with open(f"{OUTPUT_DIR}/high_quality_ai_examples.json", "w") as f:
        json.dump(ai_examples, f, indent=2)
    print(f"   ✓ Saved {len(ai_examples)} high-confidence examples")

    # Create training prompts
    print("\n4. Creating training prompt templates...")
    prompts = create_training_prompts()
    with open(f"{OUTPUT_DIR}/training_prompts.json", "w") as f:
        json.dump(prompts, f, indent=2)
    print(f"   ✓ Saved {len(prompts)} prompt templates")

    # Create README
    readme = f"""# Bensley Intelligence Training Data
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Files

1. **business_context.json** - Company info, projects, clients, patterns
2. **human_verified_examples.json** - Gold standard examples (human-corrected)
3. **high_quality_ai_examples.json** - High-confidence AI examples (>85%)
4. **training_prompts.json** - Prompt templates for fine-tuning

## Training Recommendations

### For Local Model (e.g., LLaMA, Mistral):

1. **Fine-tune on human_verified_examples.json first** (highest quality)
2. **Use business_context.json as system prompt** (provides domain knowledge)
3. **Supplement with high_quality_ai_examples.json** (for scale)

### Training Format:

```python
{{
  "system": "You are an email assistant for Bensley Design Studios... [business_context]",
  "user": "Categorize this email: {{email_content}}",
  "assistant": "{{category}}, {{subcategory}}, {{summary}}"
}}
```

### Recommended Tools:
- **Llama.cpp** - For local inference
- **LM Studio** - GUI for fine-tuning
- **Axolotl** - Advanced fine-tuning framework

## Stats
- Projects: {len(context['projects'])}
- Human-verified: {len(human_examples)}
- High-quality AI: {len(ai_examples)}
- Total training examples: {len(human_examples) + len(ai_examples)}
"""

    with open(f"{OUTPUT_DIR}/README.md", "w") as f:
        f.write(readme)

    print("\n" + "="*80)
    print("EXPORT COMPLETE!")
    print("="*80)
    print(f"\nTraining data saved to: {OUTPUT_DIR}")
    print("\nNext steps:")
    print("1. Run manual_training_feedback.py to add more human examples")
    print("2. Use exported data to fine-tune your local model")
    print("3. Feed business_context.json as system prompt for better accuracy")
    print("\n")

if __name__ == "__main__":
    main()
