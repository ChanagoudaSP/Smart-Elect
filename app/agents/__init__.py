"""
Agentic AI System for Smart-Elect
Modules per project synopsis:
- Orchestrator (Module 5)
- Election Monitoring Agent (Module 6)
- Administrative Assistance Agent (Module 7)
- Integrity & Anomaly Analysis Agent (Module 8)
- Result & Reporting Agent (Module 9)
"""

from app.agents.orchestrator import AgentOrchestrator
from app.agents.monitoring_agent import ElectionMonitoringAgent
from app.agents.anomaly_agent import IntegrityAnomalyAgent
from app.agents.assistance_agent import AdministrativeAssistanceAgent
from app.agents.reporting_agent import ResultReportingAgent

orchestrator = AgentOrchestrator()

__all__ = [
    'orchestrator',
    'AgentOrchestrator',
    'ElectionMonitoringAgent',
    'IntegrityAnomalyAgent',
    'AdministrativeAssistanceAgent',
    'ResultReportingAgent'
]
