COMPOSE = docker compose

.PHONY: flags up down ps logs up-day1 up-day2 up-client up-injection up-auth up-logic up-server up-jsp up-capstone

flags:        ## 랜덤 플래그 .env 생성
	./gen_flags.sh

up:           ## 전체 기동 (platform + bot + 모든 문제)
	$(COMPOSE) --profile all up -d --build

down:         ## 전체 종료
	$(COMPOSE) --profile all down

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

up-day1:
	$(COMPOSE) --profile day1 up -d --build
up-day2:
	$(COMPOSE) --profile day2 up -d --build
up-client:
	$(COMPOSE) --profile client up -d --build
up-injection:
	$(COMPOSE) --profile injection up -d --build
up-auth:
	$(COMPOSE) --profile auth up -d --build
up-logic:
	$(COMPOSE) --profile logic up -d --build
up-server:
	$(COMPOSE) --profile server up -d --build
up-jsp:
	$(COMPOSE) --profile jsp up -d --build
up-capstone:
	$(COMPOSE) --profile capstone up -d --build
