package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/Eglant1ne/simple_videohosting/services/video_postprocess_service/internal/config"
	"github.com/Eglant1ne/simple_videohosting/services/video_postprocess_service/internal/handler"
	"github.com/Eglant1ne/simple_videohosting/services/video_postprocess_service/internal/service"
	"github.com/go-chi/chi/v5"
)

func main() {
	cfg := config.Load()

	processor, err := service.NewVideoProcessor(&cfg)
	if err != nil {
		log.Fatalf("Failed to initialize video processor: %v", err)
	}
	defer processor.Close()

	processor.StartWorkers()
	go processor.StartConsumers()

	r := chi.NewRouter()
	r.Get("/health", handler.HealthCheckHandler)

	server := &http.Server{
		Addr:    ":8090",
		Handler: r,
	}

	done := make(chan os.Signal, 1)
	signal.Notify(done, os.Interrupt, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		log.Println("Server listening on :8090")
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("server error: %v", err)
		}
	}()

	<-done
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Fatalf("Server Shutdown Failed: %+v", err)
	}
	log.Println("Server exited properly")
}
