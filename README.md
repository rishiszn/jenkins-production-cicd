# Production-Grade Jenkins CI/CD Pipeline

A production-oriented CI/CD project demonstrating automated testing,
Docker image builds, security scanning, SBOM generation, container
registry publishing, deployment, health checks, and automatic rollback.

## 1. Project Overview

This project implements a CI/CD pipeline using:

-   **GitHub** --- source-code repository
-   **Jenkins** --- CI/CD automation server
-   **Python + Flask** --- demonstration application
-   **Pytest** --- automated testing
-   **Docker** --- application containerization
-   **Trivy** --- container vulnerability scanning
-   **Syft** --- Software Bill of Materials (SBOM) generation
-   **GitHub Container Registry (GHCR)** --- Docker image registry
-   **cURL** --- deployment health verification

### Pipeline Flow

``` text
Developer
    |
    v
 GitHub
    |
    v
 Jenkins
    |
    +--> Test
    |
    +--> Docker Build
    |
    +--> Trivy Security Scan
    |
    +--> Critical Vulnerability Gate
    |
    +--> SBOM Generation
    |
    +--> Push Image -> GHCR
    |
    +--> Deploy Container
    |
    +--> Health Check
             |
        +----+----+
        |         |
       PASS      FAIL
        |         |
        v         v
     Success   Rollback
```

------------------------------------------------------------------------

## 2. Repository Structure

``` text
jenkins-production-cicd/
|
+-- app/
|   +-- app.py
|
+-- tests/
|   +-- test_app.py
|
+-- requirements.txt
+-- Dockerfile
+-- .dockerignore
+-- .gitignore
+-- Jenkinsfile
+-- sbom.json
```

  -----------------------------------------------------------------------
  File                                Purpose
  ----------------------------------- -----------------------------------
  `app/app.py`                        Flask application

  `tests/test_app.py`                 Automated tests

  `requirements.txt`                  Python dependencies

  `Dockerfile`                        Builds the application container

  `.dockerignore`                     Excludes unnecessary files from
                                      Docker build context

  `.gitignore`                        Excludes unwanted Git files

  `Jenkinsfile`                       Defines the CI/CD pipeline

  `sbom.json`                         Generated SPDX SBOM artifact
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 3. Application

The project uses a small Flask application designed to demonstrate CI/CD
and deployment behavior.

### Endpoints

``` text
GET /
GET /health
```

The `/` endpoint returns application information.

The `/health` endpoint returns:

``` json
{
  "status": "healthy"
}
```

The application also supports a controlled failure mode using:

``` text
FORCE_HEALTH_FAILURE
```

When the variable is `false`, `/health` returns HTTP 200.

When it is `true`, `/health` returns HTTP 500.

This allows the rollback mechanism to be tested without modifying the
application code.

------------------------------------------------------------------------

# 4. Git and GitHub

Git provides version control and GitHub acts as the source repository
for the project.

### Initialize Git

``` bash
mkdir ~/jenkins-production-cicd
cd ~/jenkins-production-cicd
git init
```

### Check status

``` bash
git status
```

### Stage files

``` bash
git add .
```

or:

``` bash
git add Jenkinsfile
```

### Commit

``` bash
git commit -m "commit message"
```

### Add remote

``` bash
git remote add origin https://github.com/rishiszn/jenkins-production-cicd.git
```

### Push

``` bash
git push origin main
```

### Importance

Git provides:

-   Version control
-   Change history
-   Reproducibility
-   Collaboration
-   A source for Jenkins builds

The Jenkinsfile is also version-controlled with the application.

------------------------------------------------------------------------

# 5. Python and Automated Testing

The application is written using Python and Flask.

Dependencies:

``` text
Flask
pytest
```

### Create virtual environment

``` bash
python3 -m venv .venv
```

### Install dependencies

``` bash
.venv/bin/pip install -r requirements.txt
```

### Run tests

``` bash
.venv/bin/pytest -q
```

The project currently contains three tests.

Expected result:

``` text
3 passed
```

### Why automated testing?

The Test stage prevents the pipeline from continuing when application
tests fail.

``` text
Code
 |
 v
Tests
 |
 +-- PASS --> Continue
 |
 +-- FAIL --> Stop Pipeline
```

------------------------------------------------------------------------

# 6. Docker

Docker packages the application and its runtime dependencies into a
portable container image.

### Check Docker

``` bash
docker --version
```

The Jenkins environment used Docker 28.3.2.

### Build an image

``` bash
docker build -t jenkins-production-cicd:1 .
```

Jenkins uses the build number as the image tag:

``` text
jenkins-production-cicd:${BUILD_NUMBER}
```

For example:

``` text
jenkins-production-cicd:29
```

### Useful Docker commands

``` bash
docker images
docker ps
docker ps -a
docker logs jenkins-cicd-app
docker stop jenkins-cicd-app
docker rm jenkins-cicd-app
```

### Importance

Docker provides:

-   Consistent runtime environments
-   Application isolation
-   Reproducible builds
-   Versioned application images
-   Portable deployment

------------------------------------------------------------------------

# 7. Container Security

The Dockerfile creates a dedicated application user:

``` text
appuser
UID 10001
```

and runs the application using:

``` dockerfile
USER appuser
```

The application therefore does not run as root inside the container.

This reduces the impact of a potential container compromise compared
with running the application as root.

------------------------------------------------------------------------

# 8. Trivy Security Scanning

Trivy scans the Docker image for known vulnerabilities.

### Check installation

``` bash
which trivy
trivy --version
```

The Jenkins environment used Trivy 0.74.0.

### Informational scan

``` bash
trivy image \
  --severity HIGH,CRITICAL \
  --exit-code 0 \
  jenkins-production-cicd:${BUILD_NUMBER}
```

This scan reports HIGH and CRITICAL vulnerabilities but does not stop
the pipeline.

### Critical security gate

``` bash
trivy image \
  --severity CRITICAL \
  --exit-code 1 \
  jenkins-production-cicd:${BUILD_NUMBER}
```

The configured behavior is:

``` text
0 CRITICAL vulnerabilities -> PASS
CRITICAL vulnerabilities   -> FAIL
```

The recent pipeline run reported:

``` text
HIGH:     44
CRITICAL: 0
```

Therefore, the configured CRITICAL security gate passed.

> Important: `0 CRITICAL` does not mean the image contains zero
> vulnerabilities. HIGH findings were still present.

### Importance

Trivy adds a security gate before an image is published and deployed.

------------------------------------------------------------------------

# 9. Syft and SBOM

Syft generates a Software Bill of Materials (SBOM) for the Docker image.

### Check installation

``` bash
which syft
syft version
```

The Jenkins environment used Syft 1.52.0.

### Generate SPDX JSON SBOM

``` bash
syft jenkins-production-cicd:${BUILD_NUMBER} \
  -o spdx-json \
  > sbom.json
```

The resulting file is:

``` text
sbom.json
```

### What is an SBOM?

An SBOM is an inventory of software components contained in an
application image.

Conceptually:

``` text
Docker Image
    |
    +-- Python
    +-- Flask
    +-- Python dependencies
    +-- OS packages
    +-- Other components
```

### Importance

SBOMs improve:

-   Software supply-chain visibility
-   Dependency tracking
-   Vulnerability investigation
-   Software transparency

The SBOM is archived as a Jenkins build artifact.

------------------------------------------------------------------------

# 10. GitHub Container Registry

GitHub Container Registry (GHCR) stores the Docker images produced by
Jenkins.

Image format:

``` text
ghcr.io/rishiszn/jenkins-production-cicd:<TAG>
```

Example:

``` text
ghcr.io/rishiszn/jenkins-production-cicd:29
```

### Authentication

Jenkins stores the GHCR credentials in its Credentials Manager.

Credential ID:

``` text
ghcr-credentials
```

The pipeline uses secure credential binding and passes the password
through:

``` bash
--password-stdin
```

Secrets are not hard-coded into the Jenkinsfile.

### Push image

``` bash
docker push \
  ghcr.io/rishiszn/jenkins-production-cicd:${BUILD_NUMBER}
```

### Pull image

``` bash
docker pull \
  ghcr.io/rishiszn/jenkins-production-cicd:<TAG>
```

### Importance

The registry provides a centralized location for immutable, versioned
application images.

The deployment pulls the exact image produced by the CI build rather
than rebuilding the application during deployment.

------------------------------------------------------------------------

# 11. Jenkins

Jenkins is responsible for automating the complete CI/CD workflow.

The pipeline is defined in:

``` text
Jenkinsfile
```

This is **Pipeline as Code**.

Instead of manually configuring every build step in Jenkins, the
pipeline definition is stored alongside the application code.

------------------------------------------------------------------------

# 12. Jenkins Pipeline Stages

The pipeline contains the following stages:

``` text
Initialize
    |
    v
Test
    |
    v
Docker Environment Check
    |
    v
Docker Build
    |
    v
Security Scan
    |
    v
Critical Security Gate
    |
    v
Generate SBOM
    |
    v
Push to GHCR
    |
    v
Deploy
    |
    v
Health Check
```

------------------------------------------------------------------------

# 13. Initialize Stage

The pipeline removes stale rollback information:

``` bash
rm -f previous_image.txt
```

This ensures rollback state belongs to the current build.

------------------------------------------------------------------------

# 14. Docker Environment Check

Jenkins verifies that the required tools are accessible from its
environment.

Commands:

``` bash
whoami
which docker
docker --version
which syft
syft version
which trivy
trivy --version
```

### Importance

A tool installed on the developer machine is not automatically available
to Jenkins.

This stage confirms that Jenkins can actually execute Docker, Syft, and
Trivy.

------------------------------------------------------------------------

# 15. Image Versioning

Jenkins uses:

``` text
BUILD_NUMBER
```

as the Docker image tag.

For example:

``` text
Build #20 -> image :20
Build #21 -> image :21
Build #28 -> image :28
Build #29 -> image :29
```

This creates a direct relationship between:

``` text
Jenkins Build
     |
     v
Docker Image
     |
     v
Deployment
```

This makes deployments easier to trace and rollback.

------------------------------------------------------------------------

# 16. Deployment

The deployment uses the image stored in GHCR.

``` bash
docker run -d \
  --name jenkins-cicd-app \
  -p 5001:5000 \
  -e FORCE_HEALTH_FAILURE="${FORCE_HEALTH_FAILURE:-false}" \
  ${DEPLOYED_IMAGE}
```

### Port mapping

``` text
Host                  Container
5001  ----------------> 5000
```

Host port 5001 is used because port 5000 was already occupied on the
development machine.

------------------------------------------------------------------------

# 17. Health Check

After deployment, Jenkins waits briefly:

``` bash
sleep 3
```

Then checks:

``` bash
curl --fail --silent --show-error \
  http://localhost:5001/health
```

Expected response:

``` json
{"status":"healthy"}
```

If the application returns HTTP 500, `curl --fail` causes the Health
Check stage to fail.

Therefore, deployment success is not based only on whether the Docker
container started. Jenkins verifies that the application itself is
responding correctly.

------------------------------------------------------------------------

# 18. Automatic Rollback

Before replacing an existing deployment, Jenkins records the currently
deployed image.

Command:

``` bash
docker inspect jenkins-cicd-app \
  --format '{{.Config.Image}}'
```

The result is stored in:

``` text
previous_image.txt
```

Example:

``` text
ghcr.io/rishiszn/jenkins-production-cicd:21
```

If the new deployment fails its health check:

``` text
New Image
   |
   v
Deploy
   |
   v
Health Check
   |
   X
Failure
   |
   v
Read previous_image.txt
   |
   v
Pull previous image
   |
   v
Stop failed container
   |
   v
Remove failed container
   |
   v
Start previous image
   |
   v
Rollback Health Check
```

The previous image is restored automatically.

------------------------------------------------------------------------

# 19. Failure Demonstration

The pipeline includes a Jenkins parameter:

``` text
FORCE_HEALTH_FAILURE
```

Default:

``` text
false
```

### Normal deployment

Leave the parameter unchecked.

``` text
FORCE_HEALTH_FAILURE=false
```

Expected:

``` text
Health Check -> HTTP 200
Pipeline     -> SUCCESS
```

### Failure demonstration

Check the parameter.

``` text
FORCE_HEALTH_FAILURE=true
```

Expected:

``` text
Deploy
  |
  v
Health Check -> HTTP 500
  |
  v
Pipeline failure
  |
  v
Automatic rollback
  |
  v
Previous image
  |
  v
Rollback health check -> HTTP 200
```

This was tested successfully during the project.

------------------------------------------------------------------------

# 20. Jenkins Credentials

GHCR authentication is managed through Jenkins Credentials Manager.

Credential ID:

``` text
ghcr-credentials
```

The pipeline accesses the credentials through Jenkins credential
binding.

The registry password/token is never hard-coded into the source
repository.

Good practice:

``` text
Source Code
    |
    +-- No secrets
    |
Jenkins Credentials
    |
    +-- GHCR authentication
```

------------------------------------------------------------------------

# 21. Jenkins Artifacts

The pipeline archives:

``` text
sbom.json
previous_image.txt
```

These artifacts can be associated with the Jenkins build for later
inspection.

------------------------------------------------------------------------

# 22. .dockerignore

The Docker build context excludes unnecessary files such as:

``` text
.git
.venv
__pycache__
.pytest_cache
```

This helps keep the build context clean and avoids copying
development-only files into the image.

Benefits include:

-   Smaller build context
-   Faster builds
-   Less unnecessary data
-   Reduced potential attack surface

------------------------------------------------------------------------

# 23. Complete Command Cheat Sheet

## Git

``` bash
git init
git status
git add .
git commit -m "message"
git remote -v
git push origin main
```

## Python / Testing

``` bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pytest -q
```

## Docker

``` bash
docker --version
docker build -t jenkins-production-cicd:1 .
docker images
docker ps
docker ps -a
docker logs jenkins-cicd-app
docker stop jenkins-cicd-app
docker rm jenkins-cicd-app
```

## GHCR

``` bash
docker login ghcr.io
docker push ghcr.io/rishiszn/jenkins-production-cicd:<TAG>
docker pull ghcr.io/rishiszn/jenkins-production-cicd:<TAG>
```

## Trivy

``` bash
trivy --version

trivy image \
  --severity HIGH,CRITICAL \
  <IMAGE>

trivy image \
  --severity CRITICAL \
  --exit-code 1 \
  <IMAGE>
```

## Syft

``` bash
syft version

syft <IMAGE> \
  -o spdx-json \
  > sbom.json
```

## Health Check

``` bash
curl http://localhost:5001/health
```

or:

``` bash
curl --fail --silent --show-error \
  http://localhost:5001/health
```

------------------------------------------------------------------------

# 24. Tool Importance Summary

  -----------------------------------------------------------------------
  Tool                    Role                    Importance
  ----------------------- ----------------------- -----------------------
  Git                     Version control         Tracks source and
                                                  pipeline changes

  GitHub                  Source repository       Stores application and
                                                  Jenkinsfile

  Jenkins                 CI/CD automation        Orchestrates the
                                                  complete workflow

  Python                  Application runtime     Runs the Flask
                                                  application

  Flask                   Web framework           Provides application
                                                  endpoints

  Pytest                  Testing                 Prevents failed code
                                                  from progressing

  Docker                  Containerization        Packages application
                                                  consistently

  Trivy                   Security scanning       Detects container
                                                  vulnerabilities

  Syft                    SBOM generation         Provides software
                                                  supply-chain inventory

  GHCR                    Image registry          Stores versioned Docker
                                                  images

  cURL                    Health checking         Validates the running
                                                  application

  Jenkins Credentials     Secret management       Protects registry
                                                  credentials
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 25. Why This Project Is Production-Oriented

This project goes beyond a basic:

``` text
GitHub -> Jenkins -> Build
```

pipeline.

It demonstrates:

-   Automated application testing
-   Containerized builds
-   Versioned Docker images
-   Security scanning
-   A CRITICAL vulnerability gate
-   SBOM generation
-   Secure registry authentication
-   Container deployment
-   Post-deployment health verification
-   Automatic rollback
-   Controlled failure testing
-   Jenkins artifact archiving
-   Non-root container execution
-   Pipeline as Code

The most important reliability demonstration is that both the **success
path** and **failure/recovery path** were tested.

------------------------------------------------------------------------

# 26. Interview Explanation

A concise explanation for interviews:

> I built a production-oriented CI/CD pipeline using Jenkins, GitHub,
> Docker, Trivy, Syft and GitHub Container Registry. Every change is
> tested using pytest, after which Jenkins builds a versioned Docker
> image. Trivy performs vulnerability scanning with a CRITICAL-severity
> security gate, while Syft generates an SPDX SBOM. The image is then
> pushed to GHCR and deployed as a Docker container. Jenkins performs an
> HTTP health check after deployment. I also implemented automatic
> rollback by recording the previously deployed image and restoring it
> when the new deployment fails its health check. I tested both the
> successful deployment path and an intentional health-check failure to
> verify that the rollback mechanism works.

------------------------------------------------------------------------

# 27. Final Architecture

``` text
                       +----------------+
                       |     GitHub     |
                       | Source Control |
                       +-------+--------+
                               |
                               v
                    +---------------------+
                    |       Jenkins       |
                    |   Pipeline as Code  |
                    +----------+----------+
                               |
              +----------------+----------------+
              |                |                |
              v                v                v
          Pytest           Docker Build      Trivy
              |                |                |
              +----------------+----------------+
                               |
                               v
                         Critical Gate
                               |
                               v
                             Syft
                               |
                               v
                            SBOM
                               |
                               v
                    +---------------------+
                    |        GHCR         |
                    |   Docker Registry   |
                    +----------+----------+
                               |
                               v
                         Docker Deploy
                               |
                               v
                         Health Check
                               |
                    +----------+----------+
                    |                     |
                   PASS                  FAIL
                    |                     |
                    v                     v
                 SUCCESS              ROLLBACK
                                          |
                                          v
                                  Previous Image
                                          |
                                          v
                                  Health Check
```

------------------------------------------------------------------------

# 28. Project Status

``` text
Jenkins Production CI/CD

████████████████████████████ 100%

✓ Application
✓ Automated Tests
✓ Docker
✓ Non-root Container
✓ Jenkins Pipeline
✓ Trivy Security Scan
✓ Critical Security Gate
✓ SBOM
✓ GHCR Publishing
✓ Deployment
✓ Health Check
✓ Automatic Rollback
✓ Failure Demonstration
✓ Successful Baseline
✓ Documentation
```

## Conclusion

The project demonstrates a complete CI/CD lifecycle:

``` text
Code
 ↓
Test
 ↓
Build
 ↓
Secure
 ↓
Generate SBOM
 ↓
Publish
 ↓
Deploy
 ↓
Verify
 ↓
Rollback if necessary
```

This repository can now be presented as a practical Jenkins CI/CD
portfolio project rather than a simple Jenkins installation exercise.
