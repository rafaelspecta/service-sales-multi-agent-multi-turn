from .router_agent import router_agent
from .pricing_agent import pricing_agent
from .service_info_agent import service_info_agent
from .payment_agent import payment_agent
from .scheduling_agent import scheduling_agent
from .escalation_agent import escalation_agent

AGENTS = {
    "Router Agent": router_agent,
    "Pricing Agent": pricing_agent,
    "Payment Agent": payment_agent,
    "Scheduling Agent": scheduling_agent,
    "Service Information Agent": service_info_agent,
    "Escalation Agent": escalation_agent,
}

SPECIALISTS = {k: v for k, v in AGENTS.items() if k != "Router Agent"}