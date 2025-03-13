import requests
import json
import logging
import base64
import re
import time
from urllib.parse import parse_qs, urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ZephyrWithSessionAuth:
    """
    Zephyr API client that uses browser-like session authentication to avoid CAPTCHA
    """
    
    def __init__(self, jira_url, username, password, verify_ssl=False):
        """
        Initialize with Jira credentials
        
        Args:
            jira_url (str): Jira instance URL
            username (str): Jira username/email
            password (str): Jira password or token
            verify_ssl (bool): Whether to verify SSL certificates
        """
        self.jira_url = jira_url.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        
        # Disable SSL warnings if verification is disabled
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Set user agent to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        })
        
        # Status IDs for Zephyr
        self.STATUS = {
            "PASS": 1,
            "FAIL": 2,
            "WIP": 3,
            "BLOCKED": 4,
            "UNEXECUTED": -1
        }
    
    def login(self):
        """
        Log in to Jira using a browser-like session approach
        
        Returns:
            bool: True if login was successful, False otherwise
        """
        # Step 1: Visit the login page to get any necessary cookies
        login_url = f"{self.jira_url}/login.jsp"
        logger.info(f"Visiting login page: {login_url}")
        
        try:
            response = self.session.get(login_url, verify=self.verify_ssl)
            
            if response.status_code != 200:
                logger.error(f"Failed to access login page: {response.status_code}")
                return False
                
            # Step 2: Submit login credentials
            auth_url = f"{self.jira_url}/rest/auth/1/session"
            payload = {
                "username": self.username,
                "password": self.password
            }
            
            logger.info("Submitting login credentials")
            response = self.session.post(
                auth_url,
                json=payload,
                verify=self.verify_ssl,
                headers={
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'  # Important for some instances
                }
            )
            
            if response.status_code == 200:
                logger.info("Login successful!")
                
                # Store any session cookies or tokens returned
                self.session.headers.update({
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                })
                
                # Check if we can access a protected resource
                myself = self.session.get(
                    f"{self.jira_url}/rest/api/2/myself",
                    verify=self.verify_ssl
                )
                
                if myself.status_code == 200:
                    user_data = myself.json()
                    logger.info(f"Authenticated as: {user_data.get('displayName', user_data.get('name', 'Unknown'))}")
                    return True
                else:
                    logger.warning("Login appeared successful but user info couldn't be retrieved")
                    return False
            else:
                logger.error(f"Login failed: {response.status_code} - {response.text}")
                
                # Check for CAPTCHA challenge
                if "CAPTCHA_CHALLENGE" in response.text:
                    logger.error("CAPTCHA challenge detected. Cannot proceed with automation.")
                    logger.error("Try logging in via browser first, then use those cookies.")
                    
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False
    
    def get_cycles(self, project_id):
        """
        Get test cycles for a project
        
        Args:
            project_id (str): Project ID
            
        Returns:
            dict: JSON response with cycles
        """
        url = f"{self.jira_url}/rest/zapi/latest/cycle"
        params = {"projectId": project_id}
        
        try:
            response = self.session.get(url, params=params, verify=self.verify_ssl)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get cycles: {response.status_code} - {response.text}")
                return {"error": True, "message": response.text}
                
        except Exception as e:
            logger.error(f"Error getting cycles: {str(e)}")
            return {"error": True, "message": str(e)}
    
    def get_executions(self, cycle_id, project_id):
        """
        Get executions for a test cycle
        
        Args:
            cycle_id (str): Cycle ID
            project_id (str): Project ID
            
        Returns:
            dict: JSON response with executions
        """
        url = f"{self.jira_url}/rest/zapi/latest/execution"
        params = {
            "cycleId": cycle_id,
            "projectId": project_id
        }
        
        try:
            response = self.session.get(url, params=params, verify=self.verify_ssl)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get executions: {response.status_code} - {response.text}")
                return {"error": True, "message": response.text}
                
        except Exception as e:
            logger.error(f"Error getting executions: {str(e)}")
            return {"error": True, "message": str(e)}
    
    def update_execution(self, execution_id, status, comment=None):
        """
        Update the status of a test execution
        
        Args:
            execution_id (str): Execution ID
            status (str): Status name (PASS, FAIL, etc.)
            comment (str, optional): Comment to add
            
        Returns:
            dict: JSON response
        """
        url = f"{self.jira_url}/rest/zapi/latest/execution/{execution_id}/execute"
        
        status_id = self.STATUS.get(status.upper())
        if not status_id:
            return {"error": True, "message": f"Invalid status: {status}"}
            
        payload = {
            "status": status_id
        }
        
        if comment:
            payload["comment"] = comment
            
        try:
            response = self.session.put(
                url,
                json=payload,
                verify=self.verify_ssl
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Failed to update execution: {response.status_code} - {response.text}")
                return {"error": True, "message": response.text}
                
        except Exception as e:
            logger.error(f"Error updating execution: {str(e)}")
            return {"error": True, "message": str(e)}
    
    def get_project_id_by_key(self, project_key):
        """
        Get project ID from project key
        
        Args:
            project_key (str): Project key (e.g., "TEST")
            
        Returns:
            str: Project ID or None
        """
        url = f"{self.jira_url}/rest/api/2/project/{project_key}"
        
        try:
            response = self.session.get(url, verify=self.verify_ssl)
            
            if response.status_code == 200:
                return response.json().get("id")
            else:
                logger.error(f"Failed to get project: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting project: {str(e)}")
            return None
    
    def test_zephyr_endpoints(self):
        """
        Test various Zephyr endpoints to find working ones
        
        Returns:
            dict: Results of the tests
        """
        endpoints = [
            # Zephyr Squad endpoints
            "/rest/zapi/latest/cycle",
            "/rest/zapi/latest/execution",
            # Alternative endpoints
            "/rest/zephyr/latest/cycle",
            "/rest/zephyr/1.0/cycle",
            # Zephyr Scale endpoints (formerly TM4J)
            "/rest/atm/1.0/testcase",
            "/rest/atm/1.0/testrun"
        ]
        
        results = {}
        for endpoint in endpoints:
            logger.info(f"Testing endpoint: {endpoint}")
            
            try:
                response = self.session.get(
                    f"{self.jira_url}{endpoint}",
                    verify=self.verify_ssl,
                    params={"projectId": "10000"}  # Add a dummy project ID
                )
                
                # Consider 200-299 as success, 401/403 as auth issues, others as general errors
                if 200 <= response.status_code < 300:
                    status = "Accessible"
                elif response.status_code in [401, 403]:
                    status = "Authentication Required"
                else:
                    status = f"Error ({response.status_code})"
                    
                results[endpoint] = {
                    "status": status,
                    "status_code": response.status_code
                }
                
                logger.info(f"Endpoint {endpoint}: {status}")
                
            except Exception as e:
                logger.error(f"Error testing {endpoint}: {str(e)}")
                results[endpoint] = {
                    "status": "Error",
                    "error": str(e)
                }
                
        return results


def manual_cookie_login():
    """
    Alternative login method using cookies from a browser session.
    
    This is useful when automated login keeps triggering CAPTCHA challenges.
    Steps:
    1. Log in to Jira in your browser
    2. Open developer tools (F12)
    3. Go to Network tab, find a request to Jira
    4. Copy all cookies as a string
    5. Use those cookies here
    """
    jira_url = "https://your-domain.atlassian.net"
    
    # Create a session
    session = requests.Session()
    
    # Disable SSL verification if needed
    verify_ssl = False
    if not verify_ssl:
        import urllib3
        urllib3.disable_warnings()
    
    # Paste the cookies string from your browser here
    cookies_string = "JSESSIONID=ABCDEF123456; atlassian.xsrf.token=WXYZ-7890; jira.editor.user.mode=wysiwyg"
    
    # Parse cookies and add to session
    for cookie in cookies_string.split(';'):
        if '=' in cookie:
            name, value = cookie.strip().split('=', 1)
            session.cookies.set(name, value)
    
    # Test if it works
    try:
        response = session.get(
            f"{jira_url}/rest/api/2/myself",
            verify=verify_ssl
        )
        
        if response.status_code == 200:
            user = response.json()
            logger.info(f"Login successful! Logged in as {user.get('displayName', user.get('name'))}")
            
            # Now you can use this session to make API calls
            return session
        else:
            logger.error(f"Cookie login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error in cookie login: {str(e)}")
        return None


def main():
    # Replace with your values
    jira_url = "https://your-domain.atlassian.net"
    username = "your.email@example.com"
    password = "your-password-or-token"  # Try with actual password first
    
    # Create client and log in
    client = ZephyrWithSessionAuth(jira_url, username, password, verify_ssl=False)
    
    if client.login():
        logger.info("Login successful! Testing Zephyr endpoints...")
        
        # Test which Zephyr endpoints are accessible
        results = client.test_zephyr_endpoints()
        
        # Get project ID from key
        project_key = "TEST"  # Replace with your project key
        project_id = client.get_project_id_by_key(project_key)
        
        if project_id:
            logger.info(f"Found project ID {project_id} for key {project_key}")
            
            # Get test cycles
            cycles = client.get_cycles(project_id)
            
            if "error" not in cycles and cycles:
                # Take the first cycle
                cycle_id = list(cycles.keys())[0]
                cycle_name = cycles[cycle_id].get("name", "Unknown")
                logger.info(f"Working with cycle {cycle_name} (ID: {cycle_id})")
                
                # Get executions
                executions = client.get_executions(cycle_id, project_id)
                
                if "error" not in executions and "executions" in executions:
                    execution_id = list(executions["executions"].keys())[0]
                    test_key = executions["executions"][execution_id].get("issueKey", "Unknown")
                    
                    logger.info(f"Updating test {test_key} (execution ID: {execution_id})")
                    
                    # Update test status
                    result = client.update_execution(
                        execution_id,
                        "PASS",
                        "Automated test passed via session API"
                    )
                    
                    if "error" not in result:
                        logger.info(f"Successfully updated test {test_key} to PASS")
                    else:
                        logger.error(f"Failed to update test: {result}")
                else:
                    logger.error("Failed to get executions")
            else:
                logger.error("Failed to get test cycles")
        else:
            logger.error(f"Could not find project ID for key {project_key}")
    else:
        logger.error("Login failed. Consider using manual cookie authentication.")
        
        # Uncomment to try manual cookie authentication
        # session = manual_cookie_login()
        # if session:
        #     # Use the session for API calls
        #     pass


if __name__ == "__main__":
    main()