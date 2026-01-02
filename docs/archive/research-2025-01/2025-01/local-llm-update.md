# Local LLM Updates Research (Ollama, llama.cpp)

**Date:** 2025-12-30
**Researcher:** Agent 5 (Research Agent)
**Issue:** #205 (Ongoing Research)

---

## Summary

Researched the current state of local LLM deployment via Ollama and llama.cpp. Local LLMs have improved dramatically - open models like DeepSeek R1, Qwen 3, and Llama 3.1 now approach GPT-4 capabilities. However, **for Bensley's current scale, cloud APIs remain more cost-effective**. Local deployment makes sense only at high volume (1M+ tokens/day) or if data privacy becomes a hard requirement.

**TL;DR:** Stay with GPT-4o-mini for now. Revisit local LLMs when monthly API costs exceed $500-1,000 consistently, or when processing sensitive client data.

---

## Key Findings

### 1. Ollama 2025 Major Updates

**Platform Evolution:**
- Native desktop apps for macOS and Windows (July 2025)
- Ollama Turbo: Cloud service at $20/month
- Support for multimodal models (vision, speech, image generation)

**Technical Improvements:**
- Vulkan acceleration for AMD/Intel GPUs
- INT4 and INT2 quantization (extreme compression)
- Streaming tool responses for better UX
- Log probabilities support in API
- OpenAI-compatible API endpoint

**New Models Available:**
| Model | Parameters | Specialty |
|-------|-----------|-----------|
| DeepSeek-R1 | 1.5B-671B | Reasoning, approaching O3/Gemini 2.5 Pro |
| Qwen3 | 0.6B-235B | Dense & MoE, flexible sizing |
| Llama 3.1 | 8B-405B | General purpose, Meta's flagship |
| Qwen2.5-Coder | 0.5B-32B | Code generation & reasoning |
| Command-R-Plus | 104B | Enterprise use cases |
| Gemma3 | 270M-27B | Runs on single GPU efficiently |

### 2. llama.cpp Performance on Apple Silicon

**Current Status:**
- Apple Silicon is a "first-class citizen"
- Optimized via ARM NEON, Accelerate, Metal frameworks
- December 2025 releases include dedicated macOS ARM64 builds

**Performance Benchmarks (Apple Silicon):**
| Framework | Throughput |
|-----------|-----------|
| MLX | ~230 tok/s |
| MLC-LLM | ~190 tok/s |
| llama.cpp | ~150 tok/s |
| Ollama | 20-40 tok/s |
| PyTorch MPS | ~7-9 tok/s |

**Hardware Sweet Spots:**
- M2 Pro/Max: Great for 8B models (coding assistants, RAG)
- M2 Ultra (96GB): Can run 70B models with aggressive quantization
- Multi-Mac clusters: Possible but inefficient (diminishing returns)

### 3. Cost Comparison: Cloud vs Local

**Bensley Current State:**
- Using GPT-4o-mini at $0.15/1M input, $0.60/1M output tokens
- This is among the cheapest cloud options

**Cloud API Pricing (2025):**
| Provider | Model | Input/1M | Output/1M |
|----------|-------|----------|-----------|
| OpenAI | GPT-4o-mini | $0.15 | $0.60 |
| OpenAI | GPT-4.1 | $3-12 | $15-75 |
| Anthropic | Claude Haiku | $0.25 | $1.25 |
| Anthropic | Claude Opus 4 | $15 | $75 |
| Google | Gemini 2.5 Pro | $1.25-2.50 | $10-15 |

**Local Hardware Costs:**
| Hardware | Price | VRAM | Model Support |
|----------|-------|------|---------------|
| RTX 4090 | $1,600-1,800 | 24GB | 13B-30B models |
| RTX 4060 Ti | $500-700 | 16GB | 7B-13B models |
| Mac Mini M4 Pro | $1,999 | 24GB | 8B-13B models |
| Mac Studio M2 Ultra | $3,999+ | 192GB | Up to 70B |

**Break-Even Analysis:**
- $1,800 GPU pays for itself at ~$150/month API spend
- Break-even: ~12 months at moderate usage
- Real savings only if processing 1M+ tokens/day consistently

### 4. Bensley-Specific Assessment

**Current API Usage (estimated):**
- Email analysis: GPT-4o-mini
- ~100 emails/run × multiple runs/day
- Token usage likely $20-100/month range

**Would Local Make Sense?**

| Factor | Assessment |
|--------|------------|
| Cost | ❌ Not at current scale |
| Privacy | ✅ Would keep client data local |
| Performance | ⚠️ Comparable for simple tasks |
| Maintenance | ❌ Additional ops burden |
| Reliability | ❌ Cloud APIs more reliable |

---

## Pros of Local LLMs

1. **Data Privacy** - Client emails never leave premises
2. **No Rate Limits** - Process unlimited without throttling
3. **Predictable Costs** - Hardware cost, not per-token
4. **Offline Capability** - Works without internet
5. **Customization** - Fine-tune on Bensley data

---

## Cons of Local LLMs (For Bensley Now)

1. **Upfront Cost** - $1,600-4,000 for capable hardware
2. **Maintenance** - Model updates, GPU drivers, troubleshooting
3. **Quality Gap** - GPT-4o-mini still beats most local 8B models
4. **Ops Burden** - Another system to manage
5. **Not Cost-Effective** - At current email volume, cloud is cheaper

---

## Recommendation

**NOT RECOMMENDED NOW** - Revisit in Phase 4

**Reasoning:**
1. GPT-4o-mini is extremely cheap ($0.15-0.60/1M tokens)
2. Current email volume doesn't justify hardware investment
3. Local LLMs add ops complexity
4. Quality of GPT-4o-mini is good enough for email analysis

**When to Reconsider:**

| Trigger | Action |
|---------|--------|
| API costs > $500/month consistently | Evaluate local deployment |
| Privacy requirement (regulated clients) | Deploy local for sensitive data |
| Processing 1M+ tokens/day | Break-even achieved faster |
| Claude Code + MCP (from Week 1) | Could replace GPT for analysis |

---

## Alternative Recommendation: Hybrid Approach (Future)

If considering local later, use a hybrid strategy:

```
Simple tasks (email routing, categorization) → Local Llama 8B
Complex tasks (proposal analysis, context-aware) → GPT-4o-mini/Claude
```

This optimizes cost while maintaining quality for important decisions.

---

## Implementation Estimate (If Needed)

If Bensley wanted local LLMs in Phase 4:

| Metric | Value |
|--------|-------|
| Hardware Cost | $1,600-2,000 (RTX 4090) |
| Setup Time | 1-2 days |
| Complexity | Medium |
| Ongoing Maintenance | 2-4 hours/month |

### Quick Start (If Needed)
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download model
ollama pull llama3.1:8b

# Run local API
ollama serve

# Use in Python
import requests
response = requests.post('http://localhost:11434/api/generate',
    json={'model': 'llama3.1:8b', 'prompt': 'Analyze this email...'})
```

---

## Phase 4 Timeline Adjustment

Based on this research, local LLM deployment should remain in Phase 4 (H2 2025) but with modified triggers:

**Original Plan:** "Implement local LLMs"
**Updated Plan:** "Implement local LLMs IF API costs justify OR privacy required"

Key decision points:
1. Monitor monthly API spend
2. Check if any clients require on-premise data processing
3. Evaluate Claude MCP (Week 1) as potential replacement for GPT

---

## References

- [Ollama Official Site](https://ollama.com/)
- [Ollama Model Library](https://ollama.com/library)
- [Ollama 2025 Updates - Infralovers](https://www.infralovers.com/blog/2025-08-13-ollama-2025-updates/)
- [Best Ollama Models 2025 - Collabnix](https://collabnix.com/best-ollama-models-in-2025-complete-performance-comparison/)
- [llama.cpp GitHub](https://github.com/ggml-org/llama.cpp)
- [llama.cpp Apple Silicon Performance Discussion](https://github.com/ggml-org/llama.cpp/discussions/4167)
- [LLM API Pricing Comparison 2025 - IntuitionLabs](https://intuitionlabs.ai/articles/llm-api-pricing-comparison-2025)
- [Local LLM vs Cloud APIs - Scand](https://scand.com/company/blog/local-llms-vs-chatgpt-cost-comparison/)
- [Local LLM Hosting 2025 Guide - Medium](https://medium.com/@rosgluk/local-llm-hosting-complete-2025-guide-ollama-vllm-localai-jan-lm-studio-more-f98136ce7e4a)

---

## Appendix: Model Comparison for Email Analysis

If deploying locally, these models would be suitable for Bensley's email analysis:

| Model | Size | Speed | Quality | RAM Needed |
|-------|------|-------|---------|------------|
| Llama 3.1 8B | 8B | Fast | Good | 8GB |
| Qwen3 14B | 14B | Medium | Very Good | 16GB |
| DeepSeek-R1 7B | 7B | Fast | Good | 8GB |
| Gemma3 9B | 9B | Fast | Good | 10GB |

**Recommendation for Bensley (if local):** Llama 3.1 8B - good balance of speed, quality, and resource usage.
