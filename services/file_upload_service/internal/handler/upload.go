package handler

import (
	"context"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"path/filepath"

	api "github.com/Eglant1ne/simple_videohosting/services/file_upload_service/api"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/service"
	"github.com/google/uuid"
	"github.com/minio/minio-go/v7"
)

const defaultPartSize = 32 << 20

func UploadHandler(minioSvc *service.MinIOService, cfg *config.Config, producer *service.KafkaProducer, kafkaTopic string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		access_token, err := getCookieHandler(w, r)
		if err != nil {
			api.JSONResponse(w, http.StatusUnauthorized, "Не авторизованный пользователь!")
			return
		}
		authResp, statusCode := api.IsAuthenticated(access_token)
		if statusCode != http.StatusOK {
			api.JSONResponse(w, statusCode, authResp.Error)
			return
		}

		r.Body = http.MaxBytesReader(w, r.Body, 20<<30)
		reader, err := r.MultipartReader()
		if err != nil {
			api.JSONResponse(w, http.StatusBadRequest, fmt.Sprintf("Ошибка чтения файла: %v", err))
			return
		}

		part, err := reader.NextPart()
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
		videoID, err := uuid.NewRandom()
		if err != nil {
			api.JSONResponse(w, http.StatusBadGateway, (fmt.Sprintf("ошибка генерации uuid %v", err)))
			return
		}
		ext := filepath.Ext(part.FileName())
		fileName := hex.EncodeToString(videoID[:]) + ext

		fullPath := minioSvc.UnprocessedVideosFolder + "/" + fileName

		minioSvc.Client.PutObject(ctx, cfg.Bucket, fullPath, part, -1, minio.PutObjectOptions{PartSize: defaultPartSize})
		msg := map[string]interface{}{
			"user_id":    authResp.User.ID,
			"video_path": fullPath,
		}

		msgBytes, err := json.Marshal(msg)
		if err != nil {
			api.JSONResponse(w, http.StatusInternalServerError, fmt.Sprintf("Ошибка формирования сообщения: %v", err))
			return
		}

		if err := producer.SendMessage(kafkaTopic, videoID.String(), msgBytes); err != nil {
			api.JSONResponse(w, http.StatusInternalServerError, fmt.Sprintf("Ошибка отправки сообщения: %v", err))
			return
		}

		log.Printf("Отправлено сообщение в Kafka: topic=%s key=%s value=%s\n", kafkaTopic, videoID.String(), string(msgBytes))
		api.JSONResponse(w, http.StatusOK, "Файл успешно создан")

	}

}
