#backend
docker run -p 5010:8080 --env-file .env 823e328064bce4328d0e5add5499931ab81b8a09474c5633bf91979f0dbc4e03 

#frontend
docker run -p 5173:8080 385848d3d645744c2ddb345a18b4a7230278d03f559f4eed975ad9dff1ca3d30

#local build
#backend
docker build -t api:1.1.1 .

# gcloud build backend
../../.././google-cloud-sdk/bin/gcloud builds submit --region=global --tag gcr.io/portal-reclutamiento/api:v1.1.1

#gcloud build frontend
../../.././google-cloud-sdk/bin/gcloud builds submit --region=global --tag gcr.io/portal-reclutamiento/frontend:v1.1.1

# Para correr el backend local en un dev container
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080 

../../.././google-cloud-sdk/bin/gcloud builds submit --region=global --tag gcr.io/portal-reclutamiento/vacante_update:v1.0.0
