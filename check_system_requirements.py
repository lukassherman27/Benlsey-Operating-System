#!/usr/bin/env python3
"""
System Requirements Checker for Local Model Training
Analyzes hardware and recommends appropriate model size
"""

import subprocess
import sys
import platform
import psutil
import os

def get_system_info():
    """Gather system information"""
    info = {
        "platform": platform.system(),
        "machine": platform.machine(),
        "ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "cpu_count": psutil.cpu_count(logical=True),
        "cpu_physical": psutil.cpu_count(logical=False),
    }

    # Check for GPU (macOS Metal)
    if info["platform"] == "Darwin":
        try:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True,
                text=True
            )
            if "Metal" in result.stdout:
                info["gpu"] = "Apple Silicon (Metal)"
                info["gpu_support"] = True
            else:
                info["gpu"] = "None"
                info["gpu_support"] = False
        except:
            info["gpu"] = "Unknown"
            info["gpu_support"] = False

    return info

def recommend_model(system_info):
    """Recommend model based on system capabilities"""
    ram_gb = system_info["ram_gb"]

    recommendations = []

    print("\n" + "="*80)
    print("SYSTEM ANALYSIS")
    print("="*80)
    print(f"Platform: {system_info['platform']} ({system_info['machine']})")
    print(f"RAM: {ram_gb} GB")
    print(f"CPU: {system_info['cpu_physical']} physical cores ({system_info['cpu_count']} logical)")
    print(f"GPU: {system_info.get('gpu', 'Not detected')}")

    print("\n" + "="*80)
    print("MODEL RECOMMENDATIONS")
    print("="*80)

    # Recommendations based on RAM
    if ram_gb >= 64:
        print("\n✓ EXCELLENT - You can run larger models!")
        recommendations.append({
            "model": "Mistral-7B-Instruct",
            "size": "7B parameters",
            "ram_needed": "16-24 GB",
            "quality": "Excellent for business tasks",
            "speed": "Fast",
            "recommended": True
        })
        recommendations.append({
            "model": "LLaMA-3-8B-Instruct",
            "size": "8B parameters",
            "ram_needed": "20-28 GB",
            "quality": "High quality, good reasoning",
            "speed": "Fast",
            "recommended": True
        })
    elif ram_gb >= 32:
        print("\n✓ GOOD - Mid-size models will work well")
        recommendations.append({
            "model": "Mistral-7B-Instruct",
            "size": "7B parameters",
            "ram_needed": "16-24 GB",
            "quality": "Excellent for business tasks",
            "speed": "Fast",
            "recommended": True
        })
        recommendations.append({
            "model": "Phi-3-mini",
            "size": "3.8B parameters",
            "ram_needed": "8-12 GB",
            "quality": "Good for classification",
            "speed": "Very fast",
            "recommended": False
        })
    elif ram_gb >= 16:
        print("\n⚠️  LIMITED - Smaller models recommended")
        recommendations.append({
            "model": "Phi-3-mini",
            "size": "3.8B parameters",
            "ram_needed": "8-12 GB",
            "quality": "Good for classification",
            "speed": "Very fast",
            "recommended": True
        })
        recommendations.append({
            "model": "TinyLlama-1.1B",
            "size": "1.1B parameters",
            "ram_needed": "4-6 GB",
            "quality": "Basic classification only",
            "speed": "Extremely fast",
            "recommended": False
        })
    else:
        print("\n✗ INSUFFICIENT - 16GB+ RAM recommended for local models")
        print("Consider using API-based solutions instead")
        return []

    # Display recommendations
    for i, rec in enumerate(recommendations, 1):
        status = "★ RECOMMENDED" if rec["recommended"] else "  Alternative"
        print(f"\n{status} Option {i}: {rec['model']}")
        print(f"  Size: {rec['size']}")
        print(f"  RAM needed: {rec['ram_needed']}")
        print(f"  Quality: {rec['quality']}")
        print(f"  Speed: {rec['speed']}")

    return recommendations

def check_dependencies():
    """Check if required tools are installed"""
    print("\n" + "="*80)
    print("DEPENDENCY CHECK")
    print("="*80)

    dependencies = {
        "python3": "Python 3.8+",
        "git": "Git for downloading models",
    }

    missing = []
    for cmd, description in dependencies.items():
        try:
            result = subprocess.run([cmd, "--version"], capture_output=True)
            if result.returncode == 0:
                print(f"✓ {description}")
            else:
                print(f"✗ {description} - NOT FOUND")
                missing.append(cmd)
        except:
            print(f"✗ {description} - NOT FOUND")
            missing.append(cmd)

    # Check Python packages
    print("\nPython Packages:")
    required_packages = ["torch", "transformers", "datasets", "peft", "bitsandbytes"]

    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - NOT INSTALLED")
            missing.append(package)

    if missing:
        print("\n" + "="*80)
        print("INSTALLATION NEEDED")
        print("="*80)
        print("\nRun these commands to install missing dependencies:")
        if any(pkg in missing for pkg in required_packages):
            print("\npip3 install torch transformers datasets peft bitsandbytes accelerate")

    return len(missing) == 0

def recommend_training_approach(system_info):
    """Recommend training approach based on system"""
    print("\n" + "="*80)
    print("TRAINING APPROACH RECOMMENDATIONS")
    print("="*80)

    ram_gb = system_info["ram_gb"]

    if ram_gb >= 32:
        print("\n✓ FULL FINE-TUNING (Recommended)")
        print("  • Use LoRA (Low-Rank Adaptation) for efficient training")
        print("  • Training time: 2-4 hours for 200-300 examples")
        print("  • Quality: Best results")
        print("  • Tool: Axolotl or HuggingFace Trainer")

        print("\n✓ PROMPT ENGINEERING (Alternative)")
        print("  • Use business_context.json as system prompt")
        print("  • No training needed, instant deployment")
        print("  • Quality: Good, but less specialized")
        print("  • Tool: llama.cpp or Ollama")
    else:
        print("\n✓ PROMPT ENGINEERING (Recommended)")
        print("  • Use business_context.json as system prompt")
        print("  • No training needed, instant deployment")
        print("  • Quality: Good for classification tasks")
        print("  • Tool: llama.cpp or Ollama")

        print("\n⚠️  FINE-TUNING (May be slow)")
        print("  • Limited by RAM, may need to use smaller models")
        print("  • Training time: 4-8 hours")
        print("  • Quality: Better than prompt engineering")

def main():
    print("="*80)
    print("BENSLEY INTELLIGENCE - LOCAL MODEL SYSTEM CHECK")
    print("="*80)

    # Get system info
    system_info = get_system_info()

    # Recommend model
    recommendations = recommend_model(system_info)

    # Check dependencies
    all_deps_installed = check_dependencies()

    # Recommend training approach
    recommend_training_approach(system_info)

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)

    if recommendations:
        print("\n1. Install dependencies (if needed)")
        print("2. Choose a model from recommendations above")
        print("3. Run setup_local_model.py to download and configure")
        print("4. Run fine_tune_model.py to train on your data")
        print("5. Run test_model.py to evaluate accuracy")

        print("\n📚 Quick Start (using Ollama - easiest):")
        print("   brew install ollama")
        print("   ollama pull mistral")
        print("   python3 local_model_inference.py")
    else:
        print("\n⚠️  Your system may not meet minimum requirements")
        print("Consider using cloud-based training or API solutions")

    print("\n")

if __name__ == "__main__":
    main()
