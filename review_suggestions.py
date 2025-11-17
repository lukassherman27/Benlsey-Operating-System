#!/usr/bin/env python3
"""
Simple CLI tool to review and approve database intelligence suggestions
"""

import requests
import json
from typing import Dict, List

API_BASE = "http://localhost:8000"

def get_suggestions() -> List[Dict]:
    """Get all pending suggestions"""
    response = requests.get(f"{API_BASE}/api/intel/suggestions?status=pending")
    return response.json()['items']

def display_suggestion(suggestion: Dict, index: int, total: int):
    """Display a suggestion with formatted details"""
    print("\n" + "="*80)
    print(f"SUGGESTION {index + 1} of {total}")
    print("="*80)

    # Project info
    print(f"\n📋 PROJECT: {suggestion['project_code']} - {suggestion['project_name']}")

    # Priority bucket
    bucket_emoji = {
        'urgent': '🔴 URGENT',
        'needs_attention': '⚠️  NEEDS ATTENTION',
        'fyi': '📊 FYI'
    }
    print(f"   Priority: {bucket_emoji.get(suggestion['bucket'], suggestion['bucket'])}")

    # Issue type
    print(f"\n🔍 ISSUE: {suggestion['pattern_label']}")
    print(f"   Type: {suggestion['suggestion_type']}")
    print(f"   Confidence: {suggestion['confidence']*100:.0f}%")

    # Impact
    impact = suggestion['impact']
    print(f"\n💥 IMPACT: {impact['summary']}")
    print(f"   Severity: {impact['severity']}")
    if impact['value_usd']:
        print(f"   Financial Impact: ${impact['value_usd']:,.0f}")

    # Evidence
    print(f"\n📊 EVIDENCE:")
    evidence = suggestion['evidence']
    for signal in evidence.get('signals', []):
        print(f"   • {signal}")

    # Proposed fix
    print(f"\n✨ PROPOSED FIX:")
    for field, value in suggestion['proposed_fix'].items():
        print(f"   • {field} → {value}")

def apply_decision(suggestion_id: str, decision: str, reason: str = None) -> Dict:
    """Apply a decision to a suggestion"""
    url = f"{API_BASE}/api/intel/suggestions/{suggestion_id}/decision"
    data = {
        "decision": decision,
        "reason": reason or f"User {decision} via CLI",
        "apply_now": True,
        "dry_run": False
    }
    response = requests.post(url, json=data)
    return response.json()

def preview_decision(suggestion_id: str) -> Dict:
    """Preview what would change (dry-run)"""
    url = f"{API_BASE}/api/intel/suggestions/{suggestion_id}/decision"
    data = {
        "decision": "approved",
        "reason": "Preview",
        "apply_now": True,
        "dry_run": True
    }
    response = requests.post(url, json=data)
    return response.json()

def main():
    """Main interactive review loop"""
    print("\n" + "🤖 DATABASE INTELLIGENCE - SUGGESTION REVIEW TOOL".center(80))
    print("="*80)

    # Get all pending suggestions
    suggestions = get_suggestions()

    if not suggestions:
        print("\n✅ No pending suggestions! Database is clean.")
        return

    print(f"\n📊 Found {len(suggestions)} pending suggestions")

    # Group by bucket
    urgent = [s for s in suggestions if s['bucket'] == 'urgent']
    needs_attention = [s for s in suggestions if s['bucket'] == 'needs_attention']
    fyi = [s for s in suggestions if s['bucket'] == 'fyi']

    print(f"\n   🔴 {len(urgent)} urgent")
    print(f"   ⚠️  {len(needs_attention)} needs attention")
    print(f"   📊 {len(fyi)} FYI")

    # Review each suggestion
    approved = 0
    rejected = 0
    snoozed = 0

    for i, suggestion in enumerate(suggestions):
        display_suggestion(suggestion, i, len(suggestions))

        # Get user decision
        while True:
            print("\n" + "-"*80)
            choice = input("""
👉 What do you want to do?
   [A] Accept (approve and apply changes)
   [P] Preview (see what would change)
   [R] Reject
   [S] Snooze
   [Q] Quit

Your choice: """).strip().upper()

            if choice == 'Q':
                print("\n👋 Exiting review. Progress saved.")
                break

            elif choice == 'P':
                # Preview mode
                print("\n🔍 Previewing changes...")
                result = preview_decision(suggestion['id'])
                print(f"   Would update: {result['would_update']} project(s)")
                print(f"   Changes would be applied: {suggestion['proposed_fix']}")
                continue

            elif choice == 'A':
                # Approve
                reason = input("\n📝 Reason for approval (optional): ").strip()
                print("\n✅ Approving suggestion...")
                result = apply_decision(suggestion['id'], 'approved', reason)
                print(f"   ✅ Updated {result['updated']} project(s)")
                print(f"   📝 Decision logged to training data")
                approved += 1
                break

            elif choice == 'R':
                # Reject
                reason = input("\n📝 Reason for rejection (required): ").strip()
                if not reason:
                    print("   ❌ Rejection requires a reason!")
                    continue
                print("\n❌ Rejecting suggestion...")
                result = apply_decision(suggestion['id'], 'rejected', reason)
                print(f"   ❌ Suggestion rejected")
                rejected += 1
                break

            elif choice == 'S':
                # Snooze
                reason = input("\n📝 Reason for snooze (optional): ").strip()
                print("\n⏰ Snoozing suggestion for 7 days...")
                result = apply_decision(suggestion['id'], 'snoozed', reason)
                print(f"   ⏰ Suggestion snoozed")
                snoozed += 1
                break

            else:
                print("   ❌ Invalid choice. Please try again.")

        if choice == 'Q':
            break

    # Summary
    print("\n" + "="*80)
    print("📊 REVIEW SUMMARY".center(80))
    print("="*80)
    print(f"\n   ✅ Approved: {approved}")
    print(f"   ❌ Rejected: {rejected}")
    print(f"   ⏰ Snoozed: {snoozed}")
    print(f"   📊 Total reviewed: {approved + rejected + snoozed}/{len(suggestions)}")

    # Check remaining
    remaining = get_suggestions()
    print(f"\n   📋 Suggestions remaining: {len(remaining)}")

    if len(remaining) == 0:
        print("\n   🎉 All suggestions reviewed! Database is clean.")

    print("\n" + "="*80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Review cancelled. Progress saved.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Make sure the API server is running on port 8000")
