package service

import (
	"bytes"
	"context"
	"log"
	"time"

	appcfg "github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
)

type MinIOService struct {
	Client *minio.Client
	Config appcfg.Config
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

	return &MinIOService{
		Client: client,
		Config: cfg,
	}
}

func (svc *MinIOService) StartMultipartUpload(ctx context.Context, objectName string) (string, error) {
	client := minio.Core{Client: svc.Client}
	uploadInfo, err := client.NewMultipartUpload(ctx, svc.Config.Bucket, objectName, minio.PutObjectOptions{})
	if err != nil {
		return "", err
	}
	return uploadInfo, nil
}

func (svc *MinIOService) UploadPart(ctx context.Context, objectName, uploadID string, partNumber int, data []byte) (minio.ObjectPart, error) {
	reader := bytes.NewReader(data)
	client := minio.Core{Client: svc.Client}
	return client.PutObjectPart(ctx, svc.Config.Bucket, objectName, uploadID, partNumber, reader, int64(len(data)), minio.PutObjectPartOptions{})
}

func (svc *MinIOService) CompleteMultipartUpload(ctx context.Context, objectName, uploadID string, parts []minio.CompletePart) error {
	client := minio.Core{Client: svc.Client}
	_, err := client.CompleteMultipartUpload(ctx, svc.Config.Bucket, objectName, uploadID, parts, minio.PutObjectOptions{})
	return err
}

func (svc *MinIOService) AbortMultipartUpload(ctx context.Context, objectName, uploadID string) error {
	client := minio.Core{Client: svc.Client}
	return client.AbortMultipartUpload(ctx, svc.Config.Bucket, objectName, uploadID)
}
