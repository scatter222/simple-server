import requests
from requests.auth import HTTPBasicAuth
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ZephyrSquadAPI:
    """
    A class to interact with Zephyr Squad API for test execution management
    """

    def __init__(self, jira_base_url, username, api_token):
        """
        Initialize the API wrapper
        
        Args:
            jira_base_url (str): Base URL of your Jira instance (e.g., https://your-domain.atlassian.net)
            username (str): Jira username (usually email)
            api_token (str): Jira API token
        """
        self.jira_base_url = jira_base_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Status IDs in Zephyr Squad
        self.STATUS = {
            "PASS": 1,
            "FAIL": 2,
            "WIP": 3,
            "BLOCKED": 4,
            "UNEXECUTED": -1
        }
    
    def get_cycles(self, project_id):
        """
        Get all test cycles for a project
        
        Args:
            project_id (str): Jira project ID
            
        Returns:
            dict: JSON response with cycle information
        """
        url = f"{self.jira_base_url}/rest/zapi/latest/cycle?projectId={project_id}"
        
        response = requests.get(
            url,
            auth=self.auth,
            headers=self.headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get cycles: {response.text}")
            response.raise_for_status()
            
        return response.json()
    
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
        url = f"{self.jira_base_url}/rest/zapi/latest/execution"
        
        params = {
            "cycleId": cycle_id,
            "projectId": project_id
        }
        
        if version_id:
            params["versionId"] = version_id
            
        response = requests.get(
            url,
            auth=self.auth,
            headers=self.headers,
            params=params
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get executions: {response.text}")
            response.raise_for_status()
            
        return response.json()
    
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
        url = f"{self.jira_base_url}/rest/zapi/latest/execution/{execution_id}/execute"
        
        # Get the numeric status ID from the status name
        status_id = self.STATUS.get(status.upper())
        if not status_id:
            raise ValueError(f"Invalid status: {status}. Must be one of {list(self.STATUS.keys())}")
        
        payload = {
            "status": status_id,
            "cycleId": execution_id,  # This is redundant but sometimes required
        }
        
        if comment:
            payload["comment"] = comment
            
        response = requests.put(
            url,
            auth=self.auth,
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        if response.status_code not in [200, 201]:
            logger.error(f"Failed to update execution status: {response.text}")
            response.raise_for_status()
            
        return response.json()
    
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
        url = f"{self.jira_base_url}/rest/zapi/latest/execution/execute/bulk"
        
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
            
        response = requests.put(
            url,
            auth=self.auth,
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        if response.status_code not in [200, 201]:
            logger.error(f"Failed to bulk update executions: {response.text}")
            response.raise_for_status()
            
        return response.json()


# Example usage
def main():
    # Replace these with your actual values
    jira_url = "https://your-domain.atlassian.net"
    username = "your.email@example.com"
    api_token = "your-api-token"
    project_id = "10001"  # Get this from your Jira project
    
    # Initialize the API client
    zephyr = ZephyrSquadAPI(jira_url, username, api_token)
    
    # Get all test cycles for the project
    cycles = zephyr.get_cycles(project_id)
    logger.info(f"Found {len(cycles)} cycles")
    
    # Choose the first cycle (you would normally select the appropriate one)
    if cycles:
        cycle_id = list(cycles.keys())[0]  # Extract the first cycle ID
        logger.info(f"Working with cycle ID: {cycle_id}")
        
        # Get test case to update (replace with your test case key)
        test_key = "TEST-123"
        execution = zephyr.get_execution_by_test_key(test_key, cycle_id, project_id)
        
        if execution:
            # Update the test status to PASS
            result = zephyr.update_execution_status(
                execution["id"], 
                "PASS", 
                "Automated test executed successfully"
            )
            logger.info(f"Updated test {test_key} to PASS")
            
            # Example of updating a test to FAIL
            # result = zephyr.update_execution_status(
            #     execution["id"], 
            #     "FAIL", 
            #     "Automated test failed: Expected value 5, got 4"
            # )
            # logger.info(f"Updated test {test_key} to FAIL")
    

if __name__ == "__main__":
    main()