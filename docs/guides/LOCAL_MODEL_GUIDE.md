# Bensley Intelligence - Local Model Training Guide

Complete guide to training and deploying your own local AI model for email categorization.

## Why Local Models?

**Benefits:**
- **Zero ongoing costs** - No API fees ($0 vs ~$0.01/email with Claude)
- **Complete privacy** - All data stays on your machine
- **Customization** - Model learns YOUR business patterns
- **Speed** - No internet required, works offline
- **Control** - You own the model, no vendor lock-in

**Trade-offs:**
- Initial setup time (2-4 hours)
- Requires human training data (10-15 min/day for a week)
- Slower inference (2-5s vs 0.5s for Claude)
- Needs decent hardware (16GB+ RAM recommended)

---

## Complete Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: HUMAN TRAINING DATA COLLECTION (Week 1)            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Review emails manually (10-15 min/day)                  │
│     → python3 manual_training_feedback.py                   │
│                                                              │
│  2. Correct AI categorizations                              │
│     → Add notes about business context                      │
│     → Build 200-300 human-verified examples                 │
│                                                              │
│  Goal: High-quality training data from YOUR expertise       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: EXPORT & PREPARE (5 minutes)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  3. Export training data                                    │
│     → python3 export_training_data.py                       │
│                                                              │
│  4. Prepare fine-tuning files                               │
│     → python3 fine_tune_model.py                            │
│                                                              │
│  Output: JSONL files + configs for training                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: TRAIN MODEL (2-4 hours, automated)                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Choose ONE approach:                                       │
│                                                              │
│  Option A: Ollama (Easiest - No training needed)            │
│     → brew install ollama                                   │
│     → ollama pull mistral                                   │
│     → Uses system prompt with business context              │
│                                                              │
│  Option B: LM Studio (GUI - Easy)                           │
│     → Download LM Studio                                    │
│     → Import training data                                  │
│     → Click "Fine-tune" and wait                            │
│                                                              │
│  Option C: Axolotl (Advanced - Best results)                │
│     → pip install axolotl                                   │
│     → accelerate launch -m axolotl.cli.train config.yml    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: TEST & DEPLOY (1 hour)                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  5. Test model accuracy                                     │
│     → python3 local_model_inference.py compare              │
│                                                              │
│  6. If accuracy > 90%, deploy to production                 │
│     → Update backend/services/ai_service.py                 │
│     → Replace Claude API with local model                   │
│                                                              │
│  7. Monitor and improve                                     │
│     → Continue adding human feedback                        │
│     → Re-train monthly with new data                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Instructions

### STEP 1: Check System Requirements

```bash
python3 check_system_requirements.py
```

**This will:**
- Analyze your hardware (RAM, CPU, GPU)
- Recommend appropriate model sizes
- Check if dependencies are installed
- Suggest best training approach

**Minimum Requirements:**
- 16GB RAM (32GB+ recommended)
- 50GB free disk space
- macOS, Linux, or Windows

---

### STEP 2: Collect Human Training Data

**Why this matters:** The model learns from YOUR corrections. Each time you correct an AI mistake, the model gets smarter about YOUR business.

```bash
python3 manual_training_feedback.py
```

**Workflow:**
1. Tool shows you emails one by one
2. You categorize each email (takes 10-20 seconds)
3. Add notes about WHY you chose that category
4. Your corrections are saved to training database

**Daily commitment:**
- 10-15 minutes per day
- Review 30-50 emails per session
- Do this for 5-7 days
- Goal: 200-300 human-verified examples

**Tips:**
- Focus on emails where AI got it wrong
- Add notes about project context
- Explain industry-specific terms
- Mention key people/companies

**Example session:**
```
EMAIL ID: 42
FROM: client@resort.com
SUBJECT: Re: Fee proposal for MAL-24-02
PREVIEW: Thanks for the $2.5M proposal. Can we discuss...

CURRENT: general/none (confidence: 60%)

CATEGORIES:
  [1] proposal  [2] meeting  [3] contract
  [4] project_update  [5] schedule  ...

Select category: 1
Select subcategory:
  [1] initial  [2] follow_up  [3] revision  [4] won  [5] lost

Select subcategory: 2

Notes: Client responding positively to proposal, wants to meet.
       Project MAL-24-02 is Maldives resort - high value client.

✓ Saved and added to training data
```

---

### STEP 3: Export Training Data

After you've collected 100+ human examples:

```bash
python3 export_training_data.py
```

**Output location:**
`~/Desktop/BDS_SYSTEM/TRAINING_DATA/`

**Files created:**
- `business_context.json` - Company info, projects, patterns
- `human_verified_examples.json` - YOUR corrections (gold standard)
- `high_quality_ai_examples.json` - Supplement data
- `training_prompts.json` - Prompt templates

---

### STEP 4: Prepare Fine-Tuning

```bash
python3 fine_tune_model.py
```

**This creates:**
- `training_data.jsonl` - Training dataset
- `axolotl_config.yml` - Config for training
- `system_prompt.txt` - Business context prompt
- `README.md` - Instructions

**Output location:**
`~/Desktop/BDS_SYSTEM/LOCAL_MODELS/`

---

### STEP 5: Choose Your Training Path

#### OPTION A: Ollama (Recommended for Beginners)

**Pros:** Easiest, works immediately, no training needed
**Cons:** Slightly lower accuracy than fine-tuned models

```bash
# Install Ollama
brew install ollama

# Start Ollama server
ollama serve

# Download base model (in new terminal)
ollama pull mistral

# Create custom model with business context
cd ~/Desktop/BDS_SYSTEM/LOCAL_MODELS/
cat > Modelfile <<EOF
FROM mistral
SYSTEM "$(cat system_prompt.txt)"
EOF

# Build custom model
ollama create bensley-email-assistant -f Modelfile

# Test it
ollama run bensley-email-assistant "Categorize this email: Subject: Fee proposal for resort project..."
```

**Test the model:**
```bash
python3 local_model_inference.py test
```

**Process emails:**
```bash
python3 local_model_inference.py process 50
```

**Compare with Claude:**
```bash
python3 local_model_inference.py compare
```

---

#### OPTION B: LM Studio (Recommended for GUI Users)

**Pros:** Easy GUI, visual training progress, good results
**Cons:** Slower than command line, less control

1. **Download LM Studio:**
   - Visit: https://lmstudio.ai/
   - Download for macOS
   - Install and open

2. **Download base model:**
   - Click "Search" tab
   - Search for "Mistral-7B-Instruct"
   - Download the GGUF version

3. **Import training data:**
   - Click "Fine-tune" tab
   - Import `~/Desktop/BDS_SYSTEM/LOCAL_MODELS/training_data.jsonl`
   - Select Mistral-7B as base model

4. **Configure training:**
   - Epochs: 3
   - Learning rate: 0.0002
   - Batch size: 2-4 (depending on RAM)

5. **Start training:**
   - Click "Start Fine-tuning"
   - Wait 2-4 hours
   - Model will be saved automatically

6. **Test the model:**
   - Click "Chat" tab
   - Select your fine-tuned model
   - Paste system_prompt.txt into system prompt
   - Test with sample emails

---

#### OPTION C: Axolotl (Recommended for Best Results)

**Pros:** Best quality, most control, industry standard
**Cons:** Requires technical knowledge, command line only

```bash
# Install dependencies
pip install axolotl torch transformers datasets peft bitsandbytes accelerate

# Navigate to models directory
cd ~/Desktop/BDS_SYSTEM/LOCAL_MODELS/

# Start training (2-4 hours)
accelerate launch -m axolotl.cli.train axolotl_config.yml

# Monitor progress
# You'll see training loss decreasing
# Target: loss < 0.5 for good results

# After training, model is in: bensley-email-assistant/
```

**Training output:**
```
Step 1/300: loss=2.145
Step 50/300: loss=1.234
Step 100/300: loss=0.876
Step 150/300: loss=0.654
Step 200/300: loss=0.543
Step 250/300: loss=0.489
Step 300/300: loss=0.432 ✓

Training complete! Model saved to: bensley-email-assistant/
```

---

### STEP 6: Test Model Accuracy

```bash
# Test with sample email
python3 local_model_inference.py test

# Compare with Claude's categorizations
python3 local_model_inference.py compare
```

**Target accuracy:** >90% match with Claude

**If accuracy < 90%:**
1. Add more human-verified examples
2. Re-export training data
3. Re-train model
4. Test again

**If accuracy >= 90%:**
→ Ready for production deployment!

---

### STEP 7: Deploy to Production

Update `backend/services/ai_service.py` to use local model:

```python
from local_model_inference import LocalModelService

class AIService:
    def __init__(self, use_local_model: bool = True):
        if use_local_model:
            self.model = LocalModelService()
            self.use_local = True
        else:
            self.anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            self.use_local = False

    async def categorize_email(self, subject: str, sender: str, body: str):
        if self.use_local:
            # Use local model
            return self.model.categorize_email(subject, sender, body)
        else:
            # Use Claude API (fallback)
            # ... existing code ...
```

**Environment variable for switching:**
```bash
# .env file
USE_LOCAL_MODEL=true   # Use local model
USE_LOCAL_MODEL=false  # Use Claude API (fallback)
```

---

## Ongoing Improvement

### Monthly Re-training

As you continue to use the system, the model improves:

```bash
# Every month:
1. Review new emails with manual_training_feedback.py (10-15 min)
2. Export updated training data
3. Re-train model with new examples
4. Deploy updated model
```

**Improvement over time:**
```
Month 1: 200 examples  → 88% accuracy
Month 2: 350 examples  → 92% accuracy
Month 3: 500 examples  → 95% accuracy
Month 6: 1000 examples → 98% accuracy
```

---

## Cost Comparison

### Current System (Claude API)

- **Cost per email:** ~$0.01
- **Monthly volume:** 500 emails
- **Monthly cost:** $5
- **Annual cost:** $60

### Local Model

- **Training time:** 4 hours (one-time)
- **Cost per email:** $0
- **Monthly cost:** $0
- **Annual cost:** $0

**Break-even:** Immediate (after first month)
**Annual savings:** $60/year + data privacy + full control

---

## Troubleshooting

### "Ollama connection failed"
```bash
# Start Ollama server
ollama serve

# In new terminal, test
ollama list
```

### "Model returns invalid JSON"
- This means model needs more training
- Add more human-verified examples
- Make sure examples show correct JSON format

### "Out of memory error"
- Use smaller model (Phi-3-mini instead of Mistral-7B)
- Reduce batch size in config
- Close other applications

### "Training is very slow"
- Normal for first run
- Expected: 2-4 hours for 200 examples
- Use GPU if available (much faster)

### "Accuracy is low (<70%)"
- Need more human-verified examples
- Current AI examples might be poor quality
- Review and correct more emails manually

---

## Quick Reference

```bash
# Check system
python3 check_system_requirements.py

# Add human training data (daily)
python3 manual_training_feedback.py

# Export training data (after 100+ examples)
python3 export_training_data.py

# Prepare fine-tuning
python3 fine_tune_model.py

# Install Ollama (easiest option)
brew install ollama
ollama pull mistral
# Create custom model (see OPTION A above)

# Test local model
python3 local_model_inference.py test

# Compare accuracy
python3 local_model_inference.py compare

# Process emails with local model
python3 local_model_inference.py process 50
```

---

## Next Steps

1. **Run system check:**
   ```bash
   python3 check_system_requirements.py
   ```

2. **Start collecting human data (TODAY):**
   ```bash
   python3 manual_training_feedback.py
   ```
   → Spend 10-15 minutes reviewing emails

3. **Continue for 5-7 days** until you have 200+ examples

4. **Then export and train:**
   ```bash
   python3 export_training_data.py
   python3 fine_tune_model.py
   ```

5. **Choose training path** (Ollama recommended for beginners)

6. **Test and deploy**

---

## Support

**Documentation:**
- Ollama: https://ollama.ai/
- Axolotl: https://github.com/OpenAccess-AI-Collective/axolotl
- LM Studio: https://lmstudio.ai/docs

**Need help?** Review the README files in:
- `~/Desktop/BDS_SYSTEM/TRAINING_DATA/README.md`
- `~/Desktop/BDS_SYSTEM/LOCAL_MODELS/README.md`
