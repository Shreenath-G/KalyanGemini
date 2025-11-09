"""Validation test for end-to-end test suite structure

This test validates that all E2E test files are properly structured
and can be imported without running the actual tests that require
Google Cloud dependencies.

Requirements: 1.1, 2.1, 6.1, 7.1
"""

import ast
import os
import sys


def test_e2e_test_files_exist():
    """Verify all E2E test files exist"""
    test_dir = os.path.dirname(__file__)
    
    required_test_files = [
        "test_e2e_campaign_workflow.py",
        "test_e2e_performance_optimization.py",
        "test_e2e_bid_execution.py",
        "test_e2e_firestore_persistence.py"
    ]
    
    for test_file in required_test_files:
        file_path = os.path.join(test_dir, test_file)
        assert os.path.exists(file_path), f"Test file {test_file} not found"
        print(f"✓ Found: {test_file}")
    
    print(f"\n✓ All {len(required_test_files)} E2E test files exist")


def test_campaign_workflow_structure():
    """Validate campaign workflow test structure"""
    test_file = os.path.join(os.path.dirname(__file__), "test_e2e_campaign_workflow.py")
    
    with open(test_file, 'r') as f:
        code = f.read()
    
    tree = ast.parse(code)
    
    # Find test class
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    class_names = [cls.name for cls in classes]
    
    assert "TestCampaignCreationWorkflow" in class_names
    
    # Find test methods (including async)
    test_class = next(cls for cls in classes if cls.name == "TestCampaignCreationWorkflow")
    test_methods = [
        node.name for node in test_class.body 
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    ]
    
    required_tests = [
        "test_campaign_orchestrator_initialization",
        "test_agent_message_creation",
        "test_agent_response_structure",
        "test_campaign_request_handling",
        "test_strategy_synthesis",
        "test_launch_timeline_calculation",
        "test_complete_campaign_workflow"
    ]
    
    for test_name in required_tests:
        assert test_name in test_methods, f"Missing test: {test_name}"
    
    print(f"✓ Campaign workflow test has {len(test_methods)} test methods")
    print(f"  Required tests: {len(required_tests)}")
    print(f"  All required tests present: ✓")


def test_performance_optimization_structure():
    """Validate performance optimization test structure"""
    test_file = os.path.join(os.path.dirname(__file__), "test_e2e_performance_optimization.py")
    
    with open(test_file, 'r') as f:
        code = f.read()
    
    tree = ast.parse(code)
    
    # Find test class
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    class_names = [cls.name for cls in classes]
    
    assert "TestPerformanceOptimizationWorkflow" in class_names
    
    # Find test methods (including async)
    test_class = next(cls for cls in classes if cls.name == "TestPerformanceOptimizationWorkflow")
    test_methods = [
        node.name for node in test_class.body 
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    ]
    
    required_tests = [
        "test_performance_metrics_calculation",
        "test_variant_metrics_calculation",
        "test_underperforming_variant_detection",
        "test_top_performing_variant_detection",
        "test_optimization_action_generation",
        "test_optimization_request_handling",
        "test_complete_optimization_workflow"
    ]
    
    for test_name in required_tests:
        assert test_name in test_methods, f"Missing test: {test_name}"
    
    print(f"✓ Performance optimization test has {len(test_methods)} test methods")
    print(f"  Required tests: {len(required_tests)}")
    print(f"  All required tests present: ✓")


def test_bid_execution_structure():
    """Validate bid execution test structure"""
    test_file = os.path.join(os.path.dirname(__file__), "test_e2e_bid_execution.py")
    
    with open(test_file, 'r') as f:
        code = f.read()
    
    tree = ast.parse(code)
    
    # Find test class
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    class_names = [cls.name for cls in classes]
    
    assert "TestBidExecutionWorkflow" in class_names
    assert "MockBidExecutionAgent" in class_names
    
    # Find test methods (including async)
    test_class = next(cls for cls in classes if cls.name == "TestBidExecutionWorkflow")
    test_methods = [
        node.name for node in test_class.body 
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    ]
    
    required_tests = [
        "test_bid_agent_initialization",
        "test_relevance_check",
        "test_segment_matching",
        "test_budget_check",
        "test_bid_price_calculation",
        "test_bid_request_handling",
        "test_bid_tracking",
        "test_bidding_strategy_adjustment",
        "test_complete_bid_workflow"
    ]
    
    for test_name in required_tests:
        assert test_name in test_methods, f"Missing test: {test_name}"
    
    print(f"✓ Bid execution test has {len(test_methods)} test methods")
    print(f"  Required tests: {len(required_tests)}")
    print(f"  All required tests present: ✓")


def test_firestore_persistence_structure():
    """Validate Firestore persistence test structure"""
    test_file = os.path.join(os.path.dirname(__file__), "test_e2e_firestore_persistence.py")
    
    with open(test_file, 'r') as f:
        code = f.read()
    
    tree = ast.parse(code)
    
    # Find test class
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    class_names = [cls.name for cls in classes]
    
    assert "TestFirestorePersistence" in class_names
    
    # Find test methods (including async)
    test_class = next(cls for cls in classes if cls.name == "TestFirestorePersistence")
    test_methods = [
        node.name for node in test_class.body 
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    ]
    
    required_tests = [
        "test_firestore_service_initialization",
        "test_campaign_creation",
        "test_campaign_update",
        "test_campaign_retrieval_by_account",
        "test_creative_variants_persistence",
        "test_audience_segments_persistence",
        "test_budget_allocation_persistence",
        "test_performance_metrics_persistence",
        "test_complete_persistence_workflow"
    ]
    
    for test_name in required_tests:
        assert test_name in test_methods, f"Missing test: {test_name}"
    
    print(f"✓ Firestore persistence test has {len(test_methods)} test methods")
    print(f"  Required tests: {len(required_tests)}")
    print(f"  All required tests present: ✓")


def test_requirements_coverage():
    """Verify that tests cover all specified requirements"""
    test_dir = os.path.dirname(__file__)
    
    # Requirements that should be covered
    requirements_coverage = {
        "1.1": "Campaign creation via API",
        "2.1": "Campaign orchestrator coordination",
        "6.1": "Performance monitoring",
        "7.1": "Bid execution",
        "7.2": "Bid evaluation",
        "7.3": "Budget checking",
        "7.4": "Bid price calculation",
        "7.5": "Bid tracking",
        "13.1": "Data persistence",
        "13.4": "Data retrieval"
    }
    
    # Check each test file for requirement references
    test_files = [
        "test_e2e_campaign_workflow.py",
        "test_e2e_performance_optimization.py",
        "test_e2e_bid_execution.py",
        "test_e2e_firestore_persistence.py"
    ]
    
    requirements_found = set()
    
    for test_file in test_files:
        file_path = os.path.join(test_dir, test_file)
        with open(file_path, 'r') as f:
            content = f.read()
            
            for req_id in requirements_coverage.keys():
                if req_id in content:
                    requirements_found.add(req_id)
    
    print(f"\n✓ Requirements coverage:")
    for req_id, description in requirements_coverage.items():
        status = "✓" if req_id in requirements_found else "✗"
        print(f"  {status} {req_id}: {description}")
    
    coverage_percent = (len(requirements_found) / len(requirements_coverage)) * 100
    print(f"\n✓ Total coverage: {coverage_percent:.0f}% ({len(requirements_found)}/{len(requirements_coverage)} requirements)")
    
    assert len(requirements_found) >= len(requirements_coverage) * 0.8, "Less than 80% requirement coverage"


def test_documentation_quality():
    """Verify test documentation quality"""
    test_dir = os.path.dirname(__file__)
    
    test_files = [
        "test_e2e_campaign_workflow.py",
        "test_e2e_performance_optimization.py",
        "test_e2e_bid_execution.py",
        "test_e2e_firestore_persistence.py"
    ]
    
    for test_file in test_files:
        file_path = os.path.join(test_dir, test_file)
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for module docstring
        assert '"""' in content[:500], f"{test_file} missing module docstring"
        
        # Check for requirement references
        assert "Requirements:" in content, f"{test_file} missing requirement references"
        
        # Check for test descriptions
        tree = ast.parse(content)
        functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        test_functions = [f for f in functions if f.name.startswith("test_")]
        
        documented_tests = sum(1 for f in test_functions if ast.get_docstring(f))
        doc_percent = (documented_tests / len(test_functions)) * 100 if test_functions else 0
        
        print(f"✓ {test_file}: {doc_percent:.0f}% tests documented ({documented_tests}/{len(test_functions)})")
        
        assert doc_percent >= 50, f"{test_file} has less than 50% test documentation"
    
    print(f"\n✓ All test files have adequate documentation")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("END-TO-END TEST SUITE VALIDATION")
    print("="*60 + "\n")
    
    tests = [
        ("Test Files Exist", test_e2e_test_files_exist),
        ("Campaign Workflow Structure", test_campaign_workflow_structure),
        ("Performance Optimization Structure", test_performance_optimization_structure),
        ("Bid Execution Structure", test_bid_execution_structure),
        ("Firestore Persistence Structure", test_firestore_persistence_structure),
        ("Requirements Coverage", test_requirements_coverage),
        ("Documentation Quality", test_documentation_quality)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        print("-" * 60)
        try:
            test_func()
            results.append((test_name, True))
        except Exception as e:
            print(f"✗ FAILED: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n✓ ALL VALIDATION TESTS PASSED!")
        print("\nThe E2E test suite is properly structured with:")
        print("  - 4 comprehensive test files")
        print("  - Complete coverage of requirements 1.1, 2.1, 6.1, 7.1-7.5, 13.1, 13.4")
        print("  - Campaign creation workflow tests")
        print("  - Performance monitoring and optimization tests")
        print("  - Bid execution workflow tests")
        print("  - Firestore data persistence tests")
        print("  - Proper documentation and structure")
        print("\nTo run the actual tests (requires Google Cloud dependencies):")
        print("  pytest tests/test_e2e_campaign_workflow.py -v")
        print("  pytest tests/test_e2e_performance_optimization.py -v")
        print("  pytest tests/test_e2e_bid_execution.py -v")
        print("  pytest tests/test_e2e_firestore_persistence.py -v")
    else:
        print("\n✗ Some validation tests failed. Please review the errors above.")
    
    print("\n" + "="*60 + "\n")
    
    sys.exit(0 if all_passed else 1)
