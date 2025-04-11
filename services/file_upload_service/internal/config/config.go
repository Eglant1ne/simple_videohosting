package config

import (
	"os"
	"strings"
)

type Config struct {
    DebugMode bool
	Bucket    string
	Region    string
	Endpoint  string
	AccessKey string
	SecretKey string
}

func Load() Config {
	return Config{
	    DebugMode: strings.ToLower(os.Getenv("DEBUG_MODE")) == "true",
		Bucket:    os.Getenv("S3_BUCKET"),
		Region:    os.Getenv("S3_REGION"),
		Endpoint:  os.Getenv("MINIO_SERVER_URL"),
		AccessKey: os.Getenv("MINIO_ROOT_USER"),
		SecretKey: os.Getenv("MINIO_ROOT_PASSWORD"),
	}
}
