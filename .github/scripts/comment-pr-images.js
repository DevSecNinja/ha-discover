/**
 * Comment on PR with Docker image pull commands
 * This script is used by the pr-images workflow to post a comment with Docker image details
 *
 * @param {Object} github - Pre-authenticated GitHub API client
 * @param {Object} context - GitHub Actions context
 * @param {string} version - The version tag for the images
 */
module.exports = async ({ github, context, version }) => {
  const registry = "ghcr.io";
  const repo = `${context.repo.owner.toLowerCase()}/${context.repo.repo.toLowerCase()}`;

  const backendImage = `${registry}/${repo}/backend:${version}`;
  const frontendImage = `${registry}/${repo}/frontend:${version}`;

  const comment = `## 🐳 Docker Images Published

The following Docker images have been built and published for this PR:

### Backend
\`\`\`bash
docker pull ${backendImage}
\`\`\`

### Frontend
\`\`\`bash
docker pull ${frontendImage}
\`\`\`

### Test the PR build
\`\`\`bash
# Test backend
docker run -d -p 8000:8000 -e ENVIRONMENT=development ${backendImage}
curl http://localhost:8000/api/v1/health

# Test frontend
docker run -d -p 8080:80 ${frontendImage}
curl http://localhost:8080/hadiscover/
\`\`\`

### Using docker-compose
\`\`\`yaml
services:
  backend:
    image: ${backendImage}
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development

  frontend:
    image: ${frontendImage}
    ports:
      - "8080:80"
\`\`\`

---
*Images are tagged with \`${version}\` and will be retained for testing purposes.*`;

  await github.rest.issues.createComment({
    issue_number: context.issue.number,
    owner: context.repo.owner,
    repo: context.repo.repo,
    body: comment,
  });
};
