#!/usr/bin/env python3
"""
Export Claude Code Conversation History for LLM Training

This script extracts all conversation history from Claude Code's JSONL files
and formats them for local LLM fine-tuning.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


def find_agent_files(claude_dir: Path) -> List[Path]:
    """Find all agent conversation JSONL files"""
    projects_dir = claude_dir / "projects"
    agent_files = []

    if projects_dir.exists():
        # Find all agent-*.jsonl files in any project directory
        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir():
                agent_files.extend(project_dir.glob("agent-*.jsonl"))

    return sorted(agent_files)


def parse_jsonl_file(file_path: Path) -> List[Dict[str, Any]]:
    """Parse a JSONL file and return list of entries"""
    entries = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"Warning: Skipping malformed JSON in {file_path.name}: {e}")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return entries


def extract_conversations(entries: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Extract user/assistant message pairs from JSONL entries"""
    conversations = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        # Check if this is a message entry with the message field
        if 'message' in entry and isinstance(entry['message'], dict):
            msg = entry['message']
            role = msg.get('role', '')

            # Extract content from the message
            if 'content' in msg and isinstance(msg['content'], list):
                for content_block in msg['content']:
                    if isinstance(content_block, dict):
                        # Text content
                        if content_block.get('type') == 'text' and 'text' in content_block:
                            conversations.append({
                                'role': role,
                                'content': content_block['text'],
                                'session_id': entry.get('sessionId', ''),
                                'agent_id': entry.get('agentId', '')
                            })
                        # Tool use (optional - can include for context)
                        elif content_block.get('type') == 'tool_use':
                            tool_name = content_block.get('name', 'unknown')
                            tool_input = content_block.get('input', {})
                            conversations.append({
                                'role': 'assistant',
                                'content': f"[Tool: {tool_name}]\nInput: {json.dumps(tool_input, indent=2)[:500]}",
                                'session_id': entry.get('sessionId', ''),
                                'agent_id': entry.get('agentId', ''),
                                'is_tool_call': True
                            })

    return conversations


def format_for_training(conversations: List[Dict[str, str]], format_type: str = 'alpaca') -> List[Dict[str, str]]:
    """
    Format conversations for LLM training

    Supported formats:
    - alpaca: instruction/input/output format
    - sharegpt: multi-turn conversation format
    - raw: just the conversation pairs
    """
    formatted = []

    # Filter out tool calls for cleaner training data
    clean_conversations = [
        conv for conv in conversations
        if not conv.get('is_tool_call', False) and conv.get('role') in ['user', 'assistant']
    ]

    if format_type == 'alpaca':
        # Group consecutive user/assistant pairs
        i = 0
        while i < len(clean_conversations):
            if i + 1 < len(clean_conversations):
                if clean_conversations[i]['role'] == 'user' and clean_conversations[i + 1]['role'] == 'assistant':
                    formatted.append({
                        'instruction': clean_conversations[i]['content'],
                        'input': '',
                        'output': clean_conversations[i + 1]['content']
                    })
                    i += 2
                else:
                    i += 1
            else:
                i += 1

    elif format_type == 'sharegpt':
        # Multi-turn conversation format - group by session
        sessions = {}
        for conv in clean_conversations:
            session_id = conv.get('session_id', 'unknown')
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append({
                'from': 'human' if conv['role'] == 'user' else 'gpt',
                'value': conv['content']
            })

        # Create conversation objects for each session
        for session_id, messages in sessions.items():
            if messages:
                formatted.append({
                    'conversations': messages,
                    'session_id': session_id
                })

    elif format_type == 'raw':
        formatted = clean_conversations

    return formatted


def main():
    # Configuration
    claude_dir = Path.home() / ".claude"
    output_dir = Path("/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/training")
    output_dir.mkdir(exist_ok=True)

    print("=" * 80)
    print("Claude Code Conversation Export for LLM Training")
    print("=" * 80)
    print()

    # Find all agent files
    print("🔍 Finding conversation files...")
    agent_files = find_agent_files(claude_dir)
    print(f"   Found {len(agent_files)} conversation files")
    print()

    # Parse all conversations
    all_conversations = []
    total_entries = 0

    print("📖 Reading conversations...")
    for i, agent_file in enumerate(agent_files, 1):
        print(f"   [{i}/{len(agent_files)}] {agent_file.name}")
        entries = parse_jsonl_file(agent_file)
        total_entries += len(entries)
        conversations = extract_conversations(entries)
        all_conversations.extend(conversations)

    print()
    print(f"✅ Processed {total_entries} total entries")
    print(f"✅ Extracted {len(all_conversations)} conversation messages")
    print()

    # Export in multiple formats
    formats = ['alpaca', 'sharegpt', 'raw']

    print("💾 Exporting in multiple formats...")
    for fmt in formats:
        formatted_data = format_for_training(all_conversations, fmt)
        output_file = output_dir / f"bensley_conversations_{fmt}.jsonl"

        # Write JSONL format
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in formatted_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        file_size = output_file.stat().st_size / 1024  # KB
        print(f"   ✓ {fmt.upper()}: {output_file.name} ({file_size:.1f} KB, {len(formatted_data)} items)")

    # Also create a combined JSON version for easier inspection
    combined_output = output_dir / "bensley_conversations_combined.json"
    with open(combined_output, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'total_files': len(agent_files),
                'total_entries': total_entries,
                'total_conversations': len(all_conversations)
            },
            'conversations': all_conversations
        }, f, indent=2, ensure_ascii=False)

    file_size = combined_output.stat().st_size / 1024  # KB
    print(f"   ✓ COMBINED JSON: {combined_output.name} ({file_size:.1f} KB)")
    print()

    # Summary
    print("=" * 80)
    print("📊 Export Summary")
    print("=" * 80)
    print(f"Total conversation files processed: {len(agent_files)}")
    print(f"Total entries parsed: {total_entries}")
    print(f"Total messages extracted: {len(all_conversations)}")
    print()
    print(f"Output directory: {output_dir}")
    print()
    print("🎯 Next Steps:")
    print("   1. Review the exported files in the training/ directory")
    print("   2. Choose the format that works best for your LLM training pipeline:")
    print("      - alpaca: Good for instruction-following models")
    print("      - sharegpt: Good for multi-turn conversational models")
    print("      - raw: Keep all messages with metadata")
    print("   3. Use the JSONL files with your local LLM training framework")
    print("      (e.g., Llama-Factory, Axolotl, or custom training scripts)")
    print()


if __name__ == "__main__":
    main()
