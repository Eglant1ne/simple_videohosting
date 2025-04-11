package handler

import (
	"fmt"
	"io"
	"net/http"

	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/service"
)

func FileUploadHandler(minioSvc *service.MinIOService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		err := r.ParseMultipartForm(1000 << 20)
		if err != nil {
			http.Error(w, "file too large or invalid form", http.StatusBadRequest)
			return
		}

		file, handler, err := r.FormFile("file")
		if err != nil {
			http.Error(w, "invalid file", http.StatusBadRequest)
			return
		}
		defer file.Close()

		// Получаем информацию о размере файла
		fileSize := handler.Size
		key := handler.Filename

		// Загружаем файл
		if err := minioSvc.UploadStream(r.Context(), key, file, fileSize); err != nil {
			http.Error(w, fmt.Sprintf("upload error: %v", err), http.StatusInternalServerError)
			return
		}

		fmt.Fprintf(w, "successfully uploaded: %s (size: %d bytes)", key, fileSize)
	}
}

func UploadFileInChunks(minioSvc *service.MinIOService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Реализация chunked upload
		chunk, err := io.ReadAll(r.Body)
		if err != nil {
			http.Error(w, "failed to read chunk", http.StatusBadRequest)
			return
		}

		key := r.URL.Query().Get("filename")
		if key == "" {
			http.Error(w, "filename parameter required", http.StatusBadRequest)
			return
		}

		if err := minioSvc.UploadChunk(r.Context(), key, chunk); err != nil {
			http.Error(w, fmt.Sprintf("chunk upload failed: %v", err), http.StatusInternalServerError)
			return
		}

		fmt.Fprintf(w, "chunk uploaded for file: %s (size: %d bytes)", key, len(chunk))
	}
}
