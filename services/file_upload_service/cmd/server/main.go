package main

import (
	"fmt"
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

	producer, err := service.NewKafkaProducer([]string{"kafka:9092"})
	if err != nil {
		fmt.Println("Error loading kafka")
	}
	log.Println("unprocessed_video_uploaded ")
	kafkaTopic := "video-uploads"
	defer producer.Close()

	r := chi.NewRouter()
	//healthcheck
	r.Get("/health", handler.HealthCheckHandler)

	r.Post("/upload/video", handler.UploadHandler(minioSvc, &cfg, producer, kafkaTopic))

	log.Println("Server listening on :8080")

	if err := http.ListenAndServe(":8080", r); err != nil {
		log.Fatalf("server error: %v", err)
	}

}
