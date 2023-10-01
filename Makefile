doc-build:
	redoc-cli bundle ./docs/openapi.yml --output ./docs/redoc.html

deploy_dev:
	docker-compose up --build -d
	docker-compose exec serverless bash -c "sls deploy -s dev"
	docker-compose stop
