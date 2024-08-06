# Documentation

This site uses MkDocs to build its documentation and GitHub Pages for hosting.

## Format

Documentation within this project follows the following pattern:

- A `README.md` for each component
- A `/docs` folder for the project

Each `README.md` should contain:

- A description of what the component is/does
- A list of any prerequisites
- Setup instructions
- Execution instructions
- Deployment instructions

The `/docs` folder should contain:

- A description of what the project is
- An overview of how the everything fits together in the project
- An explanation of the tech stack
- Details of the underlying dataset

A majority of the information should reside within the `/docs` directory over the `README`. The `README`s in this project should be kept for concise instructions on how to use each component. Any detailed explanation should be kept within `/docs`.

## Updating MkDocs Deployment

If changes are made within `/docs`, the GitHub Pages deployment will need to be updated. Assuming you have already installed [MkDocs](https://www.mkdocs.org/getting-started/#installation) and [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/getting-started/#installation), do the following:

1. Navigate to the projects root directory.

2. Delete the existing `/mkdocs_deployment` directory.

3. Build the MkDocs deployment.

```bash
mkdocs build
```

4. Rename the `/site` directory to `/mkdocs_deployment`. This allows git to track the build so GitHub Pages can redeploy it.

5. Commit and Push changes.

Once completed, a GitHub Action will redeploy the new build to GitHub Pages.