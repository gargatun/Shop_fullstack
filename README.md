
# Магазин Bigcorp

## Описание
Магазин Bigcorp - это проект на Django с API и различными функциями.

## Установка
Для запуска проекта выполните следующие шаги:
1. Соберите проект локально с помощью Docker Compose:
   ```sh
   docker-compose build
   ```

2. Запустите проект:
   ```sh
   docker-compose up
   ```

## Использование
1. После запуска проекта создайте суперпользователя командой:
   ```sh
   docker-compose exec backend python manage.py createsuperuser
   ```

2. Доступ к административному интерфейсу осуществляется через браузер. Войдите в административную панель и вручную создайте хотя бы одну категорию для товаров.

3. Сгенерируйте фиктивные продукты с помощью команды:
   ```sh
   docker-compose exec backend python manage.py fakeproducts
   ```

## Используемые технологии
Проект создан с использованием следующих технологий:
- Python
- JavaScript
- Ajax
- CSS
- HTML
- Postgres
- Celery Beat
- Celery Result
- Celery
- Redis Broker
- Django Htmx
- Nginx
- Gunicorn
- API
- Swagger и Redoc Docs
- Celery Flower
- Stripe
- Yookassa
- Django Rest Framework
- Docker
- Docker Compose
- GitHub Actions
- Git
