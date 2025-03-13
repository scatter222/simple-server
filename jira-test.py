import requests
import json
import logging
from jira import JIRA

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ZephyrSquadManager:
    """
    A class to manage Zephyr Squad test cases using the JIRA Python client
    for authentication and session management
    """

    def __init__(self, jira_url, email, token, verify_ssl=False):
        """
        Initialize with Jira credentials
        
        Args:
            jira_url (str): Your Jira instance URL
            email (str): Your Jira email
            token (str): Your Jira Personal Access Token
            verify_ssl (bool): Whether to verify SSL certificates (default: False)
        """
        self.jira_url = jira_url.rstrip('/')
        self.verify_ssl = verify_ssl
        
        # Disable SSL warnings if we're not verifying
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logger.warning("SSL certificate verification is disabled. This is insecure!")
        
        # Initialize Jira client
        logger.info("Connecting to Jira...")
        self.jira = JIRA(
            server=jira_url,
            basic_auth=(email, token),
            options={'verify': verify_ssl}
        )
        logger.info("Successfully connected to Jira")
        
        # Store the authentication data from the Jira client
        self.session = self.jira._session
        self.auth_header = self.session.headers.get('Authorization')
        
        # Zephyr test status IDs
        self.STATUS = {
            "PASS": 1,
            "FAIL": 2,
            "WIP": 3,
            "BLOCKED": 4,
            "UNEXECUTED": -1
        }
    
    def _make_request(self, method, endpoint, params=None, data=None):
        """
        Make a request to the Zephyr API using the authenticated Jira session
        
        Args:
            method (str): HTTP method (GET, POST, PUT)
            endpoint (str): API endpoint
            params (dict, optional): Query parameters
            data (dict, optional): Request body
            
        Returns:
            dict: JSON response or error information
        """
        url = f"{self.jira_url}{endpoint}"
        
        # Ensure we have the right content-type
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, headers=headers, verify=self.verify_ssl)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params, data=json.dumps(data) if data else None, headers=headers, verify=self.verify_ssl)
            elif method.upper() == 'PUT':
                response = self.session.put(url, params=params, data=json.dumps(data) if data else None, headers=headers, verify=self.verify_ssl)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            logger.info(f"Request: {method} {url}")
            logger.info(f"Status code: {response.status_code}")
            
            if response.status_code >= 400:
                logger.error(f"Error response: {response.text}")
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "message": response.text
                }
            
            try:
                return response.json()
            except ValueError:
                if not response.text:
                    return {"success": True}
                return {"raw_response": response.text}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return {"error": True, "message": str(e)}
    
    def test_connectivity(self):
        """
        Test connectivity to various Zephyr endpoints
        
        Returns:
            dict: Results of endpoint tests
        """
        endpoints = [
            # Basic Jira endpoint
            "/rest/api/2/myself",
            # Zephyr Squad endpoints
            "/rest/zapi/latest/cycle",
            "/rest/zapi/latest/execution",
            # Alternative endpoints
            "/rest/zephyr/latest/cycle",
            "/rest/zephyr/1.0/cycle",
            # Classic Zephyr endpoints (for older installations)
            "/rest/api/2/issue/createmeta?projectIds=10000&issuetypeNames=Test&expand=projects.issuetypes.fields"
        ]
        
        results = {}
        for endpoint in endpoints:
            logger.info(f"Testing endpoint: {endpoint}")
            try:
                response = self.session.get(f"{self.jira_url}{endpoint}", verify=self.verify_ssl)
                results[endpoint] = {
                    "status_code": response.status_code,
                    "accessible": response.status_code < 400
                }
                logger.info(f"Endpoint {endpoint}: Status code {response.status_code}")
            except Exception as e:
                results[endpoint] = {
                    "error": str(e),
                    "accessible": False
                }
                logger.error(f"Error testing {endpoint}: {str(e)}")
                
        return results
    
    def get_test_cycles(self, project_id=None, project_key=None):
        """
        Get all test cycles for a project
        
        Args:
            project_id (str, optional): Numeric project ID
            project_key (str, optional): Project key (e.g., "TEST")
            
        Returns:
            dict: JSON response with cycles
        """
        if not project_id and project_key:
            # Get project ID from key
            project = self.jira.project(project_key)
            project_id = project.id
            
        return self._make_request("GET", "/rest/zapi/latest/cycle", params={"projectId": project_id})
    
    def get_executions_for_cycle(self, cycle_id, project_id):
        """
        Get all test executions for a test cycle
        
        Args:
            cycle_id (str): The cycle ID
            project_id (str): The project ID
            
        Returns:
            dict: JSON response with executions
        """
        return self._make_request(
            "GET", 
            "/rest/zapi/latest/execution", 
            params={"cycleId": cycle_id, "projectId": project_id}
        )
    
    def get_execution_for_test(self, test_key, cycle_id, project_id):
        """
        Find execution for a specific test in a cycle
        
        Args:
            test_key (str): Test issue key (e.g., "TEST-123")
            cycle_id (str): The cycle ID
            project_id (str): The project ID
            
        Returns:
            dict: Execution data or None if not found
        """
        executions = self.get_executions_for_cycle(cycle_id, project_id)
        
        if "executions" not in executions:
            logger.error(f"No executions found or unexpected response format: {executions}")
            return None
        
        for execution_id, execution in executions["executions"].items():
            if execution.get("issueKey") == test_key:
                return {
                    "id": execution_id,
                    "data": execution
                }
        
        logger.warning(f"No execution found for test {test_key}")
        return None
    
    def update_test_status(self, execution_id, status, comment=None):
        """
        Update the status of a test execution
        
        Args:
            execution_id (str): The execution ID
            status (str): Status name (PASS, FAIL, etc.)
            comment (str, optional): Comment to add
            
        Returns:
            dict: Response data
        """
        status_id = self.STATUS.get(status.upper())
        if not status_id:
            raise ValueError(f"Invalid status: {status}. Must be one of {list(self.STATUS.keys())}")
        
        payload = {
            "status": status_id
        }
        
        if comment:
            payload["comment"] = comment
            
        return self._make_request(
            "PUT",
            f"/rest/zapi/latest/execution/{execution_id}/execute",
            data=payload
        )
    
    def update_test_by_key(self, test_key, cycle_id, project_id, status, comment=None):
        """
        Find and update a test by its issue key
        
        Args:
            test_key (str): Test issue key (e.g., "TEST-123")
            cycle_id (str): The cycle ID
            project_id (str): The project ID
            status (str): Status name (PASS, FAIL, etc.)
            comment (str, optional): Comment to add
            
        Returns:
            dict: Response data or error
        """
        execution = self.get_execution_for_test(test_key, cycle_id, project_id)
        if not execution:
            return {"error": True, "message": f"Execution not found for test {test_key}"}
        
        return self.update_test_status(execution["id"], status, comment)


def main():
    # Replace with your values
    jira_url = "https://your-domain.atlassian.net"
    email = "your.email@example.com"
    personal_access_token = "your-pat"
    
    # Create the manager with SSL verification disabled
    zephyr = ZephyrSquadManager(jira_url, email, personal_access_token, verify_ssl=False)
    
    # Test connectivity to various endpoints
    logger.info("Testing connectivity to Jira and Zephyr endpoints...")
    endpoints = zephyr.test_connectivity()
    
    for endpoint, result in endpoints.items():
        status = "✅ Working" if result.get("accessible") else "❌ Not Working"
        logger.info(f"{status}: {endpoint} - Status: {result.get('status_code')}")
    
    # Try to use Zephyr if at least one endpoint is accessible
    if any(result.get("accessible") for result in endpoints.values()):
        # Example: Get project ID and work with a specific project
        # Option 1: Use project key
        project_key = "TEST"  # Replace with your project key
        
        # Option 2: Directly use project ID if you know it
        # project_id = "10000"  # Replace with your project ID
        
        try:
            # Get project info using the JIRA client
            project = zephyr.jira.project(project_key)
            project_id = project.id
            logger.info(f"Found project {project.name} with ID {project_id}")
            
            # Get test cycles for the project
            cycles = zephyr.get_test_cycles(project_id=project_id)
            
            if "error" in cycles:
                logger.error(f"Error getting cycles: {cycles}")
            else:
                logger.info(f"Found {len(cycles)} test cycles")
                
                # Example: Work with the first cycle
                if cycles:
                    cycle_id = list(cycles.keys())[0]
                    cycle_name = cycles[cycle_id].get("name", "Unknown")
                    logger.info(f"Working with cycle: {cycle_name} (ID: {cycle_id})")
                    
                    # Example: Update a specific test
                    test_key = "TEST-123"  # Replace with your test case key
                    result = zephyr.update_test_by_key(
                        test_key, 
                        cycle_id, 
                        project_id, 
                        "PASS", 
                        "Automated test passed via API"
                    )
                    
                    if "error" in result:
                        logger.error(f"Failed to update test: {result}")
                    else:
                        logger.info(f"Successfully updated test {test_key} to PASS")
                        
        except Exception as e:
            logger.error(f"Error processing Zephyr data: {str(e)}")
    
    else:
        logger.error("Could not access any Zephyr endpoints. Please check your installation and permissions.")


if __name__ == "__main__":
    main()