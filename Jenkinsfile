pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git 'https://github.com/<ishadamle051>/ccd_assignment5.git'
            }
        }

        stage('Build') {
            steps {
                echo 'Installing dependencies...'
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Test') {
            steps {
                echo 'Running tests...'
                sh 'pytest test_app.py'
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying app to cloud...'
                // Example: You can use Heroku CLI or AWS CLI commands here
                sh 'echo "Deployment step – configure cloud CLI here"'
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed.'
        }
    }
}
