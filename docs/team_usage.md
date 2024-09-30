# CoPilot Team Usage

## Overview
This section of the project leverages GitHub OAuth2 for user authentication, granting access to essential data.

The tech stack and UI is the same as the Organization Usage.

### Requirements for Team CoPilot Usage
To retrieve data, a team must meet the following criteria:

- At least 5 members with active CoPilot licenses.
- These 5 users must be active for a minimum of 1 day.

## Access
### Flow & Session
When on the team usage page, a `Login with GitHub` is displayed. Once clicked on, the user is taken to GitHub's authorisation page. The permissions **read-only** personal user data and **read-only** organizations and teams are required for this application. Clicking on the green `Authorize` button takes the user back to the application. 

The session is saved to streamlit's `session_state`. For security, the session resets after refresh but not when navigating between pages. This means the user has to press the `Login with GitHub` button each page refresh.

### Types of Access
#### Regular User
A user within ONSDigital. Upon authentication, the app identifies the teams they belong to and populates the selection box accordingly. If the user is part of a qualifying team, they can view the data. Users not associated with any team cannot select teams.

#### Admin User
An enhanced regular user with the ability to search for any team. This user belongs to a specific whitelisted team, enabling them to view metrics for any team that meets the CoPilot usage data requirements.
