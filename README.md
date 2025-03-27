# Zpass Telegram Bot

Добро пожаловать в **Zpass** — Telegram-бот для генерации паролей, проверки их надежности и хранения в PostgreSQL. 
Этот проект — плод моих неуклюжих попыток освоить Python, Docker и немного Telegram API. 
Если вам нужен бот для управления паролями с щепоткой хаотичного кода — вы попали по адресу!

## Описание
Этот бот умеет:
- Генерировать случайные 8-10-12 символьные пароли (чтобы вы не писали `12345678`).
- Проверять их надежность и искать в утечках через Have I Been Pwned.
- Хранить пароли в базе PostgreSQL (чтобы не забыть их на салфетке).
- Всё это упаковано в Docker-контейнеры для удобства.

**Важно:** Бот писался на **Python 3.9**, и я настоятельно рекомендую использовать эту версию для работы "из коробки". 
Если вы рискнете запустить его на Python 3.10 или новее, возможно, придется чинить что-то руками — я не профи, чтобы гарантировать совместимость!

## Установка как Docker-контейнер на Ubuntu

Если вы хотите запустить этого красавца на Ubuntu, вот пошаговая инструкция для вас. 
Предполагается, что вы уже знаете, где у вас терминал, и не боитесь командной строки. Поехали!

### Требования
- **Ubuntu** (тестировалось на 20.04/22.04, но должно работать и на других версиях).
- **Docker** и **Docker Compose** — мы их установим ниже.
- **Git** — чтобы скачать проект.
- **Telegram Bot Token** — получите у [@BotFather](https://t.me/BotFather).

### Пошаговая инструкция

1. **Обновите систему и установите зависимости:**

 sudo apt update && sudo apt upgrade -y

 sudo apt install -y git
   
3. Установите Docker:
	
 sudo apt install -y docker.io
	
 sudo systemctl start docker
	
 sudo systemctl enable docker

3. Установите Docker Compose:
	
 sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
	
 sudo chmod +x /usr/local/bin/docker-compose

4. Склонируйте репозиторий:
	
 git clone git@github.com:0ne3gghave/zpassword.git
	
 cd zpassword

5. Создайте и настройте .env:
	
 nano .env
	
 BOT_TOKEN=ваш_токен_от_BotFather
	
 PG_HOST=db
	
 PG_PORT=5432
	
 PG_USER=bot_user
	
 PG_PASSWORD=bot_password
	
 PG_DB=bot_db

6. Соберите и запустите контейнеры:
	
 sudo docker-compose up -d --build
	
7. Проверка: 
	
 sudo docker-compose ps
	
Если что-то сломалось, проверьте логи:
	
 sudo docker-compose logs

Теперь ваш Zpass готов к работе на Ubuntu! Если застрянете, пишите в issues — я не профи, но попробую помочь.

Использование
	Генерация паролей: Выберите длину и получите случайный пароль.
	Проверка паролей: Введите свой пароль, чтобы узнать, насколько он крут 	(или 	слаб).
	HIBP: Узнайте, не утек ли ваш пароль в даркнет.
	Список паролей: Храните до 1000 паролей в базе (больше — не влезет, я не 	оптимизировал).

Технические детали
	Язык: Python 3.9 (не трогайте новые версии, если не готовы чинить баги!).
	Библиотеки: Смотрите requirements.txt — там aiogram, asyncpg, pydantic и 	прочие вкусности.
	База данных: PostgreSQL 15 в отдельном контейнере.
	Контейнеры: Docker + Docker Compose для простоты развертывания.

Оговорка
	Я — не профессиональный разработчик. Этот бот собран на коленке с помощью 	"индусов с Ютуба", тематических форумов и щедрой помощи YandexGPT 	(который, 	кстати, оказался умнее меня). Если код выглядит как хаос — это 	потому, что он 	такой и есть! Но он работает, и я этим горжусь.


Благодарности
	Индусам с Ютуба: Ваши 10-часовые туториалы по Python и Docker спасли мой 	разум (и нервы).
	Тематическим форумам: Stack Overflow, вы мой лучший друг в 3 часа ночи.
	YandexGPT: Ты писал половину этого README и терпел мои глупые вопросы — 	ироничный поклон тебе, ИИ-шка!

Contributing
Если вам понравился этот бот, форкните его, доработайте и отправьте pull request. Я не кусаюсь (в отличие от багов в моем коде). Используйте его как основу для своих проектов или просто учитесь на моих ошибках!

Лицензия
MIT License — берите, ломайте, улучшайте. Всё на ваш страх и риск!
