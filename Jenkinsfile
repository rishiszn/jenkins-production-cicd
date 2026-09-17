pipeline {
    agent any

    environment {
    PATH = "/opt/homebrew/bin:/usr/local/bin:${env.PATH}"
    IMAGE_NAME = "jenkins-production-cicd"
    IMAGE_TAG = "${BUILD_NUMBER}"
    GHCR_USERNAME = credentials('ghcr-credentials')

}

    stages {
        stage('Test') {
            steps {
                sh '''
                    python3 -m venv .venv
                    .venv/bin/pip install --upgrade pip
                    .venv/bin/pip install -r requirements.txt
                    .venv/bin/pytest -q
                '''
            }
        }

        stage('Docker Environment Check') {
            steps {
                sh '''
                    whoami
                    which docker
                    docker --version
                    which syft
                    syft version
                    which trivy
                    trivy --version
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker build \
                      -t ${IMAGE_NAME}:${IMAGE_TAG} .
                '''
            }
        }

        stage('Security Scan') {
            steps {
                sh '''
                    echo "Running Trivy vulnerability scan..."

                    trivy image \
                      --severity HIGH,CRITICAL \
                      --exit-code 0 \
                      ${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }

        stage('Critical Security Gate') {
            steps {
                sh '''
                    echo "Checking for CRITICAL vulnerabilities..."

                    trivy image \
                      --severity CRITICAL \
                      --exit-code 1 \
                      ${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }
        stage('Generate SBOM') {
            steps {
                sh '''
                    echo "Generating Software Bill of Materials..."

                    syft ${IMAGE_NAME}:${IMAGE_TAG} \
                    -o spdx-json \
                    > sbom.json
                '''
            }
        }
        stage('Push to GHCR') {
    steps {
        sh '''
            echo "Logging in to GitHub Container Registry..."

            echo "$GHCR_USERNAME_PSW" | docker login ghcr.io \
  -u "$GHCR_USERNAME_USR" \
  --password-stdin

            docker tag ${IMAGE_NAME}:${IMAGE_TAG} \
              ghcr.io/rishiszn/${IMAGE_NAME}:${IMAGE_TAG}

            docker push \
              ghcr.io/rishiszn/${IMAGE_NAME}:${IMAGE_TAG}

            docker logout ghcr.io
        '''
    }
}
    }
    post {
    always {
        archiveArtifacts artifacts: 'sbom.json', fingerprint: true
    }
}
}