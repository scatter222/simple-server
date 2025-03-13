import requests
import json
import logging
import base64

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ZephyrSquadAPI:
    """
    A class to interact with Zephyr Squad API for test execution management
    with multiple authentication methods
    """

    def __init__(self, jira_base_url, username, personal_access_token, use_bearer_token=False):
        """
        Initialize the API wrapper
        
        Args:
            jira_base_url (str): Base URL of your Jira instance (e.g., https://your-domain.atlassian.net)
            username (str): Jira username (usually email)
            personal_access_token (str): Jira Personal Access Token
            use_bearer_token (bool): If True, use Bearer token auth instead of Basic Auth
        """
        self.jira_base_url = jira_base_url.rstrip('/')
        self.username = username
        self.token = personal_access_token
        self.use_bearer_token = use_bearer_token
        
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Set up authentication headers
        if use_bearer_token:
            self.headers["Authorization"] = f"Bearer {personal_access_token}"
        else:
            # Basic Auth - encoded as base64
            auth_str = f"{username}:{personal_access_token}"
            encoded_auth = base64.b64encode(auth_str.encode()).decode()
            self.headers["Authorization"] = f"Basic {encoded_auth}"
        
        # Status IDs in Zephyr Squad
        self.STATUS = {
            "PASS": 1,
            "FAIL": 2,
            "WIP": 3,
            "BLOCKED": 4,
            "UNEXECUTED": -1
        }
        
    def _make_request(self, method, endpoint, params=None, data=None):
        """
        Helper method to make requests with proper error handling
        
        Args:
            method (str): HTTP method (GET, POST, PUT, etc.)
            endpoint (str): API endpoint (without base URL)
            params (dict, optional): Query parameters
            data (dict, optional): Request body data
            
        Returns:
            dict: JSON response
        """
        url = f"{self.jira_base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, params=params, data=json.dumps(data) if data else None)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, params=params, data=json.dumps(data) if data else None)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            # Log request details for debugging
            logger.info(f"Request: {method} {url}")
            logger.info(f"Headers: {self.headers}")
            if params:
                logger.info(f"Params: {params}")
            
            # Print detailed error message on failure
            if response.status_code >= 400:
                logger.error(f"Request failed with status {response.status_code}: {response.text}")
                
                # Special handling for auth errors
                if response.status_code == 401:
                    logger.error("Authentication failed. Check your credentials and token permissions.")
                    if not self.use_bearer_token:
                        logger.info("Try setting use_bearer_token=True if your Jira instance requires Bearer token auth.")
                    
                response.raise_for_status()
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response")
            return {"error": "Invalid JSON response"}
    
    def get_cycles(self, project_id):
        """
        Get all test cycles for a project
        
        Args:
            project_id (str): Jira project ID
            
        Returns:
            dict: JSON response with cycle information
        """
        return self._make_request(
            "GET", 
            "/rest/zapi/latest/cycle", 
            params={"projectId": project_id}
        )
    
    def get_executions(self, cycle_id, project_id, version_id=None):
        """
        Get all test executions for a cycle
        
        Args:
            cycle_id (str): Test cycle ID
            project_id (str): Jira project ID
            version_id (str, optional): Version ID
            
        Returns:
            dict: JSON response with execution information
        """
        params = {
            "cycleId": cycle_id,
            "projectId": project_id
        }
        
        if version_id:
            params["versionId"] = version_id
            
        return self._make_request(
            "GET", 
            "/rest/zapi/latest/execution", 
            params=params
        )
    
    def get_execution_by_test_key(self, test_key, cycle_id, project_id):
        """
        Find a specific test execution by test case key
        
        Args:
            test_key (str): Test case key (e.g., TEST-123)
            cycle_id (str): Test cycle ID
            project_id (str): Jira project ID
            
        Returns:
            dict: Execution information or None if not found
        """
        executions = self.get_executions(cycle_id, project_id)
        
        for execution_id, execution_data in executions.get("executions", {}).items():
            if execution_data.get("issueKey") == test_key:
                return {
                    "id": execution_id,
                    "data": execution_data
                }
                
        logger.warning(f"No execution found for test key {test_key}")
        return None
    
    def update_execution_status(self, execution_id, status, comment=None):
        """
        Update the status of a test execution
        
        Args:
            execution_id (str): Execution ID
            status (str): Status name (PASS, FAIL, etc.)
            comment (str, optional): Comment to add to the execution
            
        Returns:
            dict: JSON response with updated execution
        """
        # Get the numeric status ID from the status name
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
    
    def bulk_update_executions(self, execution_ids, status, comment=None):
        """
        Update multiple test executions at once
        
        Args:
            execution_ids (list): List of execution IDs
            status (str): Status name (PASS, FAIL, etc.)
            comment (str, optional): Comment to add to all executions
            
        Returns:
            dict: JSON response with update results
        """
        # Get the numeric status ID from the status name
        status_id = self.STATUS.get(status.upper())
        if not status_id:
            raise ValueError(f"Invalid status: {status}. Must be one of {list(self.STATUS.keys())}")
        
        payload = {
            "executions": execution_ids,
            "status": status_id
        }
        
        if comment:
            payload["comment"] = comment
            
        return self._make_request(
            "PUT", 
            "/rest/zapi/latest/execution/execute/bulk",
            data=payload
        )

    # Try alternative API endpoints if the main ones don't work
    def try_alternative_endpoints(self):
        """
        Test various API endpoints to determine which ones are accessible
        Returns a list of working endpoints
        """
        endpoints = [
            # Standard Zephyr Squad endpoints
            "/rest/zapi/latest/cycle",
            "/rest/zapi/latest/execution",
            # Alternative endpoints that might be used in different versions
            "/rest/zephyr/latest/cycle",
            "/rest/zephyr/1.0/cycle",
            "/rest/api/2/project"  # This is a standard Jira endpoint to test basic connectivity
        ]
        
        working_endpoints = []
        for endpoint in endpoints:
            try:
                logger.info(f"Testing endpoint: {endpoint}")
                response = requests.get(
                    f"{self.jira_base_url}{endpoint}", 
                    headers=self.headers
                )
                
                if response.status_code < 400:
                    working_endpoints.append({
                        "endpoint": endpoint,
                        "status": response.status_code,
                        "works": True
                    })
                    logger.info(f"Endpoint {endpoint} is accessible: {response.status_code}")
                else:
                    working_endpoints.append({
                        "endpoint": endpoint,
                        "status": response.status_code,
                        "works": False
                    })
                    logger.info(f"Endpoint {endpoint} returned status code: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to access {endpoint}: {str(e)}")
                working_endpoints.append({
                    "endpoint": endpoint,
                    "status": "Error",
                    "works": False,
                    "error": str(e)
                })
                
        return working_endpoints


# Example usage with better error handling
def main():
    # Replace these with your actual values
    jira_url = "https://your-domain.atlassian.net"
    username = "your.email@example.com"
    personal_access_token = "your-personal-access-token"
    project_id = "10001"  # Get this from your Jira project
    
    # Try both authentication methods
    for auth_method in [False, True]:
        logger.info(f"Trying {'Bearer Token' if auth_method else 'Basic Auth'} authentication")
        
        try:
            # Initialize API client
            zephyr = ZephyrSquadAPI(
                jira_url, 
                username, 
                personal_access_token, 
                use_bearer_token=auth_method
            )
            
            # First test which endpoints are accessible
            working_endpoints = zephyr.try_alternative_endpoints()
            
            # Display results
            logger.info("API Endpoint Test Results:")
            for endpoint in working_endpoints:
                status = "✅ Working" if endpoint["works"] else "❌ Not Working"
                logger.info(f"{status}: {endpoint['endpoint']} - Status: {endpoint['status']}")
                
            # If we got here without errors, basic connectivity is working
            logger.info(f"Successfully connected using {'Bearer Token' if auth_method else 'Basic Auth'}")
            
            # Try to get cycles if the endpoint is working
            if any(e["endpoint"] == "/rest/zapi/latest/cycle" and e["works"] for e in working_endpoints):
                logger.info("Attempting to get test cycles...")
                cycles = zephyr.get_cycles(project_id)
                logger.info(f"Found {len(cycles) if isinstance(cycles, dict) else 0} cycles")
                
                # Continue with the main functionality...
                # (rest of the code from previous example)
                
            break  # Exit the loop if we've successfully connected
            
        except Exception as e:
            logger.error(f"Error with authentication method {'Bearer Token' if auth_method else 'Basic Auth'}: {str(e)}")
            if auth_method:  # If we've already tried both methods
                logger.error("Both authentication methods failed. Please check your credentials and Jira setup.")


if __name__ == "__main__":
    main()