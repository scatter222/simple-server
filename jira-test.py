import requests
import json
import logging
import re
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JiraZephyrClient:
    """
    Ultra-simplified Jira/Zephyr client focused on just passing/failing tests
    with correct XSRF token handling
    """
    
    def __init__(self, jira_url, username, password):
        self.jira_url = jira_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False
        
        # Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Set browser-like headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/json,application/xhtml+xml;q=0.9',
            'Accept-Language': 'en-US,en;q=0.5'
        })
        
        # Status IDs in Zephyr
        self.STATUS = {
            "PASS": 1,
            "FAIL": 2,
            "WIP": 3,
            "BLOCKED": 4,
            "UNEXECUTED": -1
        }
        
        # Initialize XSRF token
        self.xsrf_token = None
    
    def get_xsrf_token(self):
        """Get the XSRF token from Jira"""
        try:
            # First try to get it from the dashboard
            response = self.session.get(f"{self.jira_url}/secure/Dashboard.jspa")
            
            # Try to extract token from cookies
            for cookie in self.session.cookies:
                if cookie.name == 'atlassian.xsrf.token':
                    self.xsrf_token = cookie.value
                    logger.info(f"Found XSRF token in cookies: {self.xsrf_token[:5]}...")
                    return self.xsrf_token
            
            # Try to extract from HTML if not in cookies
            soup = BeautifulSoup(response.text, 'html.parser')
            meta_tag = soup.find('meta', attrs={'name': 'ajs-atl-token'})
            
            if meta_tag and 'content' in meta_tag.attrs:
                self.xsrf_token = meta_tag.attrs['content']
                logger.info(f"Found XSRF token in HTML: {self.xsrf_token[:5]}...")
                return self.xsrf_token
            
            logger.warning("Could not find XSRF token")
            return None
            
        except Exception as e:
            logger.error(f"Error getting XSRF token: {str(e)}")
            return None
    
    def login(self):
        """Log in to Jira and get necessary tokens"""
        try:
            # First visit the login page to get cookies
            self.session.get(f"{self.jira_url}/login.jsp")
            
            # Try to get XSRF token before login
            self.get_xsrf_token()
            
            # Prepare login data
            login_data = {
                'username': self.username,
                'password': self.password,
                'login': 'Log in'
            }
            
            # Add XSRF token if we have it
            headers = {}
            if self.xsrf_token:
                headers['X-Atlassian-Token'] = 'no-check'
                headers['X-AUSERNAME'] = self.username
                
            # Submit login form
            response = self.session.post(
                f"{self.jira_url}/login.jsp",
                data=login_data,
                headers=headers,
                allow_redirects=True
            )
            
            # Check if login was successful
            if 'logout' in response.text.lower() or 'log out' in response.text.lower():
                logger.info("Login successful")
                
                # Get XSRF token after login if we don't have it yet
                if not self.xsrf_token:
                    self.get_xsrf_token()
                
                # Verify we can access API
                me_response = self.session.get(f"{self.jira_url}/rest/api/2/myself")
                if me_response.status_code == 200:
                    user_data = me_response.json()
                    logger.info(f"Logged in as: {user_data.get('displayName', user_data.get('name', 'Unknown'))}")
                    return True
            
            logger.error(f"Login failed with status code: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def get_test_cycles(self, project_id):
        """Get test cycles for a project"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Add XSRF token if available
        if self.xsrf_token:
            headers['X-Atlassian-Token'] = 'no-check'
            
        response = self.session.get(
            f"{self.jira_url}/rest/zapi/latest/cycle",
            params={"projectId": project_id},
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get cycles: {response.status_code} - {response.text}")
            return None
    
    def get_executions(self, cycle_id, project_id):
        """Get executions for a test cycle"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Add XSRF token if available
        if self.xsrf_token:
            headers['X-Atlassian-Token'] = 'no-check'
            
        response = self.session.get(
            f"{self.jira_url}/rest/zapi/latest/execution",
            params={"cycleId": cycle_id, "projectId": project_id},
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get executions: {response.status_code} - {response.text}")
            return None
    
    def update_test_status(self, execution_id, status, comment=None):
        """Update test execution status"""
        status_id = self.STATUS.get(status.upper())
        if not status_id:
            logger.error(f"Invalid status: {status}")
            return False
            
        payload = {
            "status": status_id
        }
        
        if comment:
            payload["comment"] = comment
            
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Add XSRF token - this is critical for PUT/POST operations
        if self.xsrf_token:
            headers['X-Atlassian-Token'] = 'no-check'
            
        response = self.session.put(
            f"{self.jira_url}/rest/zapi/latest/execution/{execution_id}/execute",
            json=payload,
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"Successfully updated execution {execution_id} to {status}")
            return True
        else:
            logger.error(f"Failed to update execution: {response.status_code} - {response.text}")
            return False
    
    def find_test_execution(self, test_key, cycle_id, project_id):
        """Find execution ID for a specific test key in a cycle"""
        executions = self.get_executions(cycle_id, project_id)
        if not executions or "executions" not in executions:
            return None
            
        for execution_id, execution in executions["executions"].items():
            if execution.get("issueKey") == test_key:
                return execution_id
                
        return None
    
    def update_test_by_key(self, test_key, cycle_id, project_id, status, comment=None):
        """Update test status by test key"""
        execution_id = self.find_test_execution(test_key, cycle_id, project_id)
        if not execution_id:
            logger.error(f"Could not find execution for test {test_key}")
            return False
            
        return self.update_test_status(execution_id, status, comment)


def main():
    # Replace with your values
    jira_url = "https://your-jira-instance.com"
    username = "your.username"
    password = "your-password"  # Use actual password, not token
    
    # Project and test info
    project_id = "10000"  # Replace with your project ID
    test_key = "TEST-123"  # Replace with your test key
    
    # Create client
    client = JiraZephyrClient(jira_url, username, password)
    
    if client.login():
        # Get test cycles
        cycles = client.get_test_cycles(project_id)
        
        if cycles:
            # Use first cycle (you would need to select the appropriate one)
            cycle_id = list(cycles.keys())[0]
            cycle_name = cycles[cycle_id].get("name", "Unknown")
            logger.info(f"Using cycle: {cycle_name}")
            
            # Update test status
            result = client.update_test_by_key(
                test_key,
                cycle_id,
                project_id,
                "PASS",
                "Automated test passed"
            )
            
            if result:
                logger.info(f"Successfully updated test {test_key} to PASS")
            else:
                logger.error(f"Failed to update test {test_key}")
        else:
            logger.error("No test cycles found")
    else:
        logger.error("Login failed")


if __name__ == "__main__":
    main()