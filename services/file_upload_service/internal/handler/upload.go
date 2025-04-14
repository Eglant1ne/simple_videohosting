package handler

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"

	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/service"
	"github.com/minio/minio-go/v7"
)

const MinChunkSize = 5 * 1024 * 1024

type CustomMultipartFile struct {
	*bytes.Reader
}

func (f *CustomMultipartFile) ReadAt(p []byte, off int64) (n int, err error) {
	return f.Reader.ReadAt(p, off)
}

func (f *CustomMultipartFile) Close() error {
	return nil
}

func UploadHandler(minioSvc *service.MinIOService, cfg *config.Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		file, header, err := r.FormFile("file")
		if err != nil {
			http.Error(w, fmt.Sprintf("failed to read file: %v", err), http.StatusBadRequest)
			return
		}
		defer file.Close()

		buf, err := io.ReadAll(file)
		if err != nil {
			http.Error(w, "cannot read uploaded file", http.StatusInternalServerError)
			return
		}
		size := int64(len(buf))

		customFile := &CustomMultipartFile{Reader: bytes.NewReader(buf)}

		err = uploadMultipartFile(minioSvc, header.Filename, customFile, size)
		if err != nil {
			http.Error(w, fmt.Sprintf("upload error: %v", err), http.StatusInternalServerError)
			return
		}

		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("Upload successful"))
	}
}

func uploadMultipartFile(minioSvc *service.MinIOService, fileName string, file multipart.File, fileSize int64) error {
	chunkCount := int(fileSize / MinChunkSize)
	if fileSize%MinChunkSize != 0 {
		chunkCount++
	}

	uploadID, err := minioSvc.StartMultipartUpload(context.Background(), fileName)
	if err != nil {
		return err
	}

	var parts []minio.CompletePart
	for i := 0; i < chunkCount; i++ {
		start := int64(i) * MinChunkSize
		end := start + MinChunkSize
		if end > fileSize {
			end = fileSize
		}

		chunk := make([]byte, end-start)
		_, err := file.ReadAt(chunk, start)
		if err != nil && err != io.EOF {
			return fmt.Errorf("error reading chunk: %v", err)
		}

		part, err := minioSvc.UploadPart(context.Background(), fileName, uploadID, i+1, chunk)
		if err != nil {
			return fmt.Errorf("error uploading chunk %d: %v", i+1, err)
		}

		parts = append(parts, minio.CompletePart{
			PartNumber: i + 1,
			ETag:       part.ETag,
		})
	}

	return minioSvc.CompleteMultipartUpload(context.Background(), fileName, uploadID, parts)
}
