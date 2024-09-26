import streamlit as st
import requests
from urllib.parse import urlencode, urlparse, parse_qs
import os
import github_api_toolkit
import boto3
import boto3.exceptions
from botocore.exceptions import ClientError
org = os.getenv("GITHUB_ORG")

# GitHub App Client ID
org_client_id = os.getenv("GITHUB_APP_CLIENT_ID")

# AWS Secret Manager Secret Name for the .pem file
secret_name = os.getenv("AWS_SECRET_NAME")
secret_reigon = os.getenv("AWS_DEFAULT_REGION")

account = os.getenv("AWS_ACCOUNT_NAME")


client_id = 'Ov23liJPFTZTiHwrQiEq'
client_secret = 'SECRET_REMOVED'
authorize_url = 'https://github.com/login/oauth/authorize'
access_token_url = 'https://github.com/login/oauth/access_token'
user_api_url = 'https://api.github.com/user'
redirect_uri = 'http://localhost:8502'

session = boto3.Session()
s3 = session.client("s3")
secret_manager = session.client("secretsmanager", region_name=secret_reigon)


secret = secret_manager.get_secret_value(SecretId=secret_name)["SecretString"]

# Get updated copilot usage data from GitHub API
access_token = github_api_toolkit.get_token_as_installation(org, secret, org_client_id)
gh = github_api_toolkit.github_interface(access_token[0])


def get_access_token(code):
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': redirect_uri,
        'scope': 'user:email,read:org'
    }
    headers = {'Accept': 'application/json'}
    response = requests.post(access_token_url, data=data, headers=headers)
    response.raise_for_status()
    access_token = response.json().get('access_token')
    st.session_state.access_token = access_token
    return access_token


def get_user_profile(access_token):
    headers = {'Authorization': f'token {access_token}'}
    response = requests.get(user_api_url, headers=headers)
    response.raise_for_status()
    return response.json()



st.title('GitHub OAuth2 Login Example')

if 'profile' not in st.session_state:
    st.session_state.profile = None

if st.session_state.profile is None:
    login_url = f"{authorize_url}?{urlencode({'client_id': client_id, 'redirect_uri': redirect_uri, 'scope': 'user:email'})}"
    st.markdown(f"[Login with GitHub]({login_url})")

    query_params = st.query_params
    if 'code' in query_params:
        code = query_params['code']
        try:
            access_token = get_access_token(code)
            profile = get_user_profile(access_token)
            st.session_state.profile = profile
            st.query_params.clear()
            st.success(f"Hello, {profile['login']}!")
        except Exception as e:
            st.error(f"Error during login: {e}")
else:
    profile = st.session_state.profile
    st.success(f"Hello, {profile['login']}!")
    st.json(profile)


def get_user_orgs(access_token, username):
    headers = {'Authorization': f'token {access_token}'}
    orgs_url = f'https://api.github.com/users/{username}/orgs'
    response = requests.get(orgs_url, headers=headers)
    response.raise_for_status()
    return response.json()

if st.session_state.profile:
    orgs = get_user_orgs(st.session_state.access_token, st.session_state.profile['login'])
    st.write("Your Organizations:")
    for org in orgs:
        st.markdown(f"- [{org['login']}]({org['html_url']})")


def is_user_in_org(username, org):
    orgs = gh.get(f'/orgs/{org}/members/{username}')

    return orgs.status_code == 204

if st.session_state.profile:
    if is_user_in_org(st.session_state.profile['login'], 'ONSDigital'):
        st.write(f"In {org}!")
        team_slug = st.text_input("Enter team name:")
        if st.button("Check Team"):
            def check_repository(repo_name):
                try:
                    repo = gh.get(f'/orgs/{org}/teams/{team_slug}/memberships/{st.session_state.profile['login']}')
                    if repo.status_code == 200:
                        st.success(f"User is in team.")
                    else:
                        st.error(f"Error.")
                except Exception as e:
                    st.error(f"Error checking repository: {e}")

            check_repository(team_slug)
    else:
        st.write("Not in org.")