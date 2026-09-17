pipeline {
    agent any

environment {
PATH = "/usr/local/bin:${env.PATH}"
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
	    stage('Docker Environment Check'){
		    steps{
                sh ''' 
                    whoami
                    which docker
                    docker --version
                '''
            }
        }
	    stage('Docker Build') {
		    steps{
			    sh 'docker build -t jenkins-production-cicd:v1 .'
            }
        }
    }
}
