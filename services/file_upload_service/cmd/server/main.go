package main

import (
	"log"
	"net/http"

	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/handler"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/service"
	"github.com/go-chi/chi/v5"
)

func main() {
	cfg := config.Load()

	minioSvc := service.NewMinIOService(cfg)

	r := chi.NewRouter()

	r.Post("/upload", handler.FileUploadHandler(minioSvc))
	r.Post("/upload/chunk", handler.UploadFileInChunks(minioSvc))

	log.Println("Server listening on :8080")
	if err := http.ListenAndServe(":8080", r); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
