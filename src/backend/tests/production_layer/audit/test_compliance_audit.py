from decimal import Decimal

from app.production_layer.audit.compliance_audit import (
    ComplianceAudit,
    ComplianceCheck,
    ComplianceReport,
)


class TestComplianceCheck:
    def test_create_passed(self):
        check = ComplianceCheck.create(
            rule_name="position_limit",
            description="Position check",
            passed=True,
            details="ok",
        )
        assert check.passed
        assert check.rule_name == "position_limit"

    def test_create_failed(self):
        check = ComplianceCheck.create(
            rule_name="leverage_limit",
            description="Leverage check",
            passed=False,
            details="exceeded",
        )
        assert not check.passed


class TestComplianceAudit:
    def test_check_position_limit_pass(self):
        auditor = ComplianceAudit()
        check = auditor.check_position_limit("AAPL", Decimal("10"))
        assert check.passed

    def test_check_position_limit_fail(self):
        auditor = ComplianceAudit()
        auditor.thresholds["max_position_pct"] = Decimal("25")
        check = auditor.check_position_limit("AAPL", Decimal("50"))
        assert not check.passed

    def test_check_leverage_pass(self):
        auditor = ComplianceAudit()
        check = auditor.check_leverage(Decimal("2"))
        assert check.passed

    def test_check_leverage_fail(self):
        auditor = ComplianceAudit()
        check = auditor.check_leverage(Decimal("5"))
        assert not check.passed

    def test_check_daily_trades_pass(self):
        auditor = ComplianceAudit()
        check = auditor.check_daily_trades(100)
        assert check.passed

    def test_check_daily_trades_fail(self):
        auditor = ComplianceAudit()
        check = auditor.check_daily_trades(600)
        assert not check.passed

    def test_check_drawdown_pass(self):
        auditor = ComplianceAudit()
        check = auditor.check_drawdown(Decimal("10"))
        assert check.passed

    def test_check_drawdown_fail(self):
        auditor = ComplianceAudit()
        check = auditor.check_drawdown(Decimal("40"))
        assert not check.passed

    def test_generate_report_all_pass(self):
        auditor = ComplianceAudit()
        auditor.check_position_limit("A", Decimal("10"))
        auditor.check_leverage(Decimal("1.5"))
        auditor.check_daily_trades(50)
        auditor.check_drawdown(Decimal("5"))

        report = auditor.generate_report()
        assert report.total_checks == 4
        assert report.passed_checks == 4
        assert report.failed_checks == 0
        assert report.compliance_score_pct == Decimal("100")
        assert report.is_compliant()

    def test_generate_report_some_fail(self):
        auditor = ComplianceAudit()
        auditor.check_position_limit("A", Decimal("10"))
        auditor.check_position_limit("B", Decimal("50"))
        auditor.check_leverage(Decimal("5"))
        auditor.check_daily_trades(100)

        report = auditor.generate_report()
        assert report.total_checks == 4
        assert report.passed_checks == 2
        assert report.failed_checks == 2
        assert report.compliance_score_pct == Decimal("50")
        assert not report.is_compliant()
        assert len(report.failed_checks_list()) == 2

    def test_max_checks(self):
        auditor = ComplianceAudit(max_checks=10)
        for i in range(20):
            auditor.check_daily_trades(i)
        assert len(auditor.checks) <= 10

    def test_clear(self):
        auditor = ComplianceAudit()
        auditor.check_leverage(Decimal("1"))
        auditor.clear()
        assert len(auditor.checks) == 0
