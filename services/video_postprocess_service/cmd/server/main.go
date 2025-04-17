package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/Eglant1ne/simple_videohosting/services/video_postprocess_service/internal/config"
	"github.com/Eglant1ne/simple_videohosting/services/video_postprocess_service/internal/handler"
	"github.com/Eglant1ne/simple_videohosting/services/video_postprocess_service/internal/service"
	"github.com/go-chi/chi/v5"
)

type VideoEvent struct {
	VideoPath string `json:"video_path"`
	UUID      string `json:"uuid"`
}

func main() {
	cfg := config.Load()
	//healthcheck
	r.Get("/health", handler.HealthCheckHandler)

	log.Println("Server listening on :8090")

	if err := http.ListenAndServe(":8090", r); err != nil {
		log.Fatalf("server error: %v", err)
	}

}
