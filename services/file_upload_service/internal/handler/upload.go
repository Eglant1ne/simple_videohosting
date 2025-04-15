package handler

import (
	"context"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"strconv"

	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/service"
	response "github.com/Eglant1ne/simple_videohosting/services/file_upload_service/pkg/http"
	"github.com/minio/minio-go/v7"
)

const MinChunkSize = 5 * 1024 * 1024

func UploadHandler(minioSvc *service.MinIOService, cfg *config.Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		file, header, err := r.FormFile("file")
		if err != nil {
			response.JSONResponse(w, http.StatusBadRequest, fmt.Sprintf("Ошибка чтения файла: %v", err))
			return
		}
		defer file.Close()

		fileSizeStr := r.Header.Get("Content-Length")
		fileSize, _ := strconv.ParseInt(fileSizeStr, 10, 64)

		err = uploadMultipartFile(minioSvc, header.Filename, file, fileSize)
		if err != nil {
			response.JSONResponse(w, http.StatusInternalServerError, fmt.Sprintf("Ошибка загрузки: %v", err))
			return
		}

		response.JSONResponse(w, http.StatusOK, "Файл успешно загружен")
	}
}

func uploadMultipartFile(minioSvc *service.MinIOService, fileName string, file multipart.File, fileSize int64) error {
	ctx := context.Background()
	uploadID, err := minioSvc.StartMultipartUpload(ctx, fileName)
	if err != nil {
		return err
	}

	var (
		parts  []minio.CompletePart
		partNo = 1
		buf    = make([]byte, MinChunkSize)
	)

	for {
		n, err := io.ReadFull(file, buf)
		if err != nil {
			if err == io.EOF || err == io.ErrUnexpectedEOF {
				if n == 0 {
					break
				}
			} else {
				return fmt.Errorf("ошибка чтения файла: %v", err)
			}
		}

		chunk := buf[:n]

		part, err := minioSvc.UploadPart(ctx, fileName, uploadID, partNo, chunk)
		if err != nil {
			return fmt.Errorf("ошибка загрузки чанка %d: %v", partNo, err)
		}

		parts = append(parts, minio.CompletePart{
			PartNumber: partNo,
			ETag:       part.ETag,
		})

		partNo++
	}

	return minioSvc.CompleteMultipartUpload(ctx, fileName, uploadID, parts)
}
