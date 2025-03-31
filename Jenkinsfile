pipeline {
    agent any
    
    environment {
        DOCKER_IMAGE = 'viewtrain-app'
        DOCKER_TAG = "${BUILD_NUMBER}"
        DOCKER_REGISTRY = 'your-registry.com'  // Замените на ваш Docker registry
        SERVER_HOST = 'your-server.com'        // Замените на адрес вашего сервера
        SERVER_USER = 'deploy'                 // Замените на пользователя для деплоя
        APP_DIR = '/opt/viewtrain'             // Директория приложения на сервере
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh '''
                    python -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Run Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest
                '''
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                    docker.tag("${DOCKER_IMAGE}:${DOCKER_TAG}", "${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}")
                    docker.push("${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG}")
                }
            }
        }
        
        stage('Deploy to Server') {
            steps {
                sh '''
                    # Копируем файлы на сервер
                    rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '.git' \
                        ./ ${SERVER_USER}@${SERVER_HOST}:${APP_DIR}/
                    
                    # Подключаемся к серверу и выполняем необходимые команды
                    ssh ${SERVER_USER}@${SERVER_HOST} << 'EOF'
                        cd ${APP_DIR}
                        
                        # Активируем виртуальное окружение
                        source venv/bin/activate
                        
                        # Устанавливаем зависимости
                        pip install -r requirements.txt
                        
                        # Применяем миграции
                        alembic upgrade head
                        
                        # Перезапускаем сервис
                        sudo systemctl restart viewtrain
                        
                        # Проверяем статус
                        sudo systemctl status viewtrain
                    EOF
                '''
            }
        }
        
        stage('Health Check') {
            steps {
                sh '''
                    # Ждем, пока приложение запустится
                    sleep 10
                    
                    # Проверяем доступность API
                    curl -f http://${SERVER_HOST}/api/health || exit 1
                '''
            }
        }
    }
    
    post {
        always {
            // Очищаем Docker образы
            sh 'docker system prune -f'
        }
        success {
            echo 'Деплой успешно завершен!'
        }
        failure {
            echo 'Деплой завершился с ошибкой!'
        }
    }
} 