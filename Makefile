.PHONY: dev build up down logs clean

dev:
	@echo "Starting development environment..."
	docker-compose up --build

up:
	@echo "Starting production environment..."
	docker-compose -f docker-compose.prod.yml up -d

down:
	@echo "Stopping all containers..."
	docker-compose down
	docker-compose -f docker-compose.prod.yml down

logs:
	docker-compose -f docker-compose.prod.yml logs -f

clean:
	@echo "Cleaning up..."
	rm -rf MarsVision/node_modules
	rm -rf MarsVision/dist
	find . -type d -name "__pycache__" -exec rm -r {} +