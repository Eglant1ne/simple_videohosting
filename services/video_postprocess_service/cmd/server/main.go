package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/Eglant1ne/simple_videohosting/services/video_postprocess_service/internal/handler"
	"github.com/Eglant1ne/simple_videohosting/services/video_postprocess_service/internal/service"
	"github.com/go-chi/chi/v5"
)

func main() {
	//cfg := config.Load()

	//minioSvc := service.NewMinIOService(cfg)

	producer, err := service.NewKafkaProducer([]string{"kafka:9092"})
	if err != nil {
		fmt.Println("Error loading kafka")
	}
	log.Println("Kafka is loaded ")
	//kafkaTopic := "confirm_video_hls_converting"
	defer producer.Close()

	r := chi.NewRouter()
	//healthcheck
	r.Get("/health", handler.HealthCheckHandler)

	log.Println("Server listening on :8090")

	if err := http.ListenAndServe(":8090", r); err != nil {
		log.Fatalf("server error: %v", err)
	}

}
