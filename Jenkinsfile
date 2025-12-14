pipeline {
    agent any
    
    stages {
        stage('Preparation') {
            steps {
                sh '''
                    pip3 install selenium requests pytest locust urllib3 > dependencies.log 2>&1
                    
                    chmod +x start_qemu.sh
                    chmod +x chromedriver-linux64/chromedriver
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'dependencies.log'
                }
            }
        }
        
        stage('Start qemu') {
            steps {
                sh '''
                    ./start_qemu.sh > qemu_boot.log 2>&1 &

                    sleep 120
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'qemu_boot.log'
                }
            }
        }
        
        stage('API tests') {
            steps {
                sh '''
                    python3 -m pytest redfish_api.py -v --junitxml=api_test_results.xml > api_tests.log 2>&1
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'api_tests.log, api_test_results.xml'
                    junit 'api_test_results.xml'
                }
            }
        }
        
        stage('WebUI tests') {
            steps {
                sh '''
                    python3 webui_tests.py > webui_tests_logs.txt 2>&1
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'webui_tests_logs.txt'
                }
            }
        }
        
        stage('Loading testing') {
            steps {
                sh '''
                    timeout 60 locust -f locustfile.py --headless -u 1 -r 1 -t 30s --host=https://localhost:2443 --html=load_report.html > load_test.log 2>&1
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'load_report.html, load_test.log'
                }
            }
        }
    }
    
    post {
        always {
            sh '''
                pkill -f qemu-system-arm || true
            '''
        }
    }
}