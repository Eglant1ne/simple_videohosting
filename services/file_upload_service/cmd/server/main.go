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

	// Инициализация сервисов
	minioSvc := service.NewMinIOService(cfg)
	rabbitSvc := service.NewRabbitMQService(&cfg)
	defer rabbitSvc.Close()

	// Настройка роутера
	r := chi.NewRouter()
	r.Get("/health", handler.HealthCheckHandler)
	r.Post("/upload/video", handler.UploadHandler(minioSvc, &cfg, rabbitSvc))

	log.Println("Server listening on :8080")

	if err := http.ListenAndServe(":8080", r); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
