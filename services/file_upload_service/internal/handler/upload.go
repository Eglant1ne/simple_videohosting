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
	response "github.com/Eglant1ne/simple_videohosting/services/file_upload_service/pkg/http"
	filewrapper "github.com/Eglant1ne/simple_videohosting/services/file_upload_service/pkg/io"
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

		buf, err := io.ReadAll(file)
		if err != nil {
			response.JSONResponse(w, http.StatusInternalServerError, fmt.Sprintf("Невозможно прочитать загруженные файлы: %v", err))
			return
		}
		size := int64(len(buf))

		customFile := &filewrapper.FileWrapper{Reader: bytes.NewReader(buf)}

		err = uploadMultipartFile(minioSvc, header.Filename, customFile, size)
		if err != nil {
			response.JSONResponse(w, http.StatusInternalServerError, fmt.Sprintf("Ошибка загрузки: %v", err))
			return
		}

		response.JSONResponse(w, http.StatusOK, fmt.Sprintf("Файл успешно загружен: %v", err))
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
	for i := range chunkCount {
		start := int64(i) * MinChunkSize
		end := min(start+MinChunkSize, fileSize)

		chunk := make([]byte, end-start)
		_, err := file.ReadAt(chunk, start)
		if err != nil && err != io.EOF {
			return fmt.Errorf("ошибка чтения чанка: %v", err)
		}

		part, err := minioSvc.UploadPart(context.Background(), fileName, uploadID, i+1, chunk)
		if err != nil {
			return fmt.Errorf("ошибка загрузки чанка %d: %v", i+1, err)
		}

		parts = append(parts, minio.CompletePart{
			PartNumber: i + 1,
			ETag:       part.ETag,
		})
	}

	return minioSvc.CompleteMultipartUpload(context.Background(), fileName, uploadID, parts)
}
