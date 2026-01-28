#!/usr/bin/env python3
"""
Test script for Prometheus and Grafana monitoring setup.

Requirements: 18.4, 24.7
"""
import requests
import time
import sys
from typing import Dict, List, Tuple


class MonitoringTester:
    """Test the monitoring stack setup."""
    
    def __init__(self):
        self.prometheus_url = "http://localhost:9090"
        self.alertmanager_url = "http://localhost:9093"
        self.grafana_url = "http://localhost:3000"
        self.results: List[Tuple[str, bool, str]] = []
    
    def test_prometheus_health(self) -> bool:
        """Test if Prometheus is healthy."""
        try:
            response = requests.get(f"{self.prometheus_url}/-/healthy", timeout=5)
            success = response.status_code == 200
            message = "Prometheus is healthy" if success else f"Status code: {response.status_code}"
            self.results.append(("Prometheus Health", success, message))
            return success
        except Exception as e:
            self.results.append(("Prometheus Health", False, str(e)))
            return False
    
    def test_prometheus_targets(self) -> bool:
        """Test if Prometheus targets are configured."""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/targets", timeout=5)
            if response.status_code != 200:
                self.results.append(("Prometheus Targets", False, f"Status code: {response.status_code}"))
                return False
            
            data = response.json()
            active_targets = data.get("data", {}).get("activeTargets", [])
            
            if not active_targets:
                self.results.append(("Prometheus Targets", False, "No active targets found"))
                return False
            
            # Check for expected targets
            expected_jobs = ["prometheus", "multilingual-mandi-api", "node", "postgresql", "redis"]
            found_jobs = set(target.get("labels", {}).get("job", "") for target in active_targets)
            
            missing_jobs = [job for job in expected_jobs if job not in found_jobs]
            
            if missing_jobs:
                message = f"Missing targets: {', '.join(missing_jobs)}"
                self.results.append(("Prometheus Targets", False, message))
                return False
            
            self.results.append(("Prometheus Targets", True, f"Found {len(active_targets)} targets"))
            return True
            
        except Exception as e:
            self.results.append(("Prometheus Targets", False, str(e)))
            return False
    
    def test_prometheus_rules(self) -> bool:
        """Test if Prometheus alert rules are loaded."""
        try:
            response = requests.get(f"{self.prometheus_url}/api/v1/rules", timeout=5)
            if response.status_code != 200:
                self.results.append(("Prometheus Rules", False, f"Status code: {response.status_code}"))
                return False
            
            data = response.json()
            groups = data.get("data", {}).get("groups", [])
            
            if not groups:
                self.results.append(("Prometheus Rules", False, "No rule groups found"))
                return False
            
            # Count total rules
            total_rules = sum(len(group.get("rules", [])) for group in groups)
            
            if total_rules == 0:
                self.results.append(("Prometheus Rules", False, "No rules found"))
                return False
            
            # Check for expected rule groups
            expected_groups = ["latency_alerts", "system_health_alerts", "accuracy_alerts"]
            found_groups = [group.get("name") for group in groups]
            
            missing_groups = [g for g in expected_groups if g not in found_groups]
            
            if missing_groups:
                message = f"Missing rule groups: {', '.join(missing_groups)}"
                self.results.append(("Prometheus Rules", False, message))
                return False
            
            self.results.append(("Prometheus Rules", True, f"Loaded {total_rules} rules in {len(groups)} groups"))
            return True
            
        except Exception as e:
            self.results.append(("Prometheus Rules", False, str(e)))
            return False
    
    def test_alertmanager_health(self) -> bool:
        """Test if Alertmanager is healthy."""
        try:
            response = requests.get(f"{self.alertmanager_url}/-/healthy", timeout=5)
            success = response.status_code == 200
            message = "Alertmanager is healthy" if success else f"Status code: {response.status_code}"
            self.results.append(("Alertmanager Health", success, message))
            return success
        except Exception as e:
            self.results.append(("Alertmanager Health", False, str(e)))
            return False
    
    def test_alertmanager_config(self) -> bool:
        """Test if Alertmanager configuration is valid."""
        try:
            response = requests.get(f"{self.alertmanager_url}/api/v1/status", timeout=5)
            if response.status_code != 200:
                self.results.append(("Alertmanager Config", False, f"Status code: {response.status_code}"))
                return False
            
            data = response.json()
            config = data.get("data", {}).get("config", {})
            
            if not config:
                self.results.append(("Alertmanager Config", False, "No configuration found"))
                return False
            
            # Check for receivers
            receivers = config.get("receivers", [])
            if not receivers:
                self.results.append(("Alertmanager Config", False, "No receivers configured"))
                return False
            
            self.results.append(("Alertmanager Config", True, f"Found {len(receivers)} receivers"))
            return True
            
        except Exception as e:
            self.results.append(("Alertmanager Config", False, str(e)))
            return False
    
    def test_grafana_health(self) -> bool:
        """Test if Grafana is healthy."""
        try:
            response = requests.get(f"{self.grafana_url}/api/health", timeout=5)
            if response.status_code != 200:
                self.results.append(("Grafana Health", False, f"Status code: {response.status_code}"))
                return False
            
            data = response.json()
            database = data.get("database", "")
            
            if database != "ok":
                self.results.append(("Grafana Health", False, f"Database status: {database}"))
                return False
            
            self.results.append(("Grafana Health", True, "Grafana is healthy"))
            return True
            
        except Exception as e:
            self.results.append(("Grafana Health", False, str(e)))
            return False
    
    def test_grafana_datasources(self) -> bool:
        """Test if Grafana datasources are configured."""
        try:
            # Use default admin credentials
            auth = ("admin", "admin")
            response = requests.get(
                f"{self.grafana_url}/api/datasources",
                auth=auth,
                timeout=5
            )
            
            if response.status_code != 200:
                self.results.append(("Grafana Datasources", False, f"Status code: {response.status_code}"))
                return False
            
            datasources = response.json()
            
            if not datasources:
                self.results.append(("Grafana Datasources", False, "No datasources found"))
                return False
            
            # Check for Prometheus datasource
            prometheus_ds = next((ds for ds in datasources if ds.get("type") == "prometheus"), None)
            
            if not prometheus_ds:
                self.results.append(("Grafana Datasources", False, "Prometheus datasource not found"))
                return False
            
            self.results.append(("Grafana Datasources", True, f"Found {len(datasources)} datasources"))
            return True
            
        except Exception as e:
            self.results.append(("Grafana Datasources", False, str(e)))
            return False
    
    def test_grafana_dashboards(self) -> bool:
        """Test if Grafana dashboards are provisioned."""
        try:
            # Use default admin credentials
            auth = ("admin", "admin")
            response = requests.get(
                f"{self.grafana_url}/api/search?type=dash-db",
                auth=auth,
                timeout=5
            )
            
            if response.status_code != 200:
                self.results.append(("Grafana Dashboards", False, f"Status code: {response.status_code}"))
                return False
            
            dashboards = response.json()
            
            if not dashboards:
                self.results.append(("Grafana Dashboards", False, "No dashboards found"))
                return False
            
            # Check for expected dashboards
            dashboard_titles = [d.get("title", "") for d in dashboards]
            expected_dashboards = ["Multilingual Mandi - System Overview", "Multilingual Mandi - Latency Monitoring"]
            
            found_dashboards = [title for title in expected_dashboards if title in dashboard_titles]
            
            if len(found_dashboards) < len(expected_dashboards):
                missing = [d for d in expected_dashboards if d not in found_dashboards]
                message = f"Missing dashboards: {', '.join(missing)}"
                self.results.append(("Grafana Dashboards", False, message))
                return False
            
            self.results.append(("Grafana Dashboards", True, f"Found {len(dashboards)} dashboards"))
            return True
            
        except Exception as e:
            self.results.append(("Grafana Dashboards", False, str(e)))
            return False
    
    def run_all_tests(self) -> bool:
        """Run all monitoring tests."""
        print("=" * 60)
        print("Multilingual Mandi - Monitoring Stack Tests")
        print("=" * 60)
        print()
        
        tests = [
            ("Prometheus Health", self.test_prometheus_health),
            ("Prometheus Targets", self.test_prometheus_targets),
            ("Prometheus Rules", self.test_prometheus_rules),
            ("Alertmanager Health", self.test_alertmanager_health),
            ("Alertmanager Config", self.test_alertmanager_config),
            ("Grafana Health", self.test_grafana_health),
            ("Grafana Datasources", self.test_grafana_datasources),
            ("Grafana Dashboards", self.test_grafana_dashboards),
        ]
        
        print("Running tests...\n")
        
        for test_name, test_func in tests:
            print(f"Testing {test_name}...", end=" ")
            test_func()
            print()
        
        # Print results
        print("\n" + "=" * 60)
        print("Test Results")
        print("=" * 60)
        print()
        
        passed = 0
        failed = 0
        
        for test_name, success, message in self.results:
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"{status:8} | {test_name:25} | {message}")
            
            if success:
                passed += 1
            else:
                failed += 1
        
        print()
        print("=" * 60)
        print(f"Total: {len(self.results)} tests | Passed: {passed} | Failed: {failed}")
        print("=" * 60)
        print()
        
        if failed > 0:
            print("Some tests failed. Please check the monitoring stack configuration.")
            print()
            print("Troubleshooting tips:")
            print("  1. Ensure all services are running: docker-compose ps")
            print("  2. Check service logs: docker-compose logs <service-name>")
            print("  3. Verify configuration files are correct")
            print("  4. Wait a few seconds and try again (services may still be starting)")
            return False
        else:
            print("All tests passed! Monitoring stack is configured correctly.")
            print()
            print("Next steps:")
            print("  1. Access Grafana at http://localhost:3000")
            print("  2. View dashboards in the 'Multilingual Mandi' folder")
            print("  3. Configure alert notifications in Alertmanager")
            print("  4. Add Prometheus middleware to your FastAPI app")
            return True


def main():
    """Main entry point."""
    tester = MonitoringTester()
    
    print("Waiting for services to be ready...")
    time.sleep(5)
    
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
