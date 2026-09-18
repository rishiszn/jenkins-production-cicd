pipeline {
    agent any

    options {
    disableConcurrentBuilds()
}

parameters {
    booleanParam(
        name: 'FORCE_HEALTH_FAILURE',
        defaultValue: false,
        description: 'Demo only: force /health to fail and validate automatic rollback.'
    )
}

    environment {
    PATH = "/opt/homebrew/bin:/usr/local/bin:${env.PATH}"
    IMAGE_NAME = "jenkins-production-cicd"
    IMAGE_TAG = "${BUILD_NUMBER}"
    GHCR_USERNAME = credentials('ghcr-credentials')
    DEPLOYED_IMAGE = "ghcr.io/rishiszn/jenkins-production-cicd:${BUILD_NUMBER}"

}

    stages {
        stage('Initialize') {
    steps {
        sh 'rm -f previous_image.txt'
    }
}
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
stage('Deploy') {
    steps {
        withCredentials([usernamePassword(
            credentialsId: 'ghcr-credentials',
            usernameVariable: 'GHCR_USERNAME',
            passwordVariable: 'GHCR_PASSWORD'
        )]) {
            sh '''
                echo "Preparing deployment..."

                if docker inspect jenkins-cicd-app >/dev/null 2>&1; then
                    docker inspect jenkins-cicd-app \
                        --format '{{.Config.Image}}' > previous_image.txt

                    echo "Previous image:"
                    cat previous_image.txt
                else
                    echo "No previous deployment found."
                    echo "NONE" > previous_image.txt
                fi

                echo "$GHCR_PASSWORD" | docker login ghcr.io \
                    -u "$GHCR_USERNAME" \
                    --password-stdin

                docker pull ${DEPLOYED_IMAGE}

                docker stop jenkins-cicd-app || true
                docker rm jenkins-cicd-app || true

                docker run -d \
    --name jenkins-cicd-app \
    -p 5001:5000 \
    -e FORCE_HEALTH_FAILURE="${FORCE_HEALTH_FAILURE:-false}" \
    ${DEPLOYED_IMAGE}

docker logout ghcr.io

                docker logout ghcr.io

                echo "Application deployed successfully."
                docker ps --filter "name=jenkins-cicd-app"
            '''
        }
    }
}
stage('Health Check') {
    steps {
        sh '''
            echo "Running application health check..."

            sleep 3

            curl --fail --silent --show-error \
                http://localhost:5001/health

            echo ""
            echo "Health check passed."
        '''
    }
}
    }
   post {
    failure {
        script {
            if (fileExists('previous_image.txt')) {
                def previousImage = readFile('previous_image.txt').trim()

                if (previousImage != "NONE") {
                    echo "Deployment failed. Starting rollback..."
                    echo "Rolling back to: ${previousImage}"

                    withCredentials([usernamePassword(
                    credentialsId: 'ghcr-credentials',
                    usernameVariable: 'GHCR_USERNAME',
                    passwordVariable: 'GHCR_PASSWORD')])         
            {
                withEnv(["ROLLBACK_IMAGE=${previousImage}"]) {
                sh '''
                echo "$GHCR_PASSWORD" | docker login ghcr.io \
                -u "$GHCR_USERNAME" \
                --password-stdin

            docker pull "$ROLLBACK_IMAGE"

            docker stop jenkins-cicd-app || true
            docker rm jenkins-cicd-app || true

            docker run -d \
                --name jenkins-cicd-app \
                -p 5001:5000 \
                -e FORCE_HEALTH_FAILURE=false \
                "$ROLLBACK_IMAGE"

            docker logout ghcr.io

            echo "Rollback container started."

            sleep 3

            curl --fail --silent --show-error \
                http://localhost:5001/health

            echo ""
            echo "Rollback health check passed."
        '''
    }
}
                } else {
                    echo "No previous deployment available for rollback."
                }
            } else {
                echo "No previous_image.txt found. Rollback unavailable."
            }
        }
    }

    always {
        archiveArtifacts artifacts: 'sbom.json,previous_image.txt',
            fingerprint: true,
            allowEmptyArchive: true
    }
}
}