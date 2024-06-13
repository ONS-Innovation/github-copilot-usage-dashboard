import jwt
import time
import requests

def get_access_token(org: str, pem: str, client_id: str) -> tuple | str:
    """
        Generates an Installation Access Token to make Authorised Github API Requests.
        Generates a JSON Web Token
        Gets the Installation ID from the JWT
        Generates an Installation Access Token with the ID
        ==========
        Args:
            org (str):  the name of the organisation to be accessed. This should match the .pem file.
                        This variable is dealt with in code.
            pem (str):  the contents of the .pem file used to sign the JWT.
        Returns:
            tuple: contains the token and its expiration time
            or
            str: an error message
    """

    # Generate JSON Web Token
    issue_time = time.time()
    expiration_time = issue_time + 600

    signing_key = jwt.jwk_from_pem(pem.encode())

    payload = {
        # Issued at time
        "iat": int(issue_time),
        # Expiration time
        "exp": int(expiration_time),
        # Github App CLient ID
        "iss": client_id
    }

    jwt_instance = jwt.JWT()
    encoded_jwt = jwt_instance.encode(payload, signing_key, alg="RS256")

    # Get Installation ID

    header = {"Authorization": f"Bearer {encoded_jwt}"}

    response = requests.get(url=f"https://api.github.com/orgs/{org}/installation", headers=header)

    if response.status_code == 200:
        installation_json = response.json()
        installation_id = installation_json["id"]

        # Get Access Token
        response = requests.post(url=f"https://api.github.com/app/installations/{installation_id}/access_tokens", headers=header)
        access_token = response.json()
        return (access_token["token"], access_token["expires_at"])
    else:
        return response.json()["message"]
    

# api_controller class to manage all API interactions
class api_controller():
    """
        A class used to interact with the Github API.

        The class can perform get, patch, post and delete requests using the
        get(), patch(), post() and delete() functions respectively.
    """
    def __init__(self, token) -> None:
        """
            Creates the header attribute containing the Personal Access token to make auth'd API requests.
        """
        self.headers = {"Authorization": "token " + token}

    def get(self, url: str, params: dict, add_prefix: bool = True) -> requests.Response:
        """
            Performs a get request using the passed url.

            Args:
                url (str): The url endpoint of the request.
                params (dict): A Dictionary containing any Query Parameters.
                add_prefix (bool): A Boolean determining whether to add the "https://api.github.com" prefix
                to the beginning of the passed url.

            Returns:
                Response: The response from the API.
        """
        if add_prefix:
            url = "https://api.github.com" + url
        return requests.get(url=url, headers=self.headers, params=params)
    
    def patch(self, url, params, add_prefix: bool = True):
        """
            Performs a patch request using the passed url.

            Args:
                url (str): The url endpoint of the request.
                params (dict): A Dictionary containing any Query Parameters.
                add_prefix (bool): A Boolean determining whether to add the "https://api.github.com" prefix
                to the beginning of the passed url.

            Returns:
                Response: The response from the API.
        """
        if add_prefix:
            url = "https://api.github.com" + url
        return requests.patch(url=url, headers=self.headers, json=params)
    
    def post(self, url, params, add_prefix: bool = True):
        """
            Performs a post request using the passed url.

            Args:
                url (str): The url endpoint of the request.
                params (dict): A Dictionary containing any Query Parameters.
                add_prefix (bool): A Boolean determining whether to add the "https://api.github.com" prefix
                to the beginning of the passed url.

            Returns:
                Response: The response from the API.
        """
        if add_prefix:
            url = "https://api.github.com" + url
        return requests.post(url=url, headers=self.headers, json=params)
    
    def delete(self, url, add_prefix: bool = True):
        """
            Performs a delete request using the passed url.

            Args:
                url (str): The url endpoint of the request.
                params (dict): A Dictionary containing any Query Parameters.
                add_prefix (bool): A Boolean determining whether to add the "https://api.github.com" prefix
                to the beginning of the passed url.

            Returns:
                Response: The response from the API.
        """
        if add_prefix:
            url = "https://api.github.com" + url

        return requests.delete(url=url, headers=self.headers)