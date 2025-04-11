package main

import (
	"log"
	"net/http"

	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/service"
	"github.com/go-chi/chi/v5"
)

func main() {
	cfg := config.Load()
	s3svc := service.NewS3Service(cfg)

	r := chi.NewRouter()
	r.Post("/upload", handler.fileUploadHandler(s3svc))
	r.Post("/upload/chunk", handler.uploadFileInChunks(s3svc))

	log.Println("Server listening on :8080")
	log.Fatal(http.ListenAndServe(":8080", r))
}
