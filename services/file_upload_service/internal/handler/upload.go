package handler

import (
	"fmt"
	"io"
	"net/http"
	"path/filepath"
	"strings"

	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/service"
)

func FileUploadHandler(minioSvc *service.MinIOService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var maxFileSize int64 = 8 << 30
		err := r.ParseMultipartForm(maxFileSize)
		if err != nil {
			http.Error(w, "file too large or invalid form", http.StatusBadRequest)
			return
		}

		file, handler, err := r.FormFile("file")

		if handler.Size > maxFileSize {
			http.Error(w, "file too large (max 8GB)", http.StatusBadRequest)
			return
		}

		if err != nil {
			http.Error(w, "invalid file", http.StatusBadRequest)
			return
		}
		defer file.Close()

		allowedExtensions := map[string]bool{
			".mp4":  true,
			".mov":  true,
			".avi":  true,
			".mkv":  true,
			".webm": true,
			".wmv":  true,
			".flv":  true,
		}

		ext := strings.ToLower(filepath.Ext(handler.Filename))
		if !allowedExtensions[ext] {
			http.Error(w, "invalid file type: only video files are allowed", http.StatusBadRequest)
			return
		}

		buffer := make([]byte, 512)
		_, err = file.Read(buffer)
		if err != nil {
			http.Error(w, "failed to read file", http.StatusInternalServerError)
			return
		}

		_, err = file.Seek(0, 0)
		if err != nil {
			http.Error(w, "failed to reset file pointer", http.StatusInternalServerError)
			return
		}

		mimeType := http.DetectContentType(buffer)
		allowedMimeTypes := map[string]bool{
			"video/mp4":                true,
			"video/quicktime":          true,
			"video/x-msvideo":          true,
			"video/x-matroska":         true,
			"video/webm":               true,
			"video/x-ms-wmv":           true,
			"video/x-flv":              true,
			"application/octet-stream": true,
		}

		if !allowedMimeTypes[mimeType] {
			http.Error(w, fmt.Sprintf("invalid file content type: %s - only video files are allowed", mimeType), http.StatusBadRequest)
			return
		}

		fileSize := handler.Size
		key := handler.Filename

		if err := minioSvc.UploadStream(r.Context(), key, file, fileSize); err != nil {
			http.Error(w, fmt.Sprintf("upload error: %v", err), http.StatusInternalServerError)
			return
		}

	}
}

func UploadFileInChunks(minioSvc *service.MinIOService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
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
