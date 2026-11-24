from datetime import datetime
import logging
from app.agents.monitoring_agent import ElectionMonitoringAgent
from app.agents.anomaly_agent import IntegrityAnomalyAgent
from app.agents.assistance_agent import AdministrativeAssistanceAgent
from app.agents.reporting_agent import ResultReportingAgent
from app.models.models import AIAlert

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Agentic AI Orchestrator (Module 5)
    Central coordinator that delegates tasks to specialized agents,
    synthesizes outputs, manages agent lifecycle, and enforces human-in-the-loop oversight.
    """

    def __init__(self):
        self.monitoring_agent = ElectionMonitoringAgent()
        self.anomaly_agent = IntegrityAnomalyAgent()
        self.assistance_agent = AdministrativeAssistanceAgent()
        self.reporting_agent = ResultReportingAgent()
        self.last_scan_time = None
        self.last_scan_results = None

    def get_agent_fleet(self) -> list:
        """Return status and metadata for all registered agents."""
        pending_alerts_count = AIAlert.query.filter_by(status='PENDING_REVIEW').count()

        return [
            {
                'id': 'orchestrator',
                'name': 'Agentic AI Orchestrator',
                'module': 'Coordinator',
                'role': 'Coordinator & Task Dispatcher',
                'status': 'ACTIVE',
                'version': '1.0.0',
                'last_run': self.last_scan_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_scan_time else 'Ready'
            },
            {
                'id': 'monitoring',
                'name': self.monitoring_agent.name,
                'module': 'Surveillance',
                'role': 'Status, Deadlines & Turnout Monitoring',
                'status': 'ACTIVE',
                'version': self.monitoring_agent.version,
                'last_run': self.last_scan_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_scan_time else 'Ready'
            },
            {
                'id': 'anomaly',
                'name': self.anomaly_agent.name,
                'module': 'Anomaly Gate',
                'role': 'Integrity, Bursts & Pattern Analysis',
                'status': 'ACTIVE' if pending_alerts_count == 0 else 'ATTENTION',
                'version': self.anomaly_agent.version,
                'last_run': self.last_scan_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_scan_time else 'Ready'
            },
            {
                'id': 'assistance',
                'name': self.assistance_agent.name,
                'module': 'Copilot',
                'role': 'Admin Copilot & Interactive Guidance',
                'status': 'ACTIVE',
                'version': self.assistance_agent.version,
                'last_run': 'Interactive'
            },
            {
                'id': 'reporting',
                'name': self.reporting_agent.name,
                'module': 'Reporting',
                'role': 'Executive Summaries & Certified Tallies',
                'status': 'ACTIVE',
                'version': self.reporting_agent.version,
                'last_run': 'On-Demand'
            }
        ]

    def run_full_system_scan(self) -> dict:
        """Run synchronized monitoring and anomaly detection passes."""
        now = datetime.now()
        monitoring_result = self.monitoring_agent.scan()
        anomaly_result = self.anomaly_agent.scan()

        self.last_scan_time = now
        combined = {
            'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
            'orchestrator_status': 'COMPLETED',
            'monitoring': monitoring_result,
            'anomalies': anomaly_result,
            'overall_risk': anomaly_result.get('risk_level', 'LOW'),
            'system_health_score': monitoring_result.get('health_score', 100),
            'total_alerts_pending': AIAlert.query.filter_by(status='PENDING_REVIEW').count()
        }
        self.last_scan_results = combined
        return combined

    def handle_admin_query(self, query: str, admin_user=None) -> dict:
        """Route conversational request to Administrative Assistance Agent."""
        return self.assistance_agent.process_query(query, admin_user)

    def generate_election_report(self, election_id: int) -> dict:
        """Delegate executive report generation to Reporting Agent."""
        return self.reporting_agent.generate_election_report(election_id)
