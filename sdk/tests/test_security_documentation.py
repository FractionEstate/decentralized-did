"""
Test security documentation completeness

This test validates that all security testing documentation is present and complete.
"""

import os
import pytest
from pathlib import Path


class TestSecurityDocumentation:
    """Validate security testing documentation"""

    @pytest.fixture
    def docs_dir(self):
        """Get docs/security directory path"""
        repo_root = Path(__file__).resolve().parents[2]
        return repo_root / "docs" / "security"

    def test_security_docs_directory_exists(self, docs_dir):
        """Security documentation directory should exist"""
        assert docs_dir.exists(
        ), f"Security docs directory not found: {docs_dir}"
        assert docs_dir.is_dir(
        ), f"Security docs path is not a directory: {docs_dir}"

    def test_owasp_zap_guide_exists(self, docs_dir):
        """OWASP ZAP integration guide should exist"""
        guide_path = docs_dir / "owasp-zap-guide.md"
        assert guide_path.exists(), f"OWASP ZAP guide not found: {guide_path}"

        # Check minimum content
        content = guide_path.read_text()
        assert len(content) > 1000, "OWASP ZAP guide content too short"
        assert "OWASP ZAP" in content, "OWASP ZAP not mentioned in guide"
        assert "Installation" in content, "Installation section missing"
        assert "Configuration" in content, "Configuration section missing"
        assert "Running" in content or "Scan" in content, "Scanning instructions missing"

    def test_load_testing_guide_exists(self, docs_dir):
        """Load testing guide should exist"""
        guide_path = docs_dir / "load-testing-guide.md"
        assert guide_path.exists(
        ), f"Load testing guide not found: {guide_path}"

        # Check minimum content
        content = guide_path.read_text()
        assert len(content) > 1000, "Load testing guide content too short"
        assert "Load Testing" in content or "load testing" in content, "Load testing not mentioned"
        assert "Locust" in content or "k6" in content, "Load testing tools not mentioned"
        assert "Performance" in content or "performance" in content, "Performance targets missing"
        assert "concurrent" in content.lower(), "Concurrency not discussed"

    def test_performance_benchmarking_guide_exists(self, docs_dir):
        """Performance benchmarking guide should exist"""
        guide_path = docs_dir / "performance-benchmarking.md"
        assert guide_path.exists(
        ), f"Performance benchmarking guide not found: {guide_path}"

        # Check minimum content
        content = guide_path.read_text()
        assert len(
            content) > 1000, "Performance benchmarking guide content too short"
        assert "Performance" in content or "performance" in content, "Performance not mentioned"
        assert "Benchmark" in content or "benchmark" in content, "Benchmarking not discussed"
        assert "Profiling" in content or "profiling" in content, "Profiling not discussed"
        assert "Optimization" in content or "optimization" in content, "Optimization not discussed"

    def test_security_testing_checklist_exists(self, docs_dir):
        """Security testing checklist should exist"""
        checklist_path = docs_dir / "security-testing-checklist.md"
        assert checklist_path.exists(
        ), f"Security testing checklist not found: {checklist_path}"

        # Check minimum content
        content = checklist_path.read_text()
        assert len(content) > 1000, "Security testing checklist content too short"
        assert "OWASP" in content, "OWASP not mentioned in checklist"
        assert "Authentication" in content or "authentication" in content, "Authentication not in checklist"
        assert "Authorization" in content or "authorization" in content, "Authorization not in checklist"
        assert "Input Validation" in content or "input validation" in content, "Input validation not in checklist"
        assert "Rate Limiting" in content or "rate limiting" in content, "Rate limiting not in checklist"

    def test_all_guides_have_required_sections(self, docs_dir):
        """All security guides should have standard sections"""
        guides = [
            "owasp-zap-guide.md",
            "load-testing-guide.md",
            "performance-benchmarking.md",
            "security-testing-checklist.md"
        ]

        required_sections = ["Overview", "References"]

        for guide_name in guides:
            guide_path = docs_dir / guide_name
            content = guide_path.read_text()

            for section in required_sections:
                assert section in content, f"{guide_name} missing '{section}' section"

    def test_guides_have_code_examples(self, docs_dir):
        """Security guides should include code examples"""
        guides = [
            "owasp-zap-guide.md",
            "load-testing-guide.md",
            "performance-benchmarking.md",
            "security-testing-checklist.md"
        ]

        for guide_name in guides:
            guide_path = docs_dir / guide_name
            content = guide_path.read_text()

            # Check for code blocks (``` markers)
            assert "```" in content, f"{guide_name} has no code examples"

            # Count code blocks
            # Each block has opening and closing ```
            code_blocks = content.count("```") // 2
            assert code_blocks >= 3, f"{guide_name} should have at least 3 code examples (found {code_blocks})"

    def test_guides_have_bash_examples(self, docs_dir):
        """Security guides should include bash/shell examples"""
        guides = [
            "owasp-zap-guide.md",
            "load-testing-guide.md",
            "performance-benchmarking.md",
            "security-testing-checklist.md"
        ]

        for guide_name in guides:
            guide_path = docs_dir / guide_name
            content = guide_path.read_text()

            # Check for bash code blocks
            has_bash = "```bash" in content or "```sh" in content or "curl" in content
            assert has_bash, f"{guide_name} should include bash/shell examples"

    def test_security_testing_checklist_has_owasp_top_10(self, docs_dir):
        """Security checklist should cover OWASP API Security Top 10"""
        checklist_path = docs_dir / "security-testing-checklist.md"
        content = checklist_path.read_text()

        # Check for OWASP API Security Top 10 items
        owasp_items = [
            "Broken Object Level Authorization",
            "Broken Authentication",
            "Broken Object Property Level Authorization",
            "Unrestricted Resource Consumption",
            "Broken Function Level Authorization",
            "Unrestricted Access to Sensitive Business Flows",
            "Server Side Request Forgery",
            "Security Misconfiguration",
            "Improper Inventory Management",
            "Unsafe Consumption of APIs"
        ]

        found_items = 0
        for item in owasp_items:
            if item in content:
                found_items += 1

        # Should cover at least 8 out of 10 items
        assert found_items >= 8, f"Security checklist should cover OWASP API Top 10 (found {found_items}/10)"

    def test_load_testing_guide_mentions_performance_targets(self, docs_dir):
        """Load testing guide should specify performance targets"""
        guide_path = docs_dir / "load-testing-guide.md"
        content = guide_path.read_text()

        # Check for performance metrics
        assert "150ms" in content or "150 ms" in content, "Enrollment target (150ms) not specified"
        assert "75ms" in content or "75 ms" in content, "Verification target (75ms) not specified"
        assert "1000" in content, "Concurrent user target (1000) not specified"

    def test_owasp_zap_guide_has_installation_instructions(self, docs_dir):
        """OWASP ZAP guide should have installation instructions for multiple platforms"""
        guide_path = docs_dir / "owasp-zap-guide.md"
        content = guide_path.read_text()

        # Should cover multiple platforms
        assert "Linux" in content or "linux" in content, "Linux installation not covered"
        assert "Docker" in content or "docker" in content, "Docker installation not covered"

    def test_performance_benchmarking_guide_has_profiling_tools(self, docs_dir):
        """Performance benchmarking guide should mention profiling tools"""
        guide_path = docs_dir / "performance-benchmarking.md"
        content = guide_path.read_text()

        # Should mention key profiling tools
        profiling_tools = ["cProfile", "py-spy",
                           "memory_profiler", "line_profiler"]

        found_tools = 0
        for tool in profiling_tools:
            if tool in content:
                found_tools += 1

        assert found_tools >= 2, f"Should mention at least 2 profiling tools (found {found_tools})"

    def test_all_guides_cross_reference_each_other(self, docs_dir):
        """Security guides should cross-reference each other"""
        guides = {
            "owasp-zap-guide.md": ["load-testing-guide", "performance-benchmarking"],
            "load-testing-guide.md": ["performance-benchmarking", "security-testing-checklist"],
            "performance-benchmarking.md": ["security-testing-checklist"],
            "security-testing-checklist.md": []  # Final guide, no forward references needed
        }

        for guide_name, expected_refs in guides.items():
            guide_path = docs_dir / guide_name
            content = guide_path.read_text()

            for ref in expected_refs:
                # Check for markdown links or file references
                has_reference = (
                    ref in content or
                    ref.replace("-", " ").title() in content or
                    f"[{ref}]" in content
                )
                assert has_reference, f"{guide_name} should reference {ref}"
