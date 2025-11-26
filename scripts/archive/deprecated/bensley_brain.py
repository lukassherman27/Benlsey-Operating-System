#!/usr/bin/env python3
"""
BENSLEY BRAIN - Smart Query System
Just ask questions and get answers from your entire system

Usage:
    python3 bensley_brain_smart.py "where is the BK-070 proposal?"
    python3 bensley_brain_smart.py "what's the fee for Tel Aviv?"
    python3 bensley_brain_smart.py "show me all proposals from India"
    python3 bensley_brain_smart.py "which proposals are dead?"
"""
import sys
import re
from backend.services.proposal_query_service import ProposalQueryService

class BensleyBrain:
    def __init__(self):
        self.service = ProposalQueryService()

    def answer_question(self, question: str):
        """Parse natural language question and route to appropriate handler"""
        q = question.lower()

        # Extract project code if present
        code_match = re.search(r'\d{2}\s*BK-\d+|BK-\d+', question, re.IGNORECASE)

        # Detect question type
        if any(word in q for word in ['where', 'find', 'show me', 'get', 'locate']):
            if code_match or any(word in q for word in ['proposal', 'project']):
                return self.find_proposal(question)

        if any(word in q for word in ['fee', 'cost', 'price', 'value', 'worth']):
            return self.get_fee(question)

        if any(word in q for word in ['scope', 'sow', 'scope of work', 'document']):
            return self.get_scope(question)

        if any(word in q for word in ['dead', 'stale', 'old', 'inactive', 'lost']):
            return self.show_dead_proposals()

        if 'status' in q or 'how is' in q or 'health' in q:
            return self.get_status(question)

        # Default: search
        return self.find_proposal(question)

    def find_proposal(self, query: str):
        """Search for proposals"""
        # Clean up the query
        search_term = query
        stop_words = ['show', 'me', 'find', 'get', 'where', 'is', 'are', 'the', 'from', 'in', 'proposals', 'proposal', 'projects', 'project']
        for word in stop_words:
            search_term = re.sub(rf'\b{re.escape(word)}\b', '', search_term, flags=re.IGNORECASE)
        search_term = search_term.replace('?', '').strip()

        results = self.service.search_projects_and_proposals(search_term)

        if not results:
            return f"❌ No proposals found matching '{query}'"

        output = [f"\n✅ Found {len(results)} result(s):\n"]
        output.append("=" * 100)

        for prop in results:
            code = prop['project_code']
            name = prop['project_name']
            status = prop['status']
            value = prop.get('project_value')

            output.append(f"\n📋 {code} - {name}")
            output.append(f"   Status: {status}")
            if value:
                output.append(f"   Value: ${value:,.0f}")

            # Get documents
            docs = self.service.get_project_documents(code)
            if docs:
                output.append(f"   📄 {len(docs)} documents")
                scope_docs = [d for d in docs if 'scope' in d['file_name'].lower() or 'proposal' in d['file_name'].lower()]
                if scope_docs:
                    output.append(f"   📝 Scope documents:")
                    for doc in scope_docs[:3]:
                        output.append(f"      - {doc['file_name']}")
                        output.append(f"        {doc['file_path']}")

        output.append("\n" + "=" * 100)
        return "\n".join(output)

    def get_fee(self, query: str):
        """Get project fee"""
        # Extract project identifier
        code_match = re.search(r'\d{2}\s*BK-\d+|BK-\d+', query, re.IGNORECASE)
        if code_match:
            code = code_match.group()
        else:
            # Extract the key search term (remove common words)
            search_term = query.lower()
            # Remove contractions first
            search_term = search_term.replace("what's", "").replace("whats", "")
            stop_words = ['what', 'is', 'the', 'fee', 'for', 'cost', 'price', 'of']
            for word in stop_words:
                search_term = re.sub(rf'\b{re.escape(word)}\b', '', search_term, flags=re.IGNORECASE)
            search_term = search_term.replace('?', '').strip()

            # Search by name
            results = self.service.search_projects_and_proposals(search_term)
            if not results:
                return f"❌ No project found matching '{search_term}'"
            code = results[0]['project_code']

        fee = self.service.get_project_fee(code)
        if fee:
            results = self.service.search_projects_and_proposals(code)
            name = results[0]['project_name'] if results else code
            return f"\n💰 {code} - {name}\n   Fee: ${fee:,.0f}\n"
        else:
            return f"❌ Fee not available for {code}"

    def get_scope(self, query: str):
        """Get scope of work documents"""
        code_match = re.search(r'\d{2}\s*BK-\d+|BK-\d+', query, re.IGNORECASE)
        if code_match:
            code = code_match.group()
        else:
            # Extract key search term
            search_term = query
            stop_words = ['show', 'me', 'the', 'get', 'scope', 'of', 'work', 'for', 'sow']
            for word in stop_words:
                search_term = re.sub(rf'\b{re.escape(word)}\b', '', search_term, flags=re.IGNORECASE)
            search_term = search_term.replace('?', '').strip()

            results = self.service.search_projects_and_proposals(search_term)
            if not results:
                return f"❌ No project found matching '{search_term}'"
            code = results[0]['project_code']

        docs = self.service.find_scope_of_work(code)

        if not docs:
            return f"❌ No scope documents found for {code}"

        output = [f"\n📝 Scope of Work for {code}:\n"]
        for doc in docs:
            output.append(f"   - {doc['file_name']}")
            output.append(f"     Path: {doc['file_path']}")
            if doc.get('page_count'):
                output.append(f"     Pages: {doc['page_count']}")
            output.append("")

        return "\n".join(output)

    def get_status(self, query: str):
        """Get full status of a proposal"""
        code_match = re.search(r'\d{2}\s*BK-\d+|BK-\d+', query, re.IGNORECASE)
        if code_match:
            code = code_match.group()
        else:
            # Extract key search term
            search_term = query
            stop_words = ['status', 'on', 'how', 'is', 'the']
            for word in stop_words:
                search_term = re.sub(rf'\b{re.escape(word)}\b', '', search_term, flags=re.IGNORECASE)
            search_term = search_term.replace('?', '').strip()

            results = self.service.search_projects_and_proposals(search_term)
            if not results:
                return f"❌ No project found matching '{search_term}'"
            code = results[0]['project_code']

        status = self.service.get_proposal_status(code)
        if not status:
            return f"❌ Proposal {code} not found"

        output = ["\n" + "=" * 100]
        output.append(f"📊 STATUS: {status['project_name']}")
        output.append("=" * 100)
        output.append(f"Code:         {status['project_code']}")
        output.append(f"Status:       {status['status']}")

        if status.get('client_company'):
            output.append(f"Client:       {status['client_company']}")

        if status.get('project_value'):
            output.append(f"Value:        ${status['project_value']:,.0f}")

        if status.get('health_score'):
            output.append(f"Health:       {status['health_score']}%")

        if status.get('last_contact_date'):
            output.append(f"Last Contact: {status['last_contact_date']}")

        if status.get('on_hold'):
            output.append(f"⏸️  ON HOLD:   {status.get('on_hold_reason', 'No reason')}")

        # Documents
        docs = status.get('documents', [])
        if docs:
            output.append(f"\n📄 DOCUMENTS ({len(docs)}):")
            for doc in docs[:5]:
                output.append(f"   - {doc['file_name']}")
            if len(docs) > 5:
                output.append(f"   ... and {len(docs) - 5} more")

        # Emails
        emails = status.get('recent_emails', [])
        if emails:
            output.append(f"\n📧 RECENT EMAILS ({len(emails)}):")
            for email in emails[:3]:
                output.append(f"   - {email['date']}: {email['subject']}")
            if len(emails) > 3:
                output.append(f"   ... and {len(emails) - 3} more")

        output.append("=" * 100)
        return "\n".join(output)

    def show_dead_proposals(self):
        """Show proposals that are dead/stale"""
        import sqlite3
        conn = sqlite3.connect(self.service.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT project_code, project_name, days_since_contact, project_value
            FROM proposals
            WHERE status = 'proposal' AND days_since_contact > 90
            ORDER BY days_since_contact DESC
        """)

        dead = cursor.fetchall()
        conn.close()

        if not dead:
            return "\n✅ No dead proposals! All proposals have recent contact.\n"

        output = ["\n💀 DEAD PROPOSALS (>90 days no contact):\n"]
        output.append("=" * 100)

        total_value = 0
        for code, name, days, value in dead:
            output.append(f"{code:15} {name[:60]:60} {int(days):3} days")
            if value:
                output.append(f"                Value: ${value:,.0f}")
                total_value += value

        output.append("=" * 100)
        output.append(f"Total: {len(dead)} dead proposals worth ${total_value:,.0f}")
        output.append("\n💡 Consider marking these as 'lost' status")

        return "\n".join(output)


def main():
    if len(sys.argv) < 2:
        print("""
🧠 BENSLEY BRAIN - Smart Query System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ask questions in natural language:

📍 Finding Proposals:
   python3 bensley_brain_smart.py "where is BK-070?"
   python3 bensley_brain_smart.py "show me Tel Aviv proposals"
   python3 bensley_brain_smart.py "find India projects"

💰 Getting Fees:
   python3 bensley_brain_smart.py "what's the fee for BK-070?"
   python3 bensley_brain_smart.py "how much is the Bodrum project?"

📄 Finding Documents:
   python3 bensley_brain_smart.py "show me the scope for BK-070"
   python3 bensley_brain_smart.py "get scope of work for Tel Aviv"

📊 Getting Status:
   python3 bensley_brain_smart.py "status on BK-070"
   python3 bensley_brain_smart.py "how is the Bali project?"

⚰️  Finding Dead Proposals:
   python3 bensley_brain_smart.py "which proposals are dead?"
   python3 bensley_brain_smart.py "show me stale proposals"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
        sys.exit(0)

    brain = BensleyBrain()
    question = " ".join(sys.argv[1:])

    print(f"\n🧠 Question: {question}")
    answer = brain.answer_question(question)
    print(answer)


if __name__ == "__main__":
    main()
