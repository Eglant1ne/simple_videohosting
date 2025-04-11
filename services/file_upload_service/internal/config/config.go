package config

import (
	"os"
)

type Config struct {
	Bucket       string
	Region       string
	Endpoint     string
	AccessKey    string
	SecretKey    string
	UsePathStyle bool
}

func Load() Config {
	return Config{
		Bucket:       getEnv("S3_BUCKET", "uploads"),
		Region:       getEnv("S3_REGION", "us-east-1"),
		Endpoint:     getEnv("S3_ENDPOINT", "http://localhost:9000"),
		AccessKey:    getEnv("S3_ACCESS_KEY", "minioadmin"),
		SecretKey:    getEnv("S3_SECRET_KEY", "minioadmin"),
		UsePathStyle: true,
	}
}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}
