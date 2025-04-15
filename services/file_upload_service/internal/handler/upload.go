package handler

import (
	"context"
	"fmt"
	"io"
	"net/http"

	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/service"
	response "github.com/Eglant1ne/simple_videohosting/services/file_upload_service/pkg/http"
	"github.com/minio/minio-go/v7"
)

const defaultPartSize = 32 << 20

func UploadHandler(minioSvc *service.MinIOService, cfg *config.Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		r.Body = http.MaxBytesReader(w, r.Body, 10<<30)
		reader, err := r.MultipartReader()
		if err != nil {
			response.JSONResponse(w, http.StatusBadRequest, fmt.Sprintf("Ошибка чтения файла: %v", err))
			return
		}

		part, err := reader.NextPart()
		if err != nil {
			response.JSONResponse(w, http.StatusBadRequest, fmt.Sprintf("Ошибка чтения части: %v", err))
		}
		for {
			if err == io.EOF {
				response.JSONResponse(w, http.StatusBadRequest, "Нет файла")
				return
			}
			if err != nil {
				response.JSONResponse(w, http.StatusBadRequest, fmt.Sprintf("Ошибка чтения части: %v", err))
				return
			}

			if part.FormName() == "file" {
				defer part.Close()
				break
			}
			part, err = reader.NextPart()
		}

		ctx := context.Background()

		minioSvc.Client.PutObject(ctx, cfg.Bucket, part.FileName(), part, -1, minio.PutObjectOptions{PartSize: defaultPartSize})
		response.JSONResponse(w, http.StatusOK, "Файл успешно загружен")

	}

}
