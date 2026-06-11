import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://localhost:8000"

def make_request(path, method="GET", data=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8")
            return status_code, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            err_json = json.loads(body)
        except Exception:
            err_json = {"detail": body}
        return e.code, err_json
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

def run_tests():
    print("Starting API Validation on live server...")
    
    # 1. Health Endpoint
    code, res = make_request("/health")
    assert code == 200, f"Health endpoint failed: {code}"
    assert res.get("status") == "healthy", f"Status unhealthy: {res}"
    print("[PASS] GET /health")
    
    # 2. Agents Endpoint
    code, res = make_request("/agents")
    assert code == 200, f"Agents endpoint failed: {code}"
    assert len(res.get("agents", [])) == 8, f"Expected 8 agents, got {len(res.get('agents', []))}"
    print("[PASS] GET /agents")
    
    # 3. Demo Scenarios
    code, res = make_request("/demo/scenarios")
    assert code == 200, f"Demo scenarios failed: {code}"
    assert len(res.get("scenarios", [])) > 0, "No demo scenarios found"
    print("[PASS] GET /demo/scenarios")
    
    # 4. Run Demo Scenario (to load data)
    code, res = make_request("/demo/run/ai-healthcare", method="POST")
    assert code == 200, f"Run demo scenario failed: {code}"
    project_id = res.get("project_id")
    assert project_id == "demo-healthcare", f"Expected project ID 'demo-healthcare', got {project_id}"
    print("[PASS] POST /demo/run/ai-healthcare")
    
    # 5. Status endpoint
    code, res = make_request(f"/status/{project_id}")
    assert code == 200, f"Get status failed: {code}"
    assert res.get("status") == "completed", f"Status not completed: {res}"
    print("[PASS] GET /status/{id}")
    
    # 6. Report endpoint
    code, res = make_request(f"/report/{project_id}")
    assert code == 200, f"Get report failed: {code}"
    assert "report" in res, "Report markdown missing"
    assert "diagrams" in res, "Diagrams key missing"
    print("[PASS] GET /report/{id}")
    
    # 7. Metrics endpoint
    code, res = make_request(f"/metrics/{project_id}")
    assert code == 200, f"Get metrics failed: {code}"
    assert "execution_metrics" in res, "execution_metrics missing"
    print("[PASS] GET /metrics/{id}")
    
    # 8. Wiki stats endpoint
    code, res = make_request(f"/wiki/{project_id}")
    assert code == 200, f"Get wiki stats failed: {code}"
    assert "topic_count" in res, "topic_count missing in wiki stats"
    print("[PASS] GET /wiki/{id}")
    
    # 9. Wiki pages endpoint
    code, res = make_request(f"/wiki/{project_id}/pages")
    assert code == 200, f"Get wiki pages failed: {code}"
    assert "topic_pages" in res, "topic_pages missing"
    print("[PASS] GET /wiki/{id}/pages")
    
    # 10. Research endpoint
    code, res = make_request(f"/research/{project_id}")
    assert code == 200, f"Get research failed: {code}"
    assert "plans" in res, "plans missing in research response"
    print("[PASS] GET /research/{id}")
    
    print("\nAPI VALIDATION COMPLETE: ALL 10 CORE ENDPOINTS PASS!")

if __name__ == "__main__":
    run_tests()
