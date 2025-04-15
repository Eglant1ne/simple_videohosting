package handler

import (
	"context"
	"encoding/hex"
	"fmt"
	"io"
	"net/http"

	api "github.com/Eglant1ne/simple_videohosting/services/file_upload_service/api"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/service"
	"github.com/google/uuid"
	"github.com/minio/minio-go/v7"
)

const defaultPartSize = 32 << 20

func UploadHandler(minioSvc *service.MinIOService, cfg *config.Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		access_token, err := getCookieHandler(w, r)
		if err != nil {
			api.JSONResponse(w, http.StatusUnauthorized, "Не авторизованный пользователь!")
			return
		}
		if api.IsAuthenticated(access_token) != 200 {
			return
		}

		r.Body = http.MaxBytesReader(w, r.Body, 20<<30)
		reader, err := r.MultipartReader()
		if err != nil {
			api.JSONResponse(w, http.StatusBadRequest, fmt.Sprintf("Ошибка чтения файла: %v", err))
			return
		}

		part, err := reader.NextPart()
		if err != nil {
			api.JSONResponse(w, http.StatusBadRequest, fmt.Sprintf("Ошибка чтения части: %v", err))
		}
		for {
			if err == io.EOF {
				api.JSONResponse(w, http.StatusBadRequest, "Нет файла")
				return
			}
			if err != nil {
				api.JSONResponse(w, http.StatusBadRequest, fmt.Sprintf("Ошибка чтения части: %v", err))
				return
			}

			if part.FormName() == "file" {
				defer part.Close()
				break
			}
			part, err = reader.NextPart()
		}

		ctx := context.Background()
		videoid, err := uuid.NewRandom()
		if err != nil {
			api.JSONResponse(w, http.StatusBadGateway, (fmt.Sprintf("ошибка генерации uuid %v", err)))
		}
		fileName := string(hex.EncodeToString(videoid[:])) + part.FileName()[len(part.FileName())-4:]

		minioSvc.Client.PutObject(ctx, cfg.Bucket, minioSvc.UnprocessedVideosFolder+"/"+fileName, part, -1, minio.PutObjectOptions{PartSize: defaultPartSize})
		api.JSONResponse(w, http.StatusOK, "Файл успешно создан")

	}

}
