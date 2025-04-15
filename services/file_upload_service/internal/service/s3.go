package service

import (
	"context"
	"log"
	"time"

	appcfg "github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
)

type MinIOService struct {
	Client                  *minio.Client
	Config                  appcfg.Config
	UnprocessedVideosFolder string
}

func NewMinIOService(cfg appcfg.Config) *MinIOService {
	client, err := minio.New(cfg.Endpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(cfg.AccessKey, cfg.SecretKey, ""),
		Secure: false,
		Region: cfg.Region,
	})
	if err != nil {
		log.Fatalf("%v", cfg.Endpoint)
		log.Fatalf("failed to initialize MinIO client: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	exists, err := client.BucketExists(ctx, cfg.Bucket)
	if err != nil {
		log.Fatalf("failed to check bucket existence: %v", err)
	}

	if !exists {
		err = client.MakeBucket(ctx, cfg.Bucket, minio.MakeBucketOptions{})
		if err != nil {
			log.Fatalf("failed to create bucket: %v", err)
		}
	}

	folderName := "unprocessed_videos"
	folderPath := folderName + "/"

	client.PutObject(ctx, cfg.Bucket, folderPath, nil, 0,
		minio.PutObjectOptions{ContentType: "application/x-directory"})

	log.Printf("Folder %s created in bucket %s\n", folderName, cfg.Bucket)

	return &MinIOService{
		Client:                  client,
		Config:                  cfg,
		UnprocessedVideosFolder: folderName,
	}
}
