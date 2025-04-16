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
	KafkaBrokers   []string
	KafkaTopic     string
	KafkaGroupID   string
}

func Load() Config {
	brokers := strings.Split(os.Getenv("KAFKA_BROKERS"), ",")
	if len(brokers) == 0 {
		brokers = []string{"localhost:9092"}
	}

	workers, err := strconv.Atoi(os.Getenv("CONSUME_WORKERS"))
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
		KafkaBrokers:   brokers,
		KafkaTopic:     os.Getenv("KAFKA_TOPIC"),
		KafkaGroupID:   os.Getenv("KAFKA_GROUP_ID"),
	}
}
