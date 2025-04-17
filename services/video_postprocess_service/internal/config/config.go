package config

import (
	"os"
	"strconv"
	"strings"
)

type Config struct {
	DebugMode      bool
	Bucket         string
	Region         string
	Endpoint       string
	AccessKey      string
	SecretKey      string
	ConsumeWorkers int
	RabbitmqUser   string
	RabbitmqPass   string
}

func Load() Config {
	brokers := strings.Split(os.Getenv("KAFKA_BROKERS"), ",")
	if len(brokers) == 0 {
		brokers = []string{"localhost:9092"}
	}

	workers, err := strconv.Atoi(os.Getenv("VIDEO_POSTPROCESS_WORKERS"))
	if err != nil || workers <= 0 {
		workers = 5
	}

	return Config{
		DebugMode:      strings.ToLower(os.Getenv("DEBUG_MODE")) == "true",
		Bucket:         os.Getenv("S3_BUCKET"),
		Region:         os.Getenv("S3_REGION"),
		Endpoint:       os.Getenv("MINIO_SERVER_URL"),
		AccessKey:      os.Getenv("MINIO_ROOT_USER"),
		SecretKey:      os.Getenv("MINIO_ROOT_PASSWORD"),
		ConsumeWorkers: workers,
		RabbitmqUser:   os.Getenv("RABBITMQ_DEFAULT_USER"),
		RabbitmqPass:   os.Getenv("RABBITMQ_DEFAULT_PASS"),
	}
}
