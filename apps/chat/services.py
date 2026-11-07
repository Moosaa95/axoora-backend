import re
import urllib.parse
from django.utils import timezone
from .models import ChatSession, ChatMessage, ChatKnowledgeRule
from .rag import retrieve_relevant_chunks, generate_rag_answer

WHATSAPP_SUPPORT_PHONE = '2349110002966'
OFFICE_LOCATION = 'Suite 08 Block C, Cappador Mall. 85 Aguiyi Ironsi Street Maitama, Abuja'

# Keywords that indicate the customer specifically wants to speak with an actual human
HUMAN_ESCALATION_KEYWORDS = [
    'human', 'agent', 'person', 'representative', 'customer care', 'customer service',
    'real person', 'talk to someone', 'speak to someone', 'speak to a human', 'call me',
    'manager', 'operator', 'actual person', 'consultant', 'staff', 'helpdesk person',
    'escalate', 'supervisor', 'i want to talk to a human',
]


def detect_human_escalation_intent(text: str) -> bool:
    cleaned = text.lower().strip()
    for kw in HUMAN_ESCALATION_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', cleaned):
            return True
    return False


def get_whatsapp_escalation_url(session: ChatSession, reason: str = '') -> str:
    ticket = session.ticket_code
    message = (
        f"Hello Axoora Support Desk! I am requesting human agent escalation from the website chat.\n"
        f"Ticket: {ticket}\n"
        f"Customer: {session.customer_name or 'Website Guest'}\n"
        f"Phone: {session.customer_phone or 'Not provided'}\n"
    )
    if reason:
        message += f"Issue: {reason}\n"
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{WHATSAPP_SUPPORT_PHONE}?text={encoded}"


def generate_ai_response(session: ChatSession, user_text: str):
    """
    Intelligently analyzes the user's inquiry:
    1. Auto-populates session.issue_summary if empty
    2. Checks if customer pasted an application/POS tracking code (AX-... or TRK-...)
    3. Checks if customer wants to talk to a human agent -> triggers escalation mode
    4. Handles warm conversational greetings & gratitude
    5. Checks database ChatKnowledgeRule overrides
    6. Runs RAG Pipeline across KnowledgeChunk + live CMS ProductItem + FaqItem
    """
    from ..waitlist.models import WaitlistLead
    from .enums import ChatStatus

    user_lower = user_text.lower().strip()

    # Auto-populate issue_summary on first substantive message
    if not session.issue_summary and len(user_text.strip()) > 3:
        session.issue_summary = user_text.strip()[:120]
        session.save(update_fields=['issue_summary', 'updated_at'])

    # 1. Check for application / POS tracking code (e.g., AX-2026-8492 or TRK-AX9912)
    tracking_match = re.search(r'\b((?:AX|TRK)-[A-Z0-9\-]{3,20})\b', user_text.upper())
    if tracking_match:
        code = tracking_match.group(1)
        lead = WaitlistLead.get_by_ref_or_tracking(code)
        if lead:
            status_label = lead.get_status_display()
            biz = f" for {lead.business_name}" if lead.business_name else ""
            reply_text = (
                f"I found your application{biz}!\n\n"
                f"• Reference: {lead.application_ref or code}\n"
                f"• Tracking Code: {lead.tracking_number or 'Pending assignment'}\n"
                f"• Current Status: {status_label}\n"
                f"• Location: {lead.city or 'Nigeria'}\n\n"
                f"Need an officer to expedite your dispatch?"
            )
            return (
                reply_text,
                [
                    {"label": "👤 Speak to Dispatch Officer", "action": "escalate_human", "primary": True},
                    {"label": "Ask Another Question", "action": "quick_reply", "text": "Tell me about the Apex POS terminal"},
                ],
                False,
            )

    # 2. Check for human escalation trigger
    if detect_human_escalation_intent(user_lower):
        session.status = ChatStatus.ESCALATED
        session.escalated_at = timezone.now()
        session.escalation_reason = user_text
        session.save(update_fields=['status', 'escalated_at', 'escalation_reason', 'updated_at'])

        wa_url = get_whatsapp_escalation_url(session, user_text)

        reply_text = (
            f"I completely understand! I'm transferring you to an actual human customer agent right away.\n\n"
            f"Your Priority Ticket is #{session.ticket_code}.\n\n"
            f"You can connect directly with our live desk officers at our Maitama, Abuja headquarters via WhatsApp, "
            f"or submit your WhatsApp phone number below so an agent can call or message you within 3 minutes."
        )

        suggested_actions = [
            {"label": "Chat with Human Agent on WhatsApp", "action": "open_url", "url": wa_url, "primary": True},
            {"label": "Submit Contact for Callback", "action": "show_escalation_form"},
            {"label": "Continue with AI Assistant", "action": "continue_ai"},
        ]

        return reply_text, suggested_actions, True

    # 3. Conversational greetings & gratitude
    if re.match(r'^(hi|hello|hey|good\s*(morning|afternoon|evening)|salam|assalamu\s*alaikum|how\s*far|yo)\b[\s!?.]*$', user_lower):
        greeting_reply = (
            "Hello! Welcome to Axoora Priority Support. I can help you open a ₦0-fee personal or business account, "
            "order a Dual-SIM Apex POS terminal, check a tracking code (e.g. AX-...), or connect you with a live support officer. "
            "What would you like to explore?"
        )
        greeting_actions = [
            {"label": "Apex POS Terminal", "action": "quick_reply", "text": "Tell me about the Apex POS terminal", "primary": True},
            {"label": "Zero Transfer Fees", "action": "quick_reply", "text": "Are personal transfers really 0 naira?"},
            {"label": "WhatsApp Banking", "action": "quick_reply", "text": "How does WhatsApp banking work?"},
            {"label": "👤 Talk to Human Agent", "action": "escalate_human"},
        ]
        return greeting_reply, greeting_actions, False

    if re.match(r'^(thanks|thank\s*you|appreciate|jazakallah|ese|nagode|ok\s*thanks)\b', user_lower):
        return (
            "You're very welcome! Let me know if you need anything else regarding your account, Apex POS, or WhatsApp banking.",
            [
                {"label": "Open Account / Waitlist", "action": "open_waitlist", "primary": True},
                {"label": "👤 Talk to Human Agent", "action": "escalate_human"},
            ],
            False,
        )

    # 4. Check active ChatKnowledgeRule models from DB for exact overrides
    for rule in ChatKnowledgeRule.get_active_rules():
        keywords = [k.strip().lower() for k in rule.keywords.split(',') if k.strip()]
        if any(kw in user_lower for kw in keywords):
            return rule.response_text, rule.suggested_actions, False

    # 5. RAG Pipeline: Retrieve top relevant chunks from indexed documents, live FAQs, and live products
    retrieved_chunks = retrieve_relevant_chunks(user_text, top_k=3)

    if retrieved_chunks:
        rag_answer, sources, suggested_actions = generate_rag_answer(user_text, retrieved_chunks)
        return rag_answer, suggested_actions, False

    # 6. Fallback when query is outside banking knowledge scope
    fallback_reply = (
        "Thank you for contacting Axoora Priority Support. "
        "I am Axoora's AI Concierge. I can answer questions about our ₦0 fee accounts, Apex 4G POS terminals, "
        "WhatsApp AI banking, non-interest Save & Earn, and application tracking codes. "
        "If you would like to speak directly with an actual human support agent, just click 'Talk to Human Agent' below!"
    )
    fallback_actions = [
        {"label": "👤 Talk to Human Agent", "action": "escalate_human", "primary": True},
        {"label": "Apex POS Terminal", "action": "quick_reply", "text": "Tell me about the Apex POS terminal"},
        {"label": "Zero Transfer Fees", "action": "quick_reply", "text": "Are personal transfers really 0 naira?"},
        {"label": "WhatsApp Banking", "action": "quick_reply", "text": "How does WhatsApp banking work?"},
    ]
    return fallback_reply, fallback_actions, False
